"""题库灌库脚本（幂等，可重复执行）。

用法：
    cd backend
    ..\\.venv\\Scripts\\python.exe scripts\\seed_question_bank.py           # 增量灌库（推荐）
    ..\\.venv\\Scripts\\python.exe scripts\\seed_question_bank.py --rebuild  # 清空后重建

幂等策略：以题干 text 为唯一键，存在则更新元信息、不存在则插入；
默认不删除人工新增的题目，--rebuild 才会清空 SEED 来源的题目后重建。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.data.question_bank import QUESTION_BANK_SEED  # noqa: E402
from app.models.question import QuestionBank  # noqa: E402


def seed_question_bank(db, rebuild: bool = False) -> dict:
    """把题库种子数据写入 question_bank 表，返回 {inserted, updated, skipped}。"""
    if rebuild:
        deleted = db.query(QuestionBank).filter(QuestionBank.source == "SEED").delete(synchronize_session=False)
        db.commit()
        print(f"[rebuild] 已清空 SEED 来源题目 {deleted} 条")

    existing = {q.text: q for q in db.query(QuestionBank).all()}
    inserted = updated = skipped = 0

    for item in QUESTION_BANK_SEED:
        text = (item.get("text") or "").strip()
        if not text:
            skipped += 1
            continue

        payload = {
            "job_category": item.get("job_category") or "通用",
            "question_type": item.get("question_type") or "PROFESSIONAL",
            "skill_name": item.get("skill_name") or "综合素养",
            "stage": item.get("stage") or "专业基础",
            "difficulty": item.get("difficulty") or "MEDIUM",
            "reference_points_json": json.dumps(item.get("reference_points") or [], ensure_ascii=False),
            "hints": item.get("hints"),
            "time_limit_sec": int(item.get("time_limit_sec") or 180),
            "enabled": True,
        }

        q = existing.get(text)
        if q:
            for k, v in payload.items():
                setattr(q, k, v)
            updated += 1
        else:
            db.add(QuestionBank(text=text, source="SEED", **payload))
            inserted += 1

    db.commit()
    total = db.query(QuestionBank).count()
    return {"inserted": inserted, "updated": updated, "skipped": skipped, "total": total}


def main():
    parser = argparse.ArgumentParser(description="灌入结构化面试题库")
    parser.add_argument("--rebuild", action="store_true", help="先清空 SEED 来源题目再重建")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        stat = seed_question_bank(db, rebuild=args.rebuild)
        print(f"题库灌库完成：新增 {stat['inserted']}，更新 {stat['updated']}，"
              f"跳过 {stat['skipped']}，当前总量 {stat['total']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
