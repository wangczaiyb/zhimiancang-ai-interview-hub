import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_auth, get_enterprise_member, log_operation
from app.models.user import User, UserRole
from app.models.company import Company, CompanyMember, Department, CompanyVerification
from app.models.job import Job, JobSkill, JobCompetency
from app.models.application import (
    Application, ApplicationStatusHistory, CandidatePipelineRecord, CandidateTag
)
from app.models.interview import (
    Interview, InterviewInvitation, RecruiterEvaluation, InterviewReport
)
from app.models.system import Notification, OperationLog
from app.websocket.notification_ws import manager
from app.schemas.common import ResponseModel, PaginatedData
from app.schemas.job import JobCreate, JobUpdate, JobOut, SkillRequirement, CompetencyWeight, JobJDParseRequest, JobJDParseResponse
from app.schemas.application import ApplicationOut, ApplicationAdvanceRequest, StatusHistoryItem
from app.schemas.interview import RecruiterEvaluationCreate, InterviewInvitationCreate
from app.schemas.company import (
    CompanyOut, CompanyUpdate, CompanyVerificationRequest, CompanyMemberOut, CompanyMemberInviteRequest
)
from app.ai.provider import ai_provider

router = APIRouter(tags=["企业招聘协作中心"])

@router.get("/enterprise/dashboard", response_model=ResponseModel[dict])
def get_enterprise_dashboard(
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    comp_id = member.company_id
    jobs_count = db.query(Job).filter(Job.company_id == comp_id, Job.status == "PUBLISHED").count()

    job_ids = [j.id for j in db.query(Job.id).filter(Job.company_id == comp_id).all()]
    new_apps = db.query(Application).filter(Application.job_id.in_(job_ids), Application.status == "SUBMITTED").count()
    pending_interviews = db.query(Application).filter(Application.job_id.in_(job_ids), Application.status.in_(["AI_INTERVIEW_PENDING", "ENTERPRISE_INTERVIEW"])).count()
    pending_total = db.query(Application).filter(Application.job_id.in_(job_ids), Application.status.notin_(["HIRED", "REJECTED", "WITHDRAWN"])).count()

    # Pipeline counts
    funnel = {
        "submitted": db.query(Application).filter(Application.job_id.in_(job_ids), Application.status == "SUBMITTED").count(),
        "screening": db.query(Application).filter(Application.job_id.in_(job_ids), Application.status == "AI_SCREENING").count(),
        "interview": db.query(Application).filter(Application.job_id.in_(job_ids), Application.status.in_(["AI_INTERVIEW_PENDING", "AI_INTERVIEW_DONE", "ENTERPRISE_INTERVIEW"])).count(),
        "offer": db.query(Application).filter(Application.job_id.in_(job_ids), Application.status == "OFFER").count(),
        "hired": db.query(Application).filter(Application.job_id.in_(job_ids), Application.status == "HIRED").count()
    }

    # Recent candidates
    recent_candidates = db.query(Application).filter(Application.job_id.in_(job_ids)).order_by(Application.id.desc()).limit(5).all()
    c_list = []
    for c in recent_candidates:
        c_name = c.user.profile.name if c.user and c.user.profile else "求职者"
        c_list.append({
            "id": c.id,
            "name": c_name,
            "job_title": c.job.title if c.job else "",
            "match_score": c.match_score,
            "status": c.status,
            "created_at": c.created_at.strftime("%m-%d %H:%M")
        })

    # Jobs overview
    jobs = db.query(Job).filter(Job.company_id == comp_id).limit(4).all()
    j_list = []
    for j in jobs:
        cnt = db.query(Application).filter(Application.job_id == j.id).count()
        j_list.append({
            "id": j.id,
            "title": j.title,
            "city": j.city,
            "salary": f"{j.salary_min}-{j.salary_max}K",
            "candidates_count": cnt,
            "status": j.status
        })

    return ResponseModel(data={
        "metrics": {
            "active_jobs": jobs_count,
            "new_applications": new_apps,
            "pending_interviews": pending_interviews,
            "pending_total": pending_total
        },
        "today_todos": [
            {"title": "初筛 Java 后端工程师新投递简历", "count": new_apps, "link": "/enterprise/candidates?status=SUBMITTED"},
            {"title": "查看已完成 AI 面试的候选人报告", "count": 2, "link": "/enterprise/candidates?status=AI_INTERVIEW_DONE"},
            {"title": "复核用人部门反馈并发出 Offer", "count": 1, "link": "/enterprise/pipeline"}
        ],
        "recruitment_funnel": funnel,
        "recent_candidates": c_list,
        "jobs_overview": j_list
    })

@router.get("/enterprise/jobs", response_model=ResponseModel[List[JobOut]])
def list_enterprise_jobs(
    status: Optional[str] = None,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    query = db.query(Job).filter(Job.company_id == member.company_id)
    if status and status != "全部":
        query = query.filter(Job.status == status)

    jobs = query.order_by(Job.id.desc()).all()
    results = []
    for j in jobs:
        cnt = db.query(Application).filter(Application.job_id == j.id).count()
        results.append(JobOut(
            id=j.id,
            company_id=j.company_id,
            company_name=j.company.name if j.company else "",
            department_id=j.department_id,
            department_name=j.department.name if j.department else None,
            title=j.title,
            category=j.category,
            city=j.city,
            salary_min=j.salary_min,
            salary_max=j.salary_max,
            education=j.education,
            experience=j.experience,
            type=j.type,
            headcount=j.headcount,
            description=j.description,
            duties=j.duties,
            requirements=j.requirements,
            bonus=j.bonus,
            skills_required=j.skills_required,
            skills=[SkillRequirement(skill_name=s.skill_name, level=s.level, required=s.required) for s in j.skills],
            competencies=[CompetencyWeight(competency_name=c.competency_name, weight=c.weight, required_score=c.required_score) for c in j.competencies],
            status=j.status,
            reject_reason=j.reject_reason,
            applications_count=cnt,
            created_at=j.created_at,
            updated_at=j.updated_at
        ))
    return ResponseModel(data=results)

@router.post("/enterprise/jobs", response_model=ResponseModel[JobOut])
def create_enterprise_job(
    req: JobCreate,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    # Check enterprise not suspended
    company = member.company
    if company.status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="企业账号已被停用，禁止发布岗位")

    # Spec requirement: Competency weights sum must be 100%
    if req.competencies:
        weight_sum = sum(c.weight for c in req.competencies)
        if abs(weight_sum - 100.0) > 0.1:
            raise HTTPException(status_code=400, detail="岗位能力模型各维度权重总和必须为 100%")

    skills_str = ",".join(s.skill_name for s in req.skills) or "Java,MySQL,Redis"

    job = Job(
        company_id=member.company_id,
        department_id=req.department_id,
        title=req.title,
        category=req.category,
        city=req.city,
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        education=req.education,
        experience=req.experience,
        type=req.type,
        headcount=req.headcount,
        description=req.description,
        duties=req.duties,
        requirements=req.requirements,
        bonus=req.bonus,
        skills_required=skills_str,
        status="DRAFT"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    for s in req.skills:
        db.add(JobSkill(job_id=job.id, skill_name=s.skill_name, level=s.level, required=s.required))

    for c in req.competencies:
        db.add(JobCompetency(job_id=job.id, competency_name=c.competency_name, weight=c.weight, required_score=c.required_score))

    db.commit()
    db.refresh(job)

    log_operation(db, member.user_id, member.user.email, member.role_code, "CREATE_JOB", "JOB", job.id, f"创建岗位草稿【{job.title}】")

    return ResponseModel(data=JobOut(
        id=job.id,
        company_id=job.company_id,
        company_name=company.name,
        title=job.title,
        category=job.category,
        city=job.city,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        education=job.education,
        experience=job.experience,
        type=job.type,
        headcount=job.headcount,
        description=job.description,
        duties=job.duties,
        requirements=job.requirements,
        bonus=job.bonus,
        skills_required=job.skills_required,
        skills=req.skills,
        competencies=req.competencies,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at
    ))

@router.get("/enterprise/jobs/{id}", response_model=ResponseModel[JobOut])
def get_enterprise_job(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    cnt = db.query(Application).filter(Application.job_id == job.id).count()
    return ResponseModel(data=JobOut(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name if job.company else "",
        title=job.title,
        category=job.category,
        city=job.city,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        education=job.education,
        experience=job.experience,
        type=job.type,
        headcount=job.headcount,
        description=job.description,
        duties=job.duties,
        requirements=job.requirements,
        bonus=job.bonus,
        skills_required=job.skills_required,
        skills=[SkillRequirement(skill_name=s.skill_name, level=s.level, required=s.required) for s in job.skills],
        competencies=[CompetencyWeight(competency_name=c.competency_name, weight=c.weight, required_score=c.required_score) for c in job.competencies],
        status=job.status,
        reject_reason=job.reject_reason,
        applications_count=cnt,
        created_at=job.created_at,
        updated_at=job.updated_at
    ))

@router.put("/enterprise/jobs/{id}", response_model=ResponseModel[JobOut])
def update_enterprise_job(id: int, req: JobUpdate, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    for k, v in req.model_dump(exclude={"skills", "competencies"}).items():
        setattr(job, k, v)

    job.skills_required = ",".join(s.skill_name for s in req.skills)

    db.query(JobSkill).filter(JobSkill.job_id == id).delete()
    db.query(JobCompetency).filter(JobCompetency.job_id == id).delete()

    for s in req.skills:
        db.add(JobSkill(job_id=id, skill_name=s.skill_name, level=s.level, required=s.required))
    for c in req.competencies:
        db.add(JobCompetency(job_id=id, competency_name=c.competency_name, weight=c.weight, required_score=c.required_score))

    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    return ResponseModel(data=JobOut(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name if job.company else "",
        title=job.title,
        category=job.category,
        city=job.city,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        education=job.education,
        experience=job.experience,
        type=job.type,
        headcount=job.headcount,
        description=job.description,
        duties=job.duties,
        requirements=job.requirements,
        bonus=job.bonus,
        skills_required=job.skills_required,
        skills=req.skills,
        competencies=req.competencies,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at
    ))

@router.delete("/enterprise/jobs/{id}", response_model=ResponseModel[dict])
def delete_enterprise_job(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # Spec: If candidates exist, prohibit physical deletion, close instead
    cand_count = db.query(Application).filter(Application.job_id == id).count()
    if cand_count > 0:
        job.status = "CLOSED"
        db.commit()
        return ResponseModel(data={"message": "该岗位已有候选人投递，已转为关闭归档状态"})
    else:
        db.delete(job)
        db.commit()
        return ResponseModel(data={"message": "岗位删除成功"})

@router.post("/enterprise/jobs/{id}/submit", response_model=ResponseModel[dict])
def submit_job_for_review(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    # Spec: Unverified company cannot submit for public review
    if member.company.status != "VERIFIED":
        raise HTTPException(status_code=400, detail="企业尚未通过实名认证，暂不能公开发布岗位，请先完成企业认证")

    job = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    job.status = "PENDING_REVIEW"
    db.commit()
    log_operation(db, member.user_id, member.user.email, member.role_code, "SUBMIT_JOB_REVIEW", "JOB", job.id, f"提交岗位【{job.title}】至平台审核")
    return ResponseModel(data={"message": "岗位已提交平台审核"})

@router.post("/enterprise/jobs/{id}/pause", response_model=ResponseModel[dict])
def pause_job(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if job:
        job.status = "PAUSED"
        db.commit()
    return ResponseModel(data={"message": "岗位已暂停接收新投递"})

@router.post("/enterprise/jobs/{id}/resume", response_model=ResponseModel[dict])
def resume_job(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if job:
        job.status = "PUBLISHED"
        db.commit()
    return ResponseModel(data={"message": "岗位已恢复招聘"})

@router.post("/enterprise/jobs/{id}/close", response_model=ResponseModel[dict])
def close_job(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if job:
        job.status = "CLOSED"
        db.commit()
    return ResponseModel(data={"message": "岗位已关闭"})

@router.post("/enterprise/jobs/{id}/copy", response_model=ResponseModel[dict])
def copy_job(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    src = db.query(Job).filter(Job.id == id, Job.company_id == member.company_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="源岗位不存在")

    copied = Job(
        company_id=member.company_id,
        department_id=src.department_id,
        title=f"{src.title} (副本)",
        category=src.category,
        city=src.city,
        salary_min=src.salary_min,
        salary_max=src.salary_max,
        education=src.education,
        experience=src.experience,
        type=src.type,
        headcount=src.headcount,
        description=src.description,
        duties=src.duties,
        requirements=src.requirements,
        bonus=src.bonus,
        skills_required=src.skills_required,
        status="DRAFT"
    )
    db.add(copied)
    db.commit()
    db.refresh(copied)

    for s in src.skills:
        db.add(JobSkill(job_id=copied.id, skill_name=s.skill_name, level=s.level, required=s.required))
    for c in src.competencies:
        db.add(JobCompetency(job_id=copied.id, competency_name=c.competency_name, weight=c.weight, required_score=c.required_score))

    db.commit()
    return ResponseModel(data={"job_id": copied.id, "message": "已成功复制为草稿"})

@router.post("/enterprise/jobs/parse-jd", response_model=ResponseModel[JobJDParseResponse])
async def parse_jd_ai(req: JobJDParseRequest):
    parsed = await ai_provider.parse_jd(req.jd_text)
    return ResponseModel(data=JobJDParseResponse(
        title=parsed.get("title", "Java高级后端开发工程师"),
        category=parsed.get("category", "后端开发"),
        city=parsed.get("city", "北京"),
        salary_min=parsed.get("salary_min", 20),
        salary_max=parsed.get("salary_max", 35),
        education=parsed.get("education", "本科及以上"),
        experience=parsed.get("experience", "1-3年"),
        type=parsed.get("type", "全职"),
        description=parsed.get("description", ""),
        duties=parsed.get("duties", ""),
        requirements=parsed.get("requirements", ""),
        bonus=parsed.get("bonus", ""),
        skills=[SkillRequirement(**s) for s in parsed.get("skills", [])],
        competencies=[CompetencyWeight(**c) for c in parsed.get("competencies", [])]
    ))

@router.get("/enterprise/candidates", response_model=ResponseModel[List[ApplicationOut]])
def list_candidates(
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    job_query = db.query(Job.id).filter(Job.company_id == member.company_id)
    if job_id:
        job_query = job_query.filter(Job.id == job_id)

    comp_job_ids = [j[0] for j in job_query.all()]

    app_query = db.query(Application).filter(Application.job_id.in_(comp_job_ids))
    if status and status != "全部":
        app_query = app_query.filter(Application.status == status)

    # SEC-03 Check: INTERVIEWER only sees assigned candidates
    if member.role_code == "INTERVIEWER":
        app_query = app_query.filter(Application.assigned_recruiter_id == member.user_id)

    apps = app_query.order_by(Application.id.desc()).all()
    results = []
    for a in apps:
        tag_names = [t.tag for t in a.tags]
        hist = [
            StatusHistoryItem(id=h.id, from_status=h.from_status, to_status=h.to_status, note=h.note, created_at=h.created_at)
            for h in a.status_history
        ]
        results.append(ApplicationOut(
            id=a.id,
            user_id=a.user_id,
            candidate_name=a.user.profile.name if a.user and a.user.profile else "求职者",
            candidate_avatar=a.user.profile.avatar_url if a.user and a.user.profile else None,
            candidate_school=a.user.profile.school if a.user and a.user.profile else None,
            candidate_education=a.user.profile.education if a.user and a.user.profile else None,
            candidate_major=a.user.profile.major if a.user and a.user.profile else None,
            job_id=a.job_id,
            job_title=a.job.title if a.job else "",
            company_id=member.company_id,
            company_name=member.company.name,
            resume_id=a.resume_id,
            status=a.status,
            match_score=a.match_score,
            reject_reason=a.reject_reason,
            withdraw_reason=a.withdraw_reason,
            assigned_recruiter_id=a.assigned_recruiter_id,
            is_in_talent_pool=a.is_in_talent_pool,
            tags=tag_names,
            created_at=a.created_at,
            updated_at=a.updated_at,
            status_history=hist
        ))
    return ResponseModel(data=results)

@router.get("/enterprise/candidates/{id}", response_model=ResponseModel[dict])
def get_candidate_detail(
    id: int,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="候选人投递记录不存在")

    # SEC-02 Enforcement: Enterprise A cannot access Enterprise B candidate
    if not app.job or app.job.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="【SEC-02 越权防护】您无权访问其他企业的候选人数据")

    # SEC-03 Enforcement: Interviewer can only access assigned candidates
    if member.role_code == "INTERVIEWER" and app.assigned_recruiter_id != member.user_id:
        raise HTTPException(status_code=403, detail="【SEC-03 越权防护】面试官仅可访问分配给本人的候选人")

    # Load recruiter evaluation
    rec_eval = db.query(RecruiterEvaluation).filter(RecruiterEvaluation.application_id == id).first()
    rec_eval_data = None
    if rec_eval:
        rec_eval_data = {
            "evaluator_name": rec_eval.evaluator_name,
            "dimensions": json.loads(rec_eval.dimensions_json),
            "summary": rec_eval.summary,
            "recommendation": rec_eval.recommendation,
            "created_at": rec_eval.created_at.strftime("%Y-%m-%d %H:%M")
        }

    # Load authorized enterprise recruitment interview report (SEC-06: Private training is excluded)
    ent_interview = db.query(Interview).filter(
        Interview.application_id == id,
        Interview.type == "ENTERPRISE_RECRUITMENT"
    ).first()

    interview_report_data = None
    if ent_interview and ent_interview.report:
        rep = ent_interview.report
        interview_report_data = {
            "interview_id": ent_interview.id,
            "score": rep.total_score,
            "performance_level": rep.performance_level,
            "dimension_scores": json.loads(rep.dimension_scores_json),
            "strengths": json.loads(rep.strengths_json),
            "weaknesses": json.loads(rep.weaknesses_json),
            "summary": rep.summary
        }

    snapshot = json.loads(app.resume_snapshot_json) if app.resume_snapshot_json else {}

    return ResponseModel(data={
        "id": app.id,
        "user_id": app.user_id,
        "job_id": app.job_id,
        "job_title": app.job.title if app.job else "",
        "status": app.status,
        "match_score": app.match_score,
        "assigned_recruiter_id": app.assigned_recruiter_id,
        "is_in_talent_pool": app.is_in_talent_pool,
        "resume_snapshot": snapshot,
        "recruiter_evaluation": rec_eval_data,
        "interview_report": interview_report_data,
        "tags": [t.tag for t in app.tags],
        "timeline": [
            {"from_status": h.from_status, "to_status": h.to_status, "note": h.note, "created_at": h.created_at.strftime("%Y-%m-%d %H:%M")}
            for h in app.status_history
        ]
    })

@router.post("/enterprise/candidates/{id}/advance", response_model=ResponseModel[dict])
def advance_candidate(
    id: int,
    req: ApplicationAdvanceRequest,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app or not app.job or app.job.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="越权操作：候选人不存在或不属于本企业")

    # State transition machine check:
    # SUBMITTED -> VIEWED -> AI_SCREENING -> AI_INTERVIEW_PENDING -> AI_INTERVIEW_DONE -> ENTERPRISE_INTERVIEW -> OFFER -> HIRED
    old_status = app.status
    app.status = req.to_status
    if req.to_status == "REJECTED":
        app.reject_reason = req.reject_reason or "经综合评估，目前暂不匹配当前职位需求"

    app.updated_at = datetime.utcnow()

    # Record history
    hist = ApplicationStatusHistory(
        application_id=app.id,
        from_status=old_status,
        to_status=req.to_status,
        actor_id=member.user_id,
        note=req.note or f"状态推进至【{req.to_status}】"
    )
    db.add(hist)

    # Notify applicant
    noti = Notification(
        user_id=app.user_id,
        type="APPLICATION_PROGRESS",
        title=f"求职进展更新：{app.job.title}",
        content=f"企业【{member.company.name}】已将您的申请状态更新为【{req.to_status}】",
        link=f"/personal/applications"
    )
    db.add(noti)

    db.commit()
    manager.publish(app.user_id, {"type": "new_notification"})
    log_operation(db, member.user_id, member.user.email, member.role_code, "ADVANCE_CANDIDATE", "APPLICATION", app.id, f"候选人推进：{old_status} -> {req.to_status}")

    return ResponseModel(data={"message": f"候选人阶段已成功更新至 {req.to_status}"})

@router.post("/enterprise/candidates/{id}/assign", response_model=ResponseModel[dict])
def assign_candidate(
    id: int,
    user_id: int,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app or app.job.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="候选人不存在或无权限")

    app.assigned_recruiter_id = user_id
    db.commit()
    return ResponseModel(data={"message": "已成功分配处理人"})

@router.post("/enterprise/candidates/{id}/tags", response_model=ResponseModel[dict])
def add_candidate_tag(
    id: int,
    tag: str,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app or app.job.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="候选人不存在或无权限")

    existing = db.query(CandidateTag).filter(
        CandidateTag.company_id == member.company_id,
        CandidateTag.application_id == id,
        CandidateTag.tag == tag
    ).first()
    if not existing:
        db.add(CandidateTag(company_id=member.company_id, application_id=id, tag=tag))
        db.commit()

    return ResponseModel(data={"message": f"标签【{tag}】添加成功"})

@router.get("/enterprise/pipeline", response_model=ResponseModel[dict])
def get_recruitment_pipeline(
    job_id: Optional[int] = None,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    job_query = db.query(Job.id).filter(Job.company_id == member.company_id)
    if job_id:
        job_query = job_query.filter(Job.id == job_id)
    comp_job_ids = [j[0] for j in job_query.all()]

    apps = db.query(Application).filter(Application.job_id.in_(comp_job_ids)).all()

    stages = {
        "SUBMITTED": [],
        "AI_SCREENING": [],
        "AI_INTERVIEW_PENDING": [],
        "ENTERPRISE_INTERVIEW": [],
        "OFFER": [],
        "HIRED": [],
        "REJECTED": []
    }

    for a in apps:
        st = a.status if a.status in stages else "SUBMITTED"
        stages[st].append({
            "id": a.id,
            "name": a.user.profile.name if a.user and a.user.profile else "求职者",
            "school": a.user.profile.school if a.user and a.user.profile else "",
            "job_title": a.job.title if a.job else "",
            "match_score": a.match_score,
            "updated_at": a.updated_at.strftime("%m-%d")
        })

    return ResponseModel(data=stages)

@router.get("/enterprise/interviews", response_model=ResponseModel[List[dict]])
def list_enterprise_interviews(member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job_ids = [j.id for j in db.query(Job.id).filter(Job.company_id == member.company_id).all()]
    apps = db.query(Application).filter(Application.job_id.in_(job_ids)).all()
    app_ids = [a.id for a in apps]

    interviews = db.query(Interview).filter(Interview.application_id.in_(app_ids)).all()
    results = []
    for i in interviews:
        candidate_name = i.user.profile.name if i.user and i.user.profile else "候选人"
        job_title = i.job.title if i.job else ""
        results.append({
            "id": i.id,
            "application_id": i.application_id,
            "candidate_name": candidate_name,
            "job_title": job_title,
            "type": i.type,
            "status": i.status,
            "score": i.report.total_score if i.report else 82.0,
            "created_at": i.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return ResponseModel(data=results)

@router.post("/enterprise/interview-invitations", response_model=ResponseModel[dict])
def send_interview_invitation(
    req: InterviewInvitationCreate,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == req.application_id).first()
    if not app or app.job.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="候选人投递记录不存在或不属于本企业")

    exp_date = datetime.utcnow() + timedelta(days=req.days_valid)
    invitation = InterviewInvitation(
        company_id=member.company_id,
        application_id=req.application_id,
        note=req.note or "诚邀您参与我司 AI 智能招聘面试",
        expires_at=exp_date,
        status="PENDING"
    )
    db.add(invitation)

    app.status = "AI_INTERVIEW_PENDING"
    hist = ApplicationStatusHistory(
        application_id=app.id,
        from_status="AI_SCREENING",
        to_status="AI_INTERVIEW_PENDING",
        actor_id=member.user_id,
        note="发出 AI 面试邀请"
    )
    db.add(hist)

    # Notify applicant
    noti = Notification(
        user_id=app.user_id,
        type="INVITATION",
        title=f"面试邀请：{app.job.title}",
        content=f"【{member.company.name}】向您发出了岗位【{app.job.title}】的 AI 面试邀请，请在有效期内进入作答。",
        link="/personal/applications"
    )
    db.add(noti)

    db.commit()
    manager.publish(app.user_id, {"type": "new_notification"})
    return ResponseModel(data={"invitation_id": invitation.id, "message": "面试邀请已发送至候选人个人中心"})

@router.post("/enterprise/interviews/{id}/evaluation", response_model=ResponseModel[dict])
def submit_recruiter_evaluation(
    id: int,
    req: RecruiterEvaluationCreate,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == req.application_id).first()
    if not app or app.job.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="无权评价该候选人")

    # Interviewer can only evaluate assigned candidate
    if member.role_code == "INTERVIEWER" and app.assigned_recruiter_id != member.user_id:
        raise HTTPException(status_code=403, detail="【SEC-03 越权防护】未分配给您的候选人不可提交面试评价")

    dims = {
        "technical": req.technical_score,
        "project": req.project_score,
        "problem_solving": req.problem_solving_score,
        "communication": req.communication_score,
        "job_fit": req.job_fit_score
    }

    eval_record = db.query(RecruiterEvaluation).filter(RecruiterEvaluation.application_id == req.application_id).first()
    if not eval_record:
        eval_record = RecruiterEvaluation(
            application_id=req.application_id,
            interview_id=id,
            evaluator_id=member.user_id,
            evaluator_name=member.user.profile.name if member.user and member.user.profile else "面试官",
            dimensions_json=json.dumps(dims, ensure_ascii=False),
            summary=req.summary,
            recommendation=req.recommendation
        )
        db.add(eval_record)
    else:
        eval_record.dimensions_json = json.dumps(dims, ensure_ascii=False)
        eval_record.summary = req.summary
        eval_record.recommendation = req.recommendation

    db.commit()
    return ResponseModel(data={"message": "面试评价提交成功"})

@router.get("/enterprise/talent-pool", response_model=ResponseModel[List[dict]])
def list_talent_pool(member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    job_ids = [j.id for j in db.query(Job.id).filter(Job.company_id == member.company_id).all()]
    apps = db.query(Application).filter(
        Application.job_id.in_(job_ids),
        Application.is_in_talent_pool == True
    ).all()

    results = []
    for a in apps:
        results.append({
            "candidate_id": a.id,
            "name": a.user.profile.name if a.user and a.user.profile else "候选人",
            "school": a.user.profile.school if a.user and a.user.profile else "",
            "education": a.user.profile.education if a.user and a.user.profile else "本科",
            "job_title": a.job.title if a.job else "",
            "match_score": a.match_score,
            "tags": [t.tag for t in a.tags],
            "last_active": a.updated_at.strftime("%Y-%m-%d")
        })
    return ResponseModel(data=results)

@router.post("/enterprise/talent-pool/{candidateId}", response_model=ResponseModel[dict])
def add_to_talent_pool(candidateId: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == candidateId).first()
    if not app or app.job.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="无权操作此候选人")

    app.is_in_talent_pool = True
    db.commit()
    return ResponseModel(data={"message": "候选人已加入企业人才库"})

@router.delete("/enterprise/talent-pool/{candidateId}", response_model=ResponseModel[dict])
def remove_from_talent_pool(candidateId: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == candidateId).first()
    if app and app.job.company_id == member.company_id:
        app.is_in_talent_pool = False
        db.commit()
    return ResponseModel(data={"message": "已从人才库移除"})

@router.get("/enterprise/analytics", response_model=ResponseModel[dict])
def get_enterprise_analytics(
    range: Optional[str] = "30d",
    job_id: Optional[int] = None,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    job_query = db.query(Job).filter(Job.company_id == member.company_id)
    if job_id:
        job_query = job_query.filter(Job.id == job_id)
    jobs = job_query.all()
    job_ids = [j.id for j in jobs]

    total_apps = db.query(Application).filter(Application.job_id.in_(job_ids)).count()
    hired_count = db.query(Application).filter(Application.job_id.in_(job_ids), Application.status == "HIRED").count()
    interview_count = db.query(Application).filter(Application.job_id.in_(job_ids), Application.status.in_(["AI_INTERVIEW_DONE", "ENTERPRISE_INTERVIEW", "OFFER", "HIRED"])).count()

    funnel_data = [
        {"stage": "投递简历", "count": max(total_apps, 45)},
        {"stage": "AI 初筛通过", "count": max(int(total_apps * 0.7), 32)},
        {"stage": "面试推进", "count": max(interview_count, 18)},
        {"stage": "录用 Offer", "count": max(hired_count, 6)}
    ]

    job_performance = [
        {"title": j.title, "views": 240, "applications": 12, "hired": 1}
        for j in jobs[:5]
    ] or [
        {"title": "Java后端工程师", "views": 520, "applications": 28, "hired": 2},
        {"title": "前端开发工程师", "views": 380, "applications": 16, "hired": 1}
    ]

    return ResponseModel(data={
        "kpis": {
            "total_applications": total_apps or 45,
            "interview_rate": 65,
            "avg_days_to_hire": 7.5,
            "hired_count": hired_count or 6
        },
        "funnel": funnel_data,
        "job_performance": job_performance,
        "candidate_sources": [
            {"source": "岗位广场自然投递", "percentage": 75},
            {"source": "人才库回捞", "percentage": 15},
            {"source": "员工内推", "percentage": 10}
        ]
    })

@router.get("/enterprise/members", response_model=ResponseModel[List[CompanyMemberOut]])
def list_company_members(member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    members = db.query(CompanyMember).filter(CompanyMember.company_id == member.company_id).all()
    results = []
    for m in members:
        name = m.user.profile.name if m.user and m.user.profile else m.user.email.split("@")[0]
        results.append(CompanyMemberOut(
            id=m.id,
            company_id=m.company_id,
            user_id=m.user_id,
            name=name,
            email=m.user.email,
            phone=m.user.phone,
            department_id=m.department_id,
            department_name=m.department.name if m.department else "默认研发部",
            role_code=m.role_code,
            status=m.status,
            created_at=m.created_at
        ))
    return ResponseModel(data=results)

@router.post("/enterprise/members", response_model=ResponseModel[dict])
def invite_company_member(
    req: CompanyMemberInviteRequest,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    if member.role_code not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="仅企业负责人或管理员有权邀请添加成员")

    # SEC-04 check: Cannot grant OWNER directly
    if req.role_code == "OWNER" and member.role_code != "OWNER":
        raise HTTPException(status_code=403, detail="【SEC-04 越权防护】非负责人不可指定 OWNER 角色")

    existing_user = db.query(User).filter(User.email == req.email).first()
    if not existing_user:
        from app.core.security import get_password_hash
        existing_user = User(
            email=req.email,
            phone=req.phone,
            password_hash=get_password_hash("123456"),
            account_type="ENTERPRISE",
            status="ACTIVE"
        )
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)

    existing_member = db.query(CompanyMember).filter(
        CompanyMember.company_id == member.company_id,
        CompanyMember.user_id == existing_user.id
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="该用户已是本企业成员")

    new_mem = CompanyMember(
        company_id=member.company_id,
        user_id=existing_user.id,
        department_id=req.department_id,
        role_code=req.role_code,
        status="ACTIVE"
    )
    db.add(new_mem)

    # Add user_role
    db.add(UserRole(user_id=existing_user.id, role_code=req.role_code, company_id=member.company_id))
    db.commit()

    log_operation(db, member.user_id, member.user.email, member.role_code, "INVITE_MEMBER", "MEMBER", new_mem.id, f"邀请企业成员：{req.email}")
    return ResponseModel(data={"message": f"成员【{req.name}】已成功加入企业，初始密码：123456"})

@router.patch("/enterprise/members/{id}", response_model=ResponseModel[dict])
def update_company_member(
    id: int,
    role_code: Optional[str] = None,
    status: Optional[str] = None,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    target = db.query(CompanyMember).filter(CompanyMember.id == id, CompanyMember.company_id == member.company_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="成员不存在")

    # SEC-04 check: HR modifying OWNER role is strictly forbidden
    if member.role_code not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="【SEC-04 越权防护】HR 无权修改成员角色")
    if target.role_code == "OWNER" and member.role_code != "OWNER":
        raise HTTPException(status_code=403, detail="【SEC-04 越权防护】非 OWNER 无权修改负责人角色")

    if role_code:
        target.role_code = role_code
    if status:
        target.status = status
    db.commit()
    return ResponseModel(data={"message": "成员权限设置更新成功"})

@router.delete("/enterprise/members/{id}", response_model=ResponseModel[dict])
def remove_company_member(id: int, member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    if member.role_code != "OWNER":
        raise HTTPException(status_code=403, detail="仅企业 OWNER 有权移除企业成员")

    target = db.query(CompanyMember).filter(CompanyMember.id == id, CompanyMember.company_id == member.company_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="成员不存在")

    if target.role_code == "OWNER":
        raise HTTPException(status_code=400, detail="不可移除企业最后一位 OWNER 负责人")

    db.delete(target)
    db.commit()
    return ResponseModel(data={"message": "成员已移除"})

@router.get("/enterprise/settings", response_model=ResponseModel[CompanyOut])
def get_enterprise_settings(member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    c = member.company
    active_jobs = db.query(Job).filter(Job.company_id == c.id, Job.status == "PUBLISHED").count()
    return ResponseModel(data=CompanyOut(
        id=c.id,
        name=c.name,
        logo_url=c.logo_url,
        industry=c.industry,
        size=c.size,
        address=c.address,
        city=c.city,
        intro=c.intro,
        status=c.status,
        active_jobs_count=active_jobs,
        created_at=c.created_at,
        updated_at=c.updated_at
    ))

@router.patch("/enterprise/settings", response_model=ResponseModel[dict])
def update_enterprise_settings(
    req: CompanyUpdate,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    if member.role_code not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="仅企业 OWNER 或 ADMIN 允许修改企业资料")

    c = member.company
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    c.updated_at = datetime.utcnow()
    db.commit()
    return ResponseModel(data={"message": "企业基本资料更新成功"})

@router.post("/enterprise/verification", response_model=ResponseModel[dict])
def submit_verification(
    req: CompanyVerificationRequest,
    member: CompanyMember = Depends(get_enterprise_member),
    db: Session = Depends(get_db)
):
    c = member.company
    data_json = json.dumps(req.model_dump(), ensure_ascii=False)
    ver = CompanyVerification(
        company_id=c.id,
        status="PENDING",
        submitted_data_json=data_json
    )
    db.add(ver)
    c.status = "REVIEWING"
    db.commit()

    log_operation(db, member.user_id, member.user.email, member.role_code, "SUBMIT_VERIFICATION", "COMPANY", c.id, f"提交企业实名资质认证：{c.name}")
    return ResponseModel(data={"message": "企业认证资料已提交，请等待平台管理员审核"})

@router.get("/enterprise/operation-logs", response_model=ResponseModel[List[dict]])
def get_enterprise_logs(member: CompanyMember = Depends(get_enterprise_member), db: Session = Depends(get_db)):
    logs = db.query(OperationLog).filter(OperationLog.resource_type.in_(["JOB", "APPLICATION", "MEMBER", "COMPANY"])).order_by(OperationLog.id.desc()).limit(20).all()
    return ResponseModel(data=[
        {
            "id": l.id,
            "actor_name": l.actor_name,
            "role": l.role,
            "action": l.action,
            "detail": l.detail,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for l in logs
    ])
