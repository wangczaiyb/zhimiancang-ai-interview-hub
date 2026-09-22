import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_auth, log_operation
from app.models.user import User
from app.models.company import Company
from app.models.job import Job, JobSkill, JobCompetency, JobFavorite
from app.models.resume import Resume
from app.models.application import Application, ApplicationStatusHistory
from app.models.system import Notification
from app.websocket.notification_ws import manager
from app.schemas.common import ResponseModel, PaginatedData
from app.schemas.job import JobOut, SkillRequirement, CompetencyWeight
from app.schemas.application import ApplicationCreate, ApplicationOut
from app.ai.provider import ai_provider

router = APIRouter(tags=["岗位相关"])

@router.get("/jobs", response_model=ResponseModel[PaginatedData[JobOut]])
def list_public_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    education: Optional[str] = None,
    experience: Optional[str] = None,
    type: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    sort: Optional[str] = "latest", # latest, salary, match
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Job).filter(Job.status == "PUBLISHED")

    if keyword:
        query = query.filter(
            (Job.title.contains(keyword)) |
            (Job.description.contains(keyword)) |
            (Job.skills_required.contains(keyword))
        )
    if city and city != "全部":
        query = query.filter(Job.city == city)
    if category and category != "全部":
        query = query.filter(Job.category == category)
    if education and education != "全部":
        query = query.filter(Job.education == education)
    if experience and experience != "全部":
        query = query.filter(Job.experience == experience)
    if type and type != "全部":
        query = query.filter(Job.type == type)
    if salary_min:
        query = query.filter(Job.salary_min >= salary_min)
    if salary_max:
        query = query.filter(Job.salary_max <= salary_max)

    if sort == "salary":
        query = query.order_by(Job.salary_max.desc())
    else:
        query = query.order_by(Job.id.desc())

    total = query.count()
    jobs = query.offset((page - 1) * page_size).limit(page_size).all()

    # Favorite set for current user
    fav_ids = set()
    if current_user:
        favs = db.query(JobFavorite.job_id).filter(JobFavorite.user_id == current_user.id).all()
        fav_ids = {f[0] for f in favs}

    items = []
    for j in jobs:
        skill_objs = [
            SkillRequirement(skill_name=s.skill_name, level=s.level, required=s.required)
            for s in j.skills
        ]
        comp_objs = [
            CompetencyWeight(competency_name=c.competency_name, weight=c.weight, required_score=c.required_score)
            for c in j.competencies
        ]
        # Match score calculation
        match_score = 85
        if current_user and current_user.profile:
            match_score = 88

        items.append(JobOut(
            id=j.id,
            company_id=j.company_id,
            company_name=j.company.name if j.company else "",
            company_logo=j.company.logo_url if j.company else None,
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
            skills=skill_objs,
            competencies=comp_objs,
            status=j.status,
            reject_reason=j.reject_reason,
            is_favorited=j.id in fav_ids,
            match_score=match_score,
            created_at=j.created_at,
            updated_at=j.updated_at
        ))

    total_pages = (total + page_size - 1) // page_size
    return ResponseModel(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    ))

@router.get("/jobs/{id}", response_model=ResponseModel[JobOut])
def get_job_detail(id: int, current_user: Optional[User] = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在或已被删除")

    is_fav = False
    if current_user:
        is_fav = db.query(JobFavorite).filter(
            JobFavorite.user_id == current_user.id,
            JobFavorite.job_id == id
        ).first() is not None

    skill_objs = [
        SkillRequirement(skill_name=s.skill_name, level=s.level, required=s.required)
        for s in job.skills
    ]
    comp_objs = [
        CompetencyWeight(competency_name=c.competency_name, weight=c.weight, required_score=c.required_score)
        for c in job.competencies
    ]

    return ResponseModel(data=JobOut(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name if job.company else "",
        company_logo=job.company.logo_url if job.company else None,
        department_id=job.department_id,
        department_name=job.department.name if job.department else None,
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
        skills=skill_objs,
        competencies=comp_objs,
        status=job.status,
        reject_reason=job.reject_reason,
        is_favorited=is_fav,
        match_score=88 if current_user else None,
        created_at=job.created_at,
        updated_at=job.updated_at
    ))

@router.post("/jobs/{id}/favorite", response_model=ResponseModel[dict])
def favorite_job(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if current_user.account_type != "PERSONAL":
        raise HTTPException(status_code=403, detail="仅个人求职者账号可收藏岗位")

    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    fav = db.query(JobFavorite).filter(
        JobFavorite.user_id == current_user.id,
        JobFavorite.job_id == id
    ).first()
    if not fav:
        fav = JobFavorite(user_id=current_user.id, job_id=id)
        db.add(fav)
        db.commit()
    return ResponseModel(data={"favorited": True})

@router.delete("/jobs/{id}/favorite", response_model=ResponseModel[dict])
def unfavorite_job(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    db.query(JobFavorite).filter(
        JobFavorite.user_id == current_user.id,
        JobFavorite.job_id == id
    ).delete()
    db.commit()
    return ResponseModel(data={"favorited": False})

@router.post("/jobs/{id}/apply", response_model=ResponseModel[dict])
def apply_job(id: int, req: ApplicationCreate, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if current_user.account_type != "PERSONAL":
        raise HTTPException(status_code=403, detail="企业角色账号不可投递岗位")

    job = db.query(Job).filter(Job.id == id).first()
    if not job or job.status != "PUBLISHED":
        raise HTTPException(status_code=400, detail="该岗位当前不可投递或已停止招聘")

    # Check resume belongs to user
    resume = db.query(Resume).filter(
        Resume.id == req.resume_id,
        Resume.user_id == current_user.id,
        Resume.is_deleted == False
    ).first()
    if not resume:
        raise HTTPException(status_code=400, detail="请选择有效的个人简历进行投递")

    # Check duplicate application
    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == id
    ).first()
    if existing:
        if existing.status == "WITHDRAWN":
            # Re-apply allowed if withdrawn
            existing.status = "SUBMITTED"
            existing.resume_id = resume.id
            existing.updated_at = datetime.utcnow()
            hist = ApplicationStatusHistory(
                application_id=existing.id,
                from_status="WITHDRAWN",
                to_status="SUBMITTED",
                actor_id=current_user.id,
                note="重新投递简历"
            )
            db.add(hist)
            db.commit()
            return ResponseModel(data={"application_id": existing.id, "message": "重新投递成功"})
        raise HTTPException(status_code=400, detail=f"您已投递过该岗位，当前状态为：{existing.status}")

    # Build snapshot
    snapshot = {
        "resume_id": resume.id,
        "resume_name": resume.name,
        "candidate_name": current_user.profile.name if current_user.profile else "求职者",
        "school": current_user.profile.school if current_user.profile else "",
        "major": current_user.profile.major if current_user.profile else "",
        "education": current_user.profile.education if current_user.profile else "本科",
        "educations": [{"school": e.school, "major": e.major, "degree": e.degree, "start": e.start_date, "end": e.end_date} for e in resume.educations],
        "projects": [{"name": p.name, "role": p.role, "description": p.description, "tech": p.technologies} for p in resume.projects],
        "work_experiences": [{"company": w.company, "title": w.title, "description": w.description} for w in resume.work_experiences],
        "skills": [{"name": s.skill_name, "level": s.level} for s in resume.skills]
    }

    application = Application(
        user_id=current_user.id,
        job_id=job.id,
        resume_id=resume.id,
        resume_snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        status="SUBMITTED",
        match_score=86
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Record history
    hist = ApplicationStatusHistory(
        application_id=application.id,
        from_status=None,
        to_status="SUBMITTED",
        actor_id=current_user.id,
        note="求职者主动发起简历投递"
    )
    db.add(hist)

    # Notify enterprise recruiters
    company_members = job.company.members if job.company else []
    for m in company_members:
        noti = Notification(
            user_id=m.user_id,
            type="ENTERPRISE",
            title="收到新的候选人简历投递",
            content=f"候选人【{snapshot['candidate_name']}】投递了岗位【{job.title}】",
            link=f"/enterprise/candidates/{application.id}"
        )
        db.add(noti)

    db.commit()
    if company_members:
        for m in company_members:
            manager.publish(m.user_id, {"type": "new_notification"})
    log_operation(db, current_user.id, snapshot['candidate_name'], "PERSONAL", "JOB_APPLY", "APPLICATION", application.id, f"投递岗位【{job.title}】")

    return ResponseModel(data={"application_id": application.id, "message": "投递成功！已同步至企业候选人列表"})
