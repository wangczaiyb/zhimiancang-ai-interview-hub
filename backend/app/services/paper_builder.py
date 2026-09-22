"""组卷引擎：从结构化题库按「题型配比 + 岗位技能匹配 + 难度就近」抽题。

设计要点（对齐 docs/report.html 中 v1.0 的可复现组卷思路，并适配本项目的多岗位模型）：
1. 题型配比：专业题 : 通用题 : 压力题，按面试 mode 选择配比，默认 5:3:2。
2. 岗位匹配：优先命中 Job.skills_required / JobSkill 的技能与 Job.category 的岗位大类，
   其次回退到"通用"大类，保证任何岗位都能组出卷。
3. 难度就近：以 Interview.difficulty 为基准，按难度距离排序，同距离优先未用过的题。
4. 去重与补足：同一卷内题干去重；题库某类不足时按「同类放宽岗位 → 跨类借用」顺序补足，
   仍不足则由调用方用 AI 动态生成兜底（并在卷面快照中记录缺口）。
5. 卷面快照：抽题结果写入 InterviewPlan.paper_json，题库后续变更不影响历史面试。
"""

import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.question import QuestionBank

# 题型常量
PROFESSIONAL = "PROFESSIONAL"
GENERAL = "GENERAL"
STRESS = "STRESS"

# 面试模式 → 题型配比（专业:通用:压力）。未列出的模式回退 COMPREHENSIVE。
MODE_RATIOS: Dict[str, Tuple[int, int, int]] = {
    "COMPREHENSIVE": (5, 3, 2),
    "TECHNICAL": (7, 2, 1),
    "PROJECT_DEEP_DIVE": (5, 4, 1),
    "BEHAVIORAL": (2, 7, 1),
    "STRESS": (4, 2, 4),
}
DEFAULT_RATIO = MODE_RATIOS["COMPREHENSIVE"]

DIFF_ORDER = {"EASY": 0, "MEDIUM": 1, "HARD": 2}

# 压力题固定为"通用"大类，这里允许按岗位大类精确匹配的专业题类别
GENERIC_CATEGORY = "通用"


@dataclass
class PaperSlot:
    """一道组卷槽位的抽题结果。"""

    seq: int
    question_type: str
    bank_id: Optional[int]
    skill_name: str
    stage: str
    text: str
    difficulty: str
    reference_points: List[str] = field(default_factory=list)
    hints: Optional[str] = None
    time_limit_sec: int = 180
    source: str = "QUESTION_BANK"

    def to_interview_question_kwargs(self) -> Dict[str, Any]:
        return {
            "bank_id": self.bank_id,
            "seq": self.seq,
            "stage": self.stage,
            "question_type": self.question_type,
            "skill_name": self.skill_name,
            "text": self.text,
            "difficulty": self.difficulty,
            "reference_points_json": json.dumps(self.reference_points, ensure_ascii=False),
            "hints": self.hints,
            "time_limit_sec": self.time_limit_sec,
            "source": self.source,
        }


@dataclass
class Paper:
    """组卷结果：已抽到的题 + 未能满足的题型缺口（交由 AI 兜底）。"""

    slots: List[PaperSlot]
    missing: Dict[str, int]  # {"PROFESSIONAL": 1} 表示该题型仍缺 1 题
    plan: Dict[str, Any]     # 卷面快照（配比、题库统计、命中技能等）

    @property
    def snapshot_json(self) -> str:
        return json.dumps(self.plan, ensure_ascii=False)


def resolve_ratio(mode: str) -> Tuple[int, int, int]:
    return MODE_RATIOS.get((mode or "").upper(), DEFAULT_RATIO)


def allocate_counts(mode: str, total: int) -> Dict[str, int]:
    """按配比把总题量分配为各题型题数，余数按配比从大到小补齐。"""
    total = max(1, int(total or 1))
    pro, gen, str_ = resolve_ratio(mode)
    weight_sum = pro + gen + str_
    raw = {
        PROFESSIONAL: total * pro / weight_sum,
        GENERAL: total * gen / weight_sum,
        STRESS: total * str_ / weight_sum,
    }
    counts = {k: int(v) for k, v in raw.items()}
    remainder = total - sum(counts.values())
    # 余数优先给配比权重高的题型
    for key, _ in sorted(raw.items(), key=lambda kv: kv[1] - counts[kv[0]], reverse=True):
        if remainder <= 0:
            break
        counts[key] += 1
        remainder -= 1
    return counts


def collect_job_skills(job: Optional[Job]) -> List[str]:
    """岗位技能关键词：JobSkill 优先，回退 skills_required 逗号分隔。"""
    if not job:
        return []
    names = [s.skill_name.strip() for s in job.skills if s.skill_name and s.skill_name.strip()]
    if not names and job.skills_required:
        names = [x.strip() for x in job.skills_required.split(",") if x.strip()]
    return names


def _difficulty_distance(item_diff: str, target_diff: str) -> int:
    return abs(DIFF_ORDER.get(item_diff or "MEDIUM", 1) - DIFF_ORDER.get(target_diff or "MEDIUM", 1))


def _skill_hit_rank(skill_name: str, job_skills: List[str]) -> int:
    """0 = 命中岗位技能；1 = 通用类技能；2 = 未命中（同岗位大类但技能不同）。"""
    s = (skill_name or "").strip().lower()
    for js in job_skills:
        j = js.strip().lower()
        if not j:
            continue
        if j == s or j in s or s in j:
            return 0
    if s in {"综合素养", "抗压能力"}:
        return 1
    return 2


def _normalize(item: QuestionBank) -> Dict[str, Any]:
    try:
        points = json.loads(item.reference_points_json) if item.reference_points_json else []
    except Exception:
        points = []
    return {
        "id": item.id,
        "job_category": item.job_category or GENERIC_CATEGORY,
        "question_type": item.question_type,
        "skill_name": item.skill_name,
        "stage": item.stage,
        "text": item.text,
        "difficulty": item.difficulty,
        "reference_points": points if isinstance(points, list) else [],
        "hints": item.hints,
        "time_limit_sec": item.time_limit_sec or 180,
        "usage_count": item.usage_count or 0,
    }


def _rank(cand: Dict[str, Any], job_skills: List[str], target_diff: str) -> Tuple:
    """排序键：技能命中 → 难度就近 → 出题次数（均衡）→ 随机（避免固定顺序）。"""
    return (
        _skill_hit_rank(cand["skill_name"], job_skills),
        _difficulty_distance(cand["difficulty"], target_diff),
        cand["usage_count"],
        random.random(),
    )


def _pick(
    pool: List[Dict[str, Any]],
    question_type: str,
    job_skills: List[str],
    target_diff: str,
    used_ids: set,
    used_texts: set,
    categories: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """从候选池中选一道最合适的题；不满足去重/大类约束时返回 None。

    categories=None 表示不限大类（跨岗位兜底）。
    """
    candidates = [
        c for c in pool
        if c["question_type"] == question_type
        and c["id"] not in used_ids
        and c["text"] not in used_texts
        and (categories is None or c["job_category"] in categories)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda c: _rank(c, job_skills, target_diff))
    return candidates[0]


def build_paper(
    db: Session,
    job: Optional[Job],
    mode: str,
    difficulty: str,
    total_questions: int,
    count_usage: bool = True,
) -> Paper:
    """组卷主入口。

    抽题顺序：先按题型配比取题，取不到时依次放宽
      ① 放宽岗位大类（同题型、不限大类）→ ② 借用其他题型的剩余题目补足总题量。
    最终仍不足则记入 missing，由调用方用 AI 生成兜底。

    count_usage=False 用于"组卷预览"：只抽题不累计出题次数，避免预览挤占真实组卷的均衡性。
    """
    counts = allocate_counts(mode, total_questions)
    job_skills = collect_job_skills(job)
    category = (job.category if job else None) or GENERIC_CATEGORY

    # 一次性取出启用中的题库（数据量小，内存排序即可）
    rows = db.query(QuestionBank).filter(QuestionBank.enabled == True).all()  # noqa: E712
    all_items = [_normalize(r) for r in rows]

    # 抽题放宽层级：① 同岗位大类 + 通用大类 → ② 不限大类（跨岗位兜底）
    tiers: List[Optional[List[str]]] = [[category, GENERIC_CATEGORY], None]

    used_ids: set = set()
    used_texts: set = set()
    slots: List[PaperSlot] = []
    missing: Dict[str, int] = {}

    # 抽取顺序：专业 → 压力 → 通用，保证小卷也能覆盖到压力题
    draw_order = [PROFESSIONAL, STRESS, GENERAL]
    for qtype in draw_order:
        want = counts.get(qtype, 0)
        got = 0
        for _ in range(want):
            picked = None
            for cats in tiers:
                picked = _pick(all_items, qtype, job_skills, difficulty, used_ids, used_texts, cats)
                if picked:
                    break
            if picked is None:
                break
            got += 1
            used_ids.add(picked["id"])
            used_texts.add(picked["text"])
            slots.append(_to_slot(0, qtype, picked))
        if got < want:
            missing[qtype] = want - got

    # 跨题型借用补足：某类题目不足时，用其他题型的剩余题目填补，尽量保持总题量
    if missing:
        for qtype, need in list(missing.items()):
            filled = 0
            for _ in range(need):
                spare = [i for i in all_items if i["id"] not in used_ids and i["text"] not in used_texts]
                if not spare:
                    break
                spare.sort(key=lambda c: _rank(c, job_skills, difficulty))
                picked = spare[0]
                used_ids.add(picked["id"])
                used_texts.add(picked["text"])
                # 借用题保留原题型标签，避免报告统计口径错乱
                slots.append(_to_slot(0, picked["question_type"], picked))
                filled += 1
            left = need - filled
            if left > 0:
                missing[qtype] = left
            else:
                del missing[qtype]

    # 打乱后按 seq 重排：避免每次都是"专业题在前"的固定体感
    random.shuffle(slots)
    for idx, slot in enumerate(slots, start=1):
        slot.seq = idx

    # 回写题库使用次数（组卷计数，用于均衡出题）；预览模式不计次
    if count_usage and used_ids:
        db.query(QuestionBank).filter(QuestionBank.id.in_(list(used_ids))).update(
            {QuestionBank.usage_count: QuestionBank.usage_count + 1}, synchronize_session=False
        )

    plan = {
        "mode": (mode or "COMPREHENSIVE").upper(),
        "ratio": dict(zip(["PROFESSIONAL", "GENERAL", "STRESS"], resolve_ratio(mode))),
        "allocated": counts,
        "bank_total": len(all_items),
        "bank_by_type": _type_stat(all_items),
        "matched_category": category,
        "job_skills": job_skills,
        "from_bank": len(slots),
        "missing_for_ai": missing,
        # 抽中的题库 ID（按 seq 顺序），供"预览考卷 → 按此考卷开考"复用
        "bank_ids": [s.bank_id for s in slots],
    }
    return Paper(slots=slots, missing=missing, plan=plan)


def paper_from_bank_ids(
    db: Session, bank_ids: List[int], question_types: Optional[List[str]] = None
) -> List[PaperSlot]:
    """按给定的题库 ID 顺序还原卷面（用于用户已预览并确认的考卷）。

    仅返回题库中真实存在且启用的题目；缺失的 ID 由调用方按缺口用 AI 补足。
    """
    if not bank_ids:
        return []
    rows = db.query(QuestionBank).filter(
        QuestionBank.id.in_(list(bank_ids)),
        QuestionBank.enabled == True  # noqa: E712
    ).all()
    by_id = {r.id: _normalize(r) for r in rows}
    slots: List[PaperSlot] = []
    for idx, bid in enumerate(bank_ids):
        item = by_id.get(bid)
        if not item:
            continue
        qtype = item["question_type"]
        if question_types and idx < len(question_types) and question_types[idx]:
            qtype = question_types[idx]
        slots.append(_to_slot(len(slots) + 1, qtype, item))
    return slots


def _to_slot(seq: int, question_type: str, picked: Dict[str, Any]) -> PaperSlot:
    return PaperSlot(
        seq=seq,
        question_type=question_type,
        bank_id=picked["id"],
        skill_name=picked["skill_name"],
        stage=picked["stage"],
        text=picked["text"],
        difficulty=picked["difficulty"],
        reference_points=picked["reference_points"],
        hints=picked["hints"],
        time_limit_sec=picked["time_limit_sec"],
    )


def _type_stat(items: List[Dict[str, Any]]) -> Dict[str, int]:
    stat: Dict[str, int] = {}
    for i in items:
        stat[i["question_type"]] = stat.get(i["question_type"], 0) + 1
    return stat
