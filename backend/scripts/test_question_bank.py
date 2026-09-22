"""题库与组卷引擎端到端冒烟测试（临时 SQLite，不污染开发库）。"""
import os
import sys
import json
import tempfile

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

TMP_DB = os.path.join(tempfile.gettempdir(), "qb_smoke.db")
if os.path.exists(TMP_DB):
    os.remove(TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB}"
# 冒烟测试走 mock 评分通道：结果确定、不依赖外网与配额
os.environ["AI_MODE"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.question import QuestionBank  # noqa: E402
from app.models.interview import Interview, InterviewQuestion, InterviewPlan  # noqa: E402
from app.models.job import Job, JobSkill  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from scripts.seed_question_bank import seed_question_bank  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'PASS' if cond else 'FAIL'}: {name} {extra}")


db = SessionLocal()
stat = seed_question_bank(db)
db.commit()
check("题库灌库", stat["total"] >= 80, f"total={stat['total']}")

# 幂等性：重复执行不产生重复数据
stat2 = seed_question_bank(db)
db.commit()
check("灌库幂等（第二次不新增）", stat2["inserted"] == 0 and stat2["total"] == stat["total"],
      f"inserted={stat2['inserted']} total={stat2['total']}")

# 造一个岗位 + 用户
company = Company(name="测试科技", industry="互联网/软件", size="150-500人",
                  city="深圳", status="VERIFIED")
db.add(company); db.commit(); db.refresh(company)
job = Job(company_id=company.id, title="Java后端开发工程师", category="后端开发", city="深圳",
          description="d", duties="du", requirements="re", skills_required="Java,MySQL,Redis",
          status="PUBLISHED")
db.add(job); db.commit(); db.refresh(job)
for s in ["Java", "MySQL", "Redis"]:
    db.add(JobSkill(job_id=job.id, skill_name=s, level="熟练", required=True))

user = User(email="qb_test@example.com", phone="13900000099",
            password_hash=get_password_hash("123456"), account_type="PERSONAL", status="ACTIVE")
db.add(user); db.commit(); db.refresh(user)
db.add(UserRole(user_id=user.id, role_code="PERSONAL_USER"))
db.commit()

JOB_ID = job.id
USER_ID = user.id
db.close()

client = TestClient(main.app)
login = client.post("/api/v1/auth/login", json={"account": "qb_test@example.com", "password": "123456"})
check("登录", login.status_code == 200, str(login.status_code))
token = login.json()["data"]["access_token"]
H = {"Authorization": f"Bearer {token}"}

# ===== 1. 题库统计接口 =====
r = client.get("/api/v1/interviews/bank-stats", headers=H)
check("bank-stats 接口", r.status_code == 200 and r.json()["data"]["ready"], str(r.json()["data"].get("total")))
bt = r.json()["data"]["by_type"]
check("三类题型齐全", all(k in bt for k in ("PROFESSIONAL", "GENERAL", "STRESS")), str(bt))

# ===== 2. 配比接口 =====
r = client.get("/api/v1/interviews/paper-ratio", params={"mode": "COMPREHENSIVE", "total_questions": 10}, headers=H)
d = r.json()["data"]
check("5:3:2 配比分配 10 题", d["allocated"] == {"PROFESSIONAL": 5, "GENERAL": 3, "STRESS": 2}, str(d["allocated"]))
r = client.get("/api/v1/interviews/paper-ratio", params={"mode": "STRESS", "total_questions": 5}, headers=H)
check("STRESS 模式配比生效", sum(r.json()["data"]["allocated"].values()) == 5, str(r.json()["data"]["allocated"]))

# ===== 3. 组卷预览 =====
r = client.post("/api/v1/interviews/paper-preview",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM", "total_questions": 5},
                headers=H)
prev = r.json()["data"]
check("组卷预览返回 5 题", len(prev["questions"]) == 5, f"from_bank={prev['from_bank']}")
check("预览命中题库", prev["from_bank"] == 5 and prev["bank_available"] > 0)
check("预览含压力题", any(q["question_type"] == "STRESS" for q in prev["questions"]),
      str([q["question_type"] for q in prev["questions"]]))

# ===== 4. 创建面试（题库组卷）=====
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM",
                      "total_questions": 5, "duration_minutes": 25},
                headers=H)
check("创建面试", r.status_code == 200, str(r.status_code))
iv = r.json()["data"]
iv_id = iv["id"]
qs = iv["questions"]
check("卷面预生成全部 5 题（非仅首题）", len(qs) == 5, f"got={len(qs)}")
check("题目来源为题库", all(q["source"] == "QUESTION_BANK" for q in qs))
check("题目带题型标签", all(q["question_type"] in ("PROFESSIONAL", "GENERAL", "STRESS") for q in qs))
check("题目带限时", all(q["time_limit_sec"] >= 60 for q in qs))
check("作答阶段不下发参考答案（闭卷）",
      all(not q["reference_points"] and q["reveal_reference"] is False for q in qs))
check("题目带提示 hints", any(q["hints"] for q in qs))

# 卷面快照
db = SessionLocal()
plan = db.query(InterviewPlan).filter(InterviewPlan.interview_id == iv_id).first()
snap = json.loads(plan.paper_json) if plan and plan.paper_json else {}
check("卷面快照落库", snap.get("from_bank") == 5 and "ratio" in snap, str(snap.get("ratio")))
db.close()

# ===== 5. 逐题作答 =====
client.post(f"/api/v1/interviews/{iv_id}/start", headers=H)
answer_text = "我在电商项目中用 Redis 做热点缓存，采用 Cache Aside 模式：写时先更新数据库再删除缓存，" \
              "并用延迟双删与 Canal 订阅 binlog 兜底，配合布隆过滤器防穿透，逻辑过期防击穿，TTL 加随机抖动防雪崩。"
done_seqs = []
for i in range(5):
    r = client.post(f"/api/v1/interviews/{iv_id}/answer",
                    json={"text": answer_text, "duration_sec": 90}, headers=H)
    if r.status_code != 200:
        check(f"第{i+1}题作答", False, str(r.status_code) + r.text[:120])
        break
    d = r.json()["data"]
    check(f"第{i+1}题评分返回", 0 <= d["total_score"] <= 100, f"score={d['total_score']}")
    nq = d.get("next_question")
    if nq:
        done_seqs.append(d["answer_id"])
        check(f"第{i+1}题下一题不泄露参考答案", not nq.get("reference_points"))
check("答题推进产生 4 个下一题", len(done_seqs) == 4, f"got={len(done_seqs)}")

# ===== 6. 结算 + 报告含参考答案 =====
r = client.post(f"/api/v1/interviews/{iv_id}/finish", headers=H)
check("结算面试", r.status_code == 200, str(r.status_code) + r.text[:150])

r = client.get(f"/api/v1/interviews/{iv_id}/report", headers=H)
check("获取报告", r.status_code == 200)
qa = r.json()["data"]["questions_analysis"]
check("报告逐题数=5", len(qa) == 5, f"got={len(qa)}")
check("报告逐题含参考答案要点", all(len(x.get("reference_points", [])) > 0 for x in qa),
      f"first={len(qa[0]['reference_points']) if qa else 0}")
check("报告逐题含题型与来源", all(x.get("question_type") and x.get("source") for x in qa))

# 面试结束后 GET 应下发参考答案
r = client.get(f"/api/v1/interviews/{iv_id}", headers=H)
qs2 = r.json()["data"]["questions"]
check("结束后可见参考答案（复盘对照）",
      all(q["reference_points"] for q in qs2) and all(q["reveal_reference"] for q in qs2))

# ===== 7. 关闭题库走 AI 全量生成 =====
r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "TECHNICAL", "difficulty": "HARD",
                      "total_questions": 3, "use_question_bank": False},
                headers=H)
check("关闭题库仍可创建", r.status_code == 200)
iv2 = r.json()["data"]
check("关闭题库走 AI 生成", all(q["source"] == "AI_GENERATED" for q in iv2["questions"]),
      str([q["source"] for q in iv2["questions"]]))
check("AI 题也有参考答案兜底", all(q["reference_points"] == [] for q in iv2["questions"]))
db = SessionLocal()
p2 = db.query(InterviewPlan).filter(InterviewPlan.interview_id == iv2["id"]).first()
snap2 = json.loads(p2.paper_json) if p2 and p2.paper_json else {}
check("AI 模式记录卷面原因", snap2.get("reason") == "question_bank_disabled_or_empty", str(snap2))
db.close()

# ===== 8. 组卷多样性（同岗位两次抽题不完全相同）=====
def draw_texts():
    db = SessionLocal()
    j = db.query(Job).filter(Job.id == JOB_ID).first()
    from app.services.paper_builder import build_paper
    p = build_paper(db, j, "COMPREHENSIVE", "MEDIUM", 5)
    db.commit(); db.close()
    return {s.text for s in p.slots}

a, b = draw_texts(), draw_texts()
check("组卷具备随机多样性", len(a & b) < 5, f"overlap={len(a & b)}")

# ===== 9. 按已预览考卷开考（所见即所考）=====
r = client.post("/api/v1/interviews/paper-preview",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM", "total_questions": 5},
                headers=H)
picked = r.json()["data"]
picked_ids = [q["bank_id"] for q in picked["questions"] if q["bank_id"]]
picked_texts = [q["text"] for q in picked["questions"]]
check("预览返回题目 ID", len(picked_ids) == 5, str(picked_ids))

r = client.post("/api/v1/interviews",
                json={"job_id": JOB_ID, "mode": "COMPREHENSIVE", "difficulty": "MEDIUM",
                      "total_questions": 5, "selected_bank_ids": picked_ids},
                headers=H)
check("按选中考卷创建", r.status_code == 200)
iv3 = r.json()["data"]
actual_texts = [q["text"] for q in iv3["questions"]]
check("所见即所考（考卷文本与预览一致）", set(actual_texts) == set(picked_texts),
      f"actual={len(actual_texts)} picked={len(picked_texts)}")
check("卷面记录 user_selected_paper",
      json.loads(SessionLocal().query(InterviewPlan).filter(
          InterviewPlan.interview_id == iv3["id"]).first().paper_json).get("user_selected_paper") is True)

# ===== 10. 题库覆盖度：每个岗位大类都能组出满卷 =====
db = SessionLocal()
cats = {r.job_category for r in db.query(QuestionBank).distinct().filter(
    QuestionBank.job_category != "通用").all()} if hasattr(QuestionBank, "job_category") else set()
db.close()
from app.services.paper_builder import build_paper
db = SessionLocal()
j = db.query(Job).filter(Job.id == JOB_ID).first()
paper_full = build_paper(db, j, "COMPREHENSIVE", "MEDIUM", 10)
check("10 题满卷无缺口", not paper_full.missing and len(paper_full.slots) == 10,
      f"missing={paper_full.missing}")
db.close()

print("\n" + "=" * 60)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:", FAIL)
    sys.exit(1)
print("ALL CHECKS PASSED")
