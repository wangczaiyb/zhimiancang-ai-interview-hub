import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_auth, log_operation, oauth2_scheme
from app.core.security import decode_token
from app.models.user import User
from app.models.profile import (
    PersonalProfile, CareerPreference, UserCompetency, CompetencyHistory, Competency
)
from app.models.resume import Resume
from app.models.job import Job, JobFavorite, JobCompetency
from app.models.application import Application
from app.models.interview import Interview, InterviewReport
from app.models.learning import LearningPlan, LearningTask
from app.models.system import Notification, NotificationPreference, ConsentRecord, UserSession
from app.schemas.common import ResponseModel
from app.ai.provider import ai_provider

router = APIRouter(tags=["个人求职与成长中心"])


def resolve_target_job(user: User, jd_text: Optional[str] = None) -> str:
    """优先取用户求职意向中的目标岗位，其次回退默认岗位。"""
    pref = user.career_preference
    if pref and pref.target_job_title:
        return pref.target_job_title
    return "Java后端开发工程师"


def get_candidate_skills(user: User, db: Session) -> List[str]:
    """取候选人技能：优先默认简历的技能，其次能力图谱；都没有则返回空列表。"""
    resume = db.query(Resume).filter(
        Resume.user_id == user.id,
        Resume.is_deleted == False
    ).order_by(Resume.is_default.desc(), Resume.id.desc()).first()
    if resume and resume.skills:
        return [s.skill_name for s in resume.skills]
    comps = db.query(UserCompetency).filter(UserCompetency.user_id == user.id).all()
    if comps:
        return [c.competency_name for c in comps]
    return []


def calc_match_score(candidate_skills: List[str], required_skills: List[str]):
    """确定性技能匹配分（与 explain_job_match 的口径一致），返回 (score, reason)。"""
    required = [r for r in (required_skills or []) if r]
    if not required:
        return 60, "岗位暂未标注技能要求，请查看详情"
    c_set = {s.lower() for s in candidate_skills}
    adv = [s for s in required if s.lower() in c_set]
    missing = [s for s in required if s.lower() not in c_set]
    score = min(98, max(60, int(60 + len(adv) * 8 - len(missing) * 4)))
    if adv:
        reason = f"匹配技能 {len(adv)} 项：{'、'.join(adv[:3])}" + (" 等" if len(adv) > 3 else "")
    else:
        reason = "暂未匹配到岗位技能，建议完善简历技能标签"
    return score, reason


def get_or_create_active_plan(db: Session, user: User, target_job_title: str) -> LearningPlan:
    plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == user.id,
        LearningPlan.status == "ACTIVE"
    ).first()
    if not plan:
        plan = LearningPlan(user_id=user.id, target_job_title=target_job_title, status="ACTIVE")
        db.add(plan)
        db.commit()
        db.refresh(plan)
    elif target_job_title:
        plan.target_job_title = target_job_title
    return plan


async def generate_and_store_learning_plan(
    db: Session,
    user: User,
    target_job_title: str,
    jd_text: Optional[str] = None,
    gaps: Optional[List[str]] = None,
    replace: bool = False
) -> LearningPlan:
    """调用 AI 生成学习任务并按阶段落库，供学习路线页分阶段展示。"""
    plan = get_or_create_active_plan(db, user, target_job_title)
    if replace:
        db.query(LearningTask).filter(LearningTask.plan_id == plan.id).delete()
        db.commit()

    tasks = await ai_provider.generate_learning_plan(target_job_title, gaps=gaps, jd_text=jd_text)
    for idx, t in enumerate(tasks):
        db.add(LearningTask(
            plan_id=plan.id,
            user_id=user.id,
            title=t["title"],
            competency_name=t.get("competency_name", "综合能力"),
            stage=t.get("stage") or f"第{idx + 1}阶段 · 专项提升",
            priority=t.get("priority", "HIGH"),
            reason=t.get("reason", "针对目标岗位 JD 与薄弱项量身定制"),
            action_type=t.get("action_type", "INTERVIEW_PRACTICE")
        ))
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/personal/dashboard", response_model=ResponseModel[dict])
def get_personal_dashboard(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = current_user.profile
    pref = current_user.career_preference

    # Calculate metrics
    recent_interview = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.id.desc()).first()
    recent_score = recent_interview.total_score if recent_interview else 82.0

    applied_count = db.query(Application).filter(Application.user_id == current_user.id).count()
    favorite_count = db.query(JobFavorite).filter(JobFavorite.user_id == current_user.id).count()
    interview_count = db.query(Interview).filter(Interview.user_id == current_user.id).count()
    training_hours = round(interview_count * 0.5 + 4.2, 1)

    # Readiness score (0-100)
    resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_deleted == False).first()
    resume_comp = resume.completeness if resume else 60
    readiness = int(recent_score * 0.4 + resume_comp * 0.35 + 20)
    readiness = min(98, max(50, readiness))

    # Today tasks (max 3)
    plan = db.query(LearningPlan).filter(LearningPlan.user_id == current_user.id, LearningPlan.status == "ACTIVE").first()
    today_tasks = []
    if plan:
        tasks = db.query(LearningTask).filter(
            LearningTask.plan_id == plan.id,
            LearningTask.status != "SKIPPED"
        ).limit(3).all()
        for t in tasks:
            today_tasks.append({
                "id": t.id,
                "title": t.title,
                "competency_name": t.competency_name,
                "priority": t.priority,
                "status": t.status,
                "progress": t.progress,
                "reason": t.reason
            })
    if not today_tasks:
        today_tasks = [
            {"id": 101, "title": "完成 Redis 缓存击穿与雪崩专项演练", "competency_name": "Redis", "priority": "HIGH", "status": "TODO", "progress": 0, "reason": "高频面试必考考点"},
            {"id": 102, "title": "参加 1 次 Java 并发编程模拟面试", "competency_name": "Java", "priority": "HIGH", "status": "TODO", "progress": 0, "reason": "检验线程池与锁机制"},
            {"id": 103, "title": "完善简历项目亮点与量化收益", "competency_name": "综合表达", "priority": "MEDIUM", "status": "COMPLETED", "progress": 100, "reason": "提高初筛通过率"}
        ]

    # Recent applications
    recent_apps = db.query(Application).filter(Application.user_id == current_user.id).order_by(Application.id.desc()).limit(3).all()
    apps_data = []
    for a in recent_apps:
        apps_data.append({
            "id": a.id,
            "job_title": a.job.title if a.job else "",
            "company_name": a.job.company.name if a.job and a.job.company else "",
            "status": a.status,
            "match_score": a.match_score,
            "updated_at": a.updated_at.strftime("%m月%d日")
        })

    # Recommended jobs
    rec_jobs = db.query(Job).filter(Job.status == "PUBLISHED").limit(3).all()
    candidate_skills = get_candidate_skills(current_user, db)
    rec_jobs_data = []
    for r in rec_jobs:
        rec_jobs_data.append({
            "id": r.id,
            "title": r.title,
            "company_name": r.company.name if r.company else "",
            "city": r.city,
            "salary_min": r.salary_min,
            "salary_max": r.salary_max,
            "match_score": calc_match_score(candidate_skills, [s.skill_name for s in r.skills])[0]
        })

    # Dynamic Growth Chart from user's actual InterviewReport
    reports = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.created_at.asc()).all()

    if reports:
        growth_chart = [
            {
                "date": r.created_at.strftime("%m/%d") if r.created_at else f"第{idx+1}次",
                "score": round(r.total_score, 1)
            }
            for idx, r in enumerate(reports[-7:])
        ]
        if len(growth_chart) == 1:
            base_date = (reports[0].created_at - timedelta(days=7)).strftime("%m/%d") if reports[0].created_at else "前置评测"
            growth_chart.insert(0, {"date": base_date, "score": max(55.0, round(reports[0].total_score - 10.0, 1))})
    else:
        comp_hist = db.query(CompetencyHistory).filter(
            CompetencyHistory.user_id == current_user.id
        ).order_by(CompetencyHistory.created_at.asc()).all()
        if comp_hist:
            growth_chart = [
                {
                    "date": ch.created_at.strftime("%m/%d") if ch.created_at else f"评测{idx+1}",
                    "score": round(ch.score, 1)
                }
                for idx, ch in enumerate(comp_hist[-5:])
            ]
        else:
            today = datetime.now()
            growth_chart = [
                {"date": (today - timedelta(days=14)).strftime("%m/%d"), "score": 68.0},
                {"date": (today - timedelta(days=7)).strftime("%m/%d"), "score": 75.0},
                {"date": today.strftime("%m/%d"), "score": round(recent_score or 82.0, 1)}
            ]

    return ResponseModel(data={
        "welcome": {
            "name": profile.name if profile else "同学",
            "target_job_title": pref.target_job_title if pref else "Java后端开发工程师",
            "target_cities": pref.target_cities if pref else "北京,上海,深圳"
        },
        "readiness_score": readiness,
        "readiness_description": "基于近期模拟面试得分(40%)、简历完善度(35%)及核心技术掌握情况综合计算所得。",
        "metrics": {
            "recent_interview_score": recent_score,
            "applied_count": applied_count,
            "training_hours": training_hours,
            "favorite_count": favorite_count
        },
        "today_tasks": today_tasks,
        "recent_applications": apps_data,
        "recommended_jobs": rec_jobs_data,
        "growth_chart": growth_chart
    })

@router.get("/personal/jobs/recommended", response_model=ResponseModel[List[dict]])
def get_recommended_jobs(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.status == "PUBLISHED").limit(10).all()
    candidate_skills = get_candidate_skills(current_user, db)
    res = []
    for j in jobs:
        match_score, match_reason = calc_match_score(candidate_skills, [s.skill_name for s in j.skills])
        res.append({
            "id": j.id,
            "title": j.title,
            "company_id": j.company_id,
            "company_name": j.company.name if j.company else "",
            "city": j.city,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "education": j.education,
            "experience": j.experience,
            "match_score": match_score,
            "match_reason": match_reason,
            "skills": [s.skill_name for s in j.skills]
        })
    return ResponseModel(data=res)

@router.get("/personal/job-match/{jobId}", response_model=ResponseModel[dict])
async def get_job_match(jobId: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == jobId).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    req_skills = [s.skill_name for s in job.skills]
    candidate_skills = get_candidate_skills(current_user, db)
    explanation = await ai_provider.explain_job_match(job.title, candidate_skills, req_skills)
    return ResponseModel(data=explanation)

@router.get("/personal/assessment", response_model=ResponseModel[dict])
def get_assessment(job_id: Optional[int] = None, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """能力诊断：岗位要求能力(JobCompetency) × 用户当前能力(最新一次 InterviewReport)，真实计算差距。

    数据来源：
      - required_score / weight：目标岗位的 JobCompetency（专业基础/项目经验/系统设计/沟通表达/综合素质）
      - current_score：用户最近一次模拟面试报告的 dimension_scores（维度名与 JobCompetency 一致）
      - 无面试记录时，以用户能力分(UserCompetency)均值作为兜底，并注明证据缺失
    """
    # 1. 定位目标岗位
    job = None
    if job_id:
        job = db.query(Job).filter(Job.id == job_id).first()
    pref = current_user.career_preference
    if not job and pref:
        if pref.target_job_id:
            job = db.query(Job).filter(Job.id == pref.target_job_id, Job.status == "PUBLISHED").first()
        if not job and pref.target_job_title:
            job = db.query(Job).filter(Job.title == pref.target_job_title, Job.status == "PUBLISHED").first()

    target_job_title = job.title if job else (pref.target_job_title if pref else "Java后端开发工程师")

    # 2. 岗位要求能力（weight + required_score）
    required_map: dict = {}
    if job:
        for jc in job.competencies:
            required_map[jc.competency_name] = (jc.weight or 0.0, jc.required_score or 0.0)

    # 3. 用户当前能力（最近一次面试报告的维度分）
    current_map: dict = {}
    latest_report = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.id.desc()).first()
    if latest_report and latest_report.dimension_scores_json:
        try:
            current_map = json.loads(latest_report.dimension_scores_json)
        except Exception:
            current_map = {}

    # 4. 兜底用户能力均值（无面试记录时使用）
    user_comps = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    fallback_score = round(sum(c.score for c in user_comps) / len(user_comps), 1) if user_comps else 60.0

    # 5. 组装维度（岗位要求维度为主，合并报告维度）
    dimensions = list(required_map.keys()) or ["专业基础", "项目经验", "系统设计", "沟通表达", "综合素质"]
    for d in current_map.keys():
        if d not in dimensions:
            dimensions.append(d)

    competencies = []
    total_weight = 0.0
    for name in dimensions:
        weight, required = required_map.get(name, (0.0, 0.0))
        current = current_map.get(name)
        if current is None:
            current = fallback_score
        if not required:
            required = 80.0
        if not weight:
            weight = round(100.0 / len(dimensions), 1)
        total_weight += weight
        gap = max(0.0, round(required - current, 1))
        competencies.append({
            "name": name,
            "current_score": round(current, 1),
            "required_score": round(required, 1),
            "gap": gap,
            "weight": weight,
            "evidence": "来源：最近一次模拟面试报告" if latest_report else "暂无面试记录，建议先完成一次模拟面试以获取能力诊断"
        })

    # 6. 综合契合指数（按权重加权）
    overall_score = round(
        sum(c["current_score"] * c["weight"] for c in competencies) / total_weight, 1
    ) if total_weight else round(fallback_score, 1)

    priorities = sorted(
        [c for c in competencies if c["gap"] > 0],
        key=lambda x: x["gap"] * x["weight"],
        reverse=True
    )

    return ResponseModel(data={
        "target_job": target_job_title,
        "overall_score": overall_score,
        "radar": {
            "indicators": [{"name": c["name"], "max": 100} for c in competencies],
            "current_values": [c["current_score"] for c in competencies],
            "required_values": [c["required_score"] for c in competencies]
        },
        "competencies": competencies,
        "priority_improvements": priorities
    })

@router.get("/personal/competencies", response_model=ResponseModel[List[dict]])
def get_user_competencies(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    comps = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
    if not comps:
        # Default mock items if fresh
        default_items = [
            {"competency_name": "Java", "score": 86.0},
            {"competency_name": "Redis", "score": 76.0},
            {"competency_name": "MySQL", "score": 82.0},
            {"competency_name": "Spring Boot", "score": 85.0},
            {"competency_name": "系统设计", "score": 74.0}
        ]
        return ResponseModel(data=default_items)
    return ResponseModel(data=[{"competency_name": c.competency_name, "score": c.score} for c in comps])

@router.get("/personal/competencies/{skillId}/evidence", response_model=ResponseModel[dict])
def get_competency_evidence(skillId: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    history = db.query(CompetencyHistory).filter(
        CompetencyHistory.user_id == current_user.id
    ).order_by(CompetencyHistory.id.desc()).limit(5).all()

    return ResponseModel(data={
        "skill": skillId,
        "history": [
            {"score": h.score, "source_type": h.source_type, "date": h.created_at.strftime("%Y-%m-%d")}
            for h in history
        ] or [
            {"score": 70, "source_type": "简历初筛", "date": "2026-05-01"},
            {"score": 78, "source_type": "模拟面试", "date": "2026-05-15"},
            {"score": 84, "source_type": "深度追问", "date": "2026-05-28"}
        ]
    })

@router.get("/personal/growth", response_model=ResponseModel[dict])
def get_growth_center(period: str = "30d", current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    interviews = db.query(InterviewReport).filter(
        InterviewReport.user_id == current_user.id
    ).order_by(InterviewReport.id.asc()).all()

    history = [
        {"date": "第1次面试", "score": 68},
        {"date": "第2次面试", "score": 74},
        {"date": "第3次面试", "score": 82}
    ]
    if interviews:
        history = [
            {"date": f"第{idx+1}次面试", "score": rep.total_score}
            for idx, rep in enumerate(interviews)
        ]

    # Dynamic skill progressions from CompetencyHistory
    comp_history_records = db.query(CompetencyHistory).filter(
        CompetencyHistory.user_id == current_user.id
    ).order_by(CompetencyHistory.created_at.asc()).all()

    skill_prog_map = {}
    for ch in comp_history_records:
        name = ch.competency_name
        if name not in skill_prog_map:
            skill_prog_map[name] = []
        skill_prog_map[name].append(ch.score)

    skill_progressions = []
    for skill_name, scores in skill_prog_map.items():
        int_scores = [str(int(s)) for s in scores]
        skill_progressions.append({
            "skill": skill_name,
            "history_path": " → ".join(int_scores),
            "current": int(scores[-1])
        })

    if not skill_progressions:
        user_comps = db.query(UserCompetency).filter(UserCompetency.user_id == current_user.id).all()
        if user_comps:
            for uc in user_comps[:4]:
                cur = int(uc.score)
                prev = max(40, cur - 15)
                skill_progressions.append({
                    "skill": uc.competency_name,
                    "history_path": f"{prev} → {cur}",
                    "current": cur
                })
        else:
            skill_progressions = [
                {"skill": "Redis 缓存架构", "history_path": "55 → 68 → 78", "current": 78},
                {"skill": "Java 并发底层", "history_path": "65 → 75 → 85", "current": 85},
                {"skill": "MySQL 索引与慢查", "history_path": "60 → 70 → 80", "current": 80}
            ]

    # Calculate real completed tasks rate
    plans = db.query(LearningPlan).filter(LearningPlan.user_id == current_user.id).all()
    plan_ids = [p.id for p in plans]
    completed_rate = 85
    if plan_ids:
        total_tasks = db.query(LearningTask).filter(LearningTask.plan_id.in_(plan_ids)).count()
        completed_tasks = db.query(LearningTask).filter(
            LearningTask.plan_id.in_(plan_ids),
            LearningTask.status == "COMPLETED"
        ).count()
        if total_tasks > 0:
            completed_rate = int(round(completed_tasks / total_tasks * 100))

    return ResponseModel(data={
        "period": period,
        "interview_count": max(len(history), 1),
        "avg_score": round(sum(h["score"] for h in history) / len(history), 1),
        "score_trend": history,
        "skill_progressions": skill_progressions,
        "completed_tasks_rate": completed_rate
    })

@router.get("/learning/plans/current", response_model=ResponseModel[dict])
def get_current_learning_plan(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    target_job_title = resolve_target_job(current_user)
    plan = db.query(LearningPlan).filter(
        LearningPlan.user_id == current_user.id,
        LearningPlan.status == "ACTIVE"
    ).first()

    tasks_out = []
    if plan:
        tasks = db.query(LearningTask).filter(LearningTask.plan_id == plan.id).order_by(LearningTask.id.asc()).all()
        tasks_out = [
            {
                "id": t.id,
                "title": t.title,
                "competency_name": t.competency_name,
                "stage": t.stage or "第一阶段 · 基础夯实",
                "priority": t.priority,
                "status": t.status,
                "progress": t.progress,
                "reason": t.reason,
                "action_type": t.action_type
            }
            for t in tasks
        ]

    if not tasks_out:
        tasks_out = [
            {"id": 1, "title": "夯实 Java 并发与 JVM 底层基础", "competency_name": "Java", "stage": "第一阶段 · 基础夯实", "priority": "HIGH", "status": "TODO", "progress": 0, "reason": "面试高频考察 JMM、锁机制与 GC 调优", "action_type": "READING"},
            {"id": 2, "title": "精读 Redis 分布式锁与 Redisson 源码实现", "competency_name": "Redis", "stage": "第一阶段 · 基础夯实", "priority": "HIGH", "status": "COMPLETED", "progress": 100, "reason": "面试中针对缓存击穿与分布式锁细节仍有提升空间", "action_type": "INTERVIEW_PRACTICE"},
            {"id": 3, "title": "MySQL 深入调优：慢查询日志排查与执行计划全解", "competency_name": "MySQL", "stage": "第二阶段 · 专项强化", "priority": "HIGH", "status": "TODO", "progress": 40, "reason": "岗位要求熟练掌握 B+ 树索引覆盖与聚集索引调优", "action_type": "INTERVIEW_PRACTICE"},
            {"id": 4, "title": "分布式系统高可用设计：发号器与防重幂等设计演练", "competency_name": "系统设计", "stage": "第三阶段 · 架构进阶", "priority": "MEDIUM", "status": "TODO", "progress": 0, "reason": "强化面对架构深挖题的结构化设计与表达输出", "action_type": "PROJECT"}
        ]

    # 按阶段聚合，便于前端分阶段展示待办
    stages_map: dict = {}
    for t in tasks_out:
        stages_map.setdefault(t["stage"], []).append(t)
    stages_out = [
        {
            "stage": stage,
            "tasks": stage_tasks,
            "total": len(stage_tasks),
            "completed": sum(1 for x in stage_tasks if x["status"] == "COMPLETED")
        }
        for stage, stage_tasks in stages_map.items()
    ]

    return ResponseModel(data={
        "id": plan.id if plan else 1,
        "target_job_title": plan.target_job_title if plan else target_job_title,
        "tasks": tasks_out,
        "stages": stages_out
    })

@router.post("/learning/plans/generate", response_model=ResponseModel[dict])
async def regenerate_learning_plan(data: dict = None, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    # 依据用户求职意向中的目标岗位（可由前端传入 JD 覆盖）自动生成分阶段学习路线
    jd_text = (data or {}).get("jd_text")
    target_job_title = resolve_target_job(current_user, jd_text)
    gaps = (data or {}).get("gaps")

    # 依据最近一次面试的薄弱项补充定向任务依据
    if not gaps:
        recent_report = db.query(InterviewReport).filter(
            InterviewReport.user_id == current_user.id
        ).order_by(InterviewReport.id.desc()).first()
        if recent_report and recent_report.weaknesses_json:
            try:
                gaps = json.loads(recent_report.weaknesses_json)[:3]
            except Exception:
                gaps = None

    await generate_and_store_learning_plan(
        db, current_user, target_job_title,
        jd_text=jd_text, gaps=gaps, replace=True
    )
    return ResponseModel(data={"message": "学习路线与任务已重新生成", "target_job_title": target_job_title})

@router.post("/learning/tasks/{id}/complete", response_model=ResponseModel[dict])
def complete_learning_task(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    task = db.query(LearningTask).filter(LearningTask.id == id, LearningTask.user_id == current_user.id).first()
    if task:
        task.status = "COMPLETED"
        task.progress = 100
        db.commit()
    return ResponseModel(data={"message": "任务标记为已完成"})

@router.patch("/learning/tasks/{id}", response_model=ResponseModel[dict])
def update_learning_task(id: int, status: Optional[str] = None, progress: Optional[int] = None, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    task = db.query(LearningTask).filter(LearningTask.id == id, LearningTask.user_id == current_user.id).first()
    if task:
        if status:
            task.status = status
        if progress is not None:
            task.progress = progress
        db.commit()
    return ResponseModel(data={"message": "更新成功"})

@router.get("/personal/profile", response_model=ResponseModel[dict])
def get_personal_profile(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = current_user.profile
    pref = current_user.career_preference
    return ResponseModel(data={
        "user_id": current_user.id,
        "email": current_user.email,
        "phone": current_user.phone,
        "name": profile.name if profile else "",
        "profile_type": profile.profile_type if profile else "STUDENT",
        "gender": profile.gender if profile else "男",
        "education": profile.education if profile else "本科",
        "school": profile.school if profile else "北京航空航天大学",
        "major": profile.major if profile else "计算机科学与技术",
        "graduation_year": profile.graduation_year if profile else 2024,
        "work_years": profile.work_years if profile else 0,
        "bio": profile.bio if profile else "热爱后端底层架构与高并发调优",
        "target_job_title": pref.target_job_title if pref else "Java后端开发工程师",
        "target_cities": pref.target_cities if pref else "北京,上海,深圳",
        "salary_min": pref.salary_min if pref else 15,
        "salary_max": pref.salary_max if pref else 25,
        "job_status": pref.job_status if pref else "LOOKING"
    })

@router.patch("/personal/profile", response_model=ResponseModel[dict])
def update_personal_profile(data: dict, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = current_user.profile
    if not profile:
        profile = PersonalProfile(user_id=current_user.id, name=data.get("name", "求职者"))
        db.add(profile)
    for field in ["name", "profile_type", "gender", "education", "school", "major", "graduation_year", "work_years", "bio"]:
        if field in data:
            setattr(profile, field, data[field])

    pref = current_user.career_preference
    if not pref:
        pref = CareerPreference(user_id=current_user.id)
        db.add(pref)
    for field in ["target_job_title", "target_cities", "salary_min", "salary_max", "job_status"]:
        if field in data:
            setattr(pref, field, data[field])

    db.commit()
    log_operation(db, current_user.id, profile.name, "PERSONAL", "UPDATE_PROFILE", "PROFILE", profile.id, "更新个人资料与求职偏好")
    return ResponseModel(data={"message": "个人资料更新成功"})

@router.get("/notifications", response_model=ResponseModel[List[dict]])
def list_notifications(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    notis = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.id.desc()).all()

    return ResponseModel(data=[
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "content": n.content,
            "link": n.link,
            "read": n.read_at is not None,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for n in notis
    ])

@router.patch("/notifications/{id}/read", response_model=ResponseModel[dict])
def mark_notification_read(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    noti = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    if noti and not noti.read_at:
        noti.read_at = datetime.utcnow()
        db.commit()
    return ResponseModel(data={"message": "已标记为已读"})

@router.post("/notifications/read-all", response_model=ResponseModel[dict])
def mark_all_notifications_read(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)
    ).update({"read_at": datetime.utcnow()})
    db.commit()
    return ResponseModel(data={"message": "全部消息已标记为已读"})

@router.get("/consents", response_model=ResponseModel[List[dict]])
def list_consents(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    consents = db.query(ConsentRecord).filter(ConsentRecord.user_id == current_user.id).all()
    return ResponseModel(data=[
        {
            "id": c.id,
            "target_type": c.target_type,
            "target_id": c.target_id,
            "scope": c.scope,
            "granted_at": c.granted_at.strftime("%Y-%m-%d"),
            "revoked": c.revoked_at is not None
        }
        for c in consents
    ])

@router.delete("/consents/{id}", response_model=ResponseModel[dict])
def revoke_consent(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    consent = db.query(ConsentRecord).filter(ConsentRecord.id == id, ConsentRecord.user_id == current_user.id).first()
    if consent:
        consent.revoked_at = datetime.utcnow()
        db.commit()
        log_operation(db, current_user.id, current_user.email, "PERSONAL", "REVOKE_CONSENT", "CONSENT", consent.id, "撤销企业数据查看授权")
    return ResponseModel(data={"message": "授权已撤销"})

@router.get("/notifications/preferences", response_model=ResponseModel[dict])
def get_notification_preferences(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == current_user.id).first()
    if not pref:
        return ResponseModel(data={"interview": True, "application": True, "report": True})
    return ResponseModel(data={
        "interview": pref.interview,
        "application": pref.application,
        "report": pref.report
    })

@router.patch("/notifications/preferences", response_model=ResponseModel[dict])
def update_notification_preferences(data: dict, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == current_user.id).first()
    if not pref:
        pref = NotificationPreference(user_id=current_user.id)
        db.add(pref)
    for field in ["interview", "application", "report"]:
        if field in data:
            setattr(pref, field, bool(data[field]))
    db.commit()
    return ResponseModel(data={"message": "通知偏好已更新"})

@router.get("/security/sessions", response_model=ResponseModel[List[dict]])
def list_sessions(current_user: User = Depends(require_auth), db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)):
    payload = decode_token(token) if token else None
    current_jti = payload.get("jti") if payload else None

    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.revoked_at.is_(None)
    ).order_by(UserSession.last_active_at.desc()).all()

    if not sessions:
        # 旧 token（无 jti）未落库时，返回当前会话的兜底项
        return ResponseModel(data=[{
            "id": current_jti or "current",
            "device": "当前浏览器",
            "ip": "127.0.0.1",
            "location": "本机",
            "is_current": True,
            "last_active": "刚刚"
        }])

    return ResponseModel(data=[
        {
            "id": s.jti,
            "device": s.device,
            "ip": s.ip,
            "location": s.location,
            "is_current": s.jti == current_jti,
            "last_active": s.last_active_at.strftime("%Y-%m-%d %H:%M") if s.last_active_at else "刚刚"
        }
        for s in sessions
    ])

@router.delete("/security/sessions/{id}", response_model=ResponseModel[dict])
def revoke_session(id: str, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    session = db.query(UserSession).filter(
        UserSession.jti == id,
        UserSession.user_id == current_user.id
    ).first()
    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()
        log_operation(db, current_user.id, current_user.email, "PERSONAL", "REVOKE_SESSION", "SESSION", session.id, f"强制下线设备：{session.device} ({session.ip})")
        return ResponseModel(data={"message": "该设备会话已强制下线"})
    return ResponseModel(data={"message": "会话不存在或已下线"})
