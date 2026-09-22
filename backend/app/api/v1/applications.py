from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_auth, log_operation
from app.models.user import User
from app.models.application import Application, ApplicationStatusHistory, CandidateTag
from app.models.interview import InterviewInvitation, Interview
from app.models.system import Notification
from app.websocket.notification_ws import manager
from app.schemas.common import ResponseModel
from app.schemas.application import (
    ApplicationOut, ApplicationWithdrawRequest, StatusHistoryItem
)

router = APIRouter(tags=["我的求职与申请"])

def build_app_out(app: Application) -> ApplicationOut:
    history_items = [
        StatusHistoryItem(
            id=h.id,
            from_status=h.from_status,
            to_status=h.to_status,
            note=h.note,
            created_at=h.created_at
        )
        for h in app.status_history
    ]
    tag_list = [t.tag for t in app.tags]

    invitation = bool(app.interviews and any(i.type == "ENTERPRISE_RECRUITMENT" for i in app.interviews))
    invitation_status = None
    if app.interviews:
        ent_interview = next((i for i in app.interviews if i.type == "ENTERPRISE_RECRUITMENT"), None)
        if ent_interview:
            invitation_status = ent_interview.status

    return ApplicationOut(
        id=app.id,
        user_id=app.user_id,
        candidate_name=app.user.profile.name if app.user and app.user.profile else "求职者",
        candidate_avatar=app.user.profile.avatar_url if app.user and app.user.profile else None,
        candidate_school=app.user.profile.school if app.user and app.user.profile else None,
        candidate_education=app.user.profile.education if app.user and app.user.profile else None,
        candidate_major=app.user.profile.major if app.user and app.user.profile else None,
        job_id=app.job_id,
        job_title=app.job.title if app.job else "岗位已下线",
        company_id=app.job.company_id if app.job else None,
        company_name=app.job.company.name if app.job and app.job.company else "未知企业",
        company_logo=app.job.company.logo_url if app.job and app.job.company else None,
        resume_id=app.resume_id,
        status=app.status,
        match_score=app.match_score,
        reject_reason=app.reject_reason,
        withdraw_reason=app.withdraw_reason,
        assigned_recruiter_id=app.assigned_recruiter_id,
        is_in_talent_pool=app.is_in_talent_pool,
        tags=tag_list,
        has_interview_invitation=invitation,
        invitation_status=invitation_status,
        created_at=app.created_at,
        updated_at=app.updated_at,
        status_history=history_items
    )

@router.get("/applications", response_model=ResponseModel[List[ApplicationOut]])
def list_my_applications(
    status: Optional[str] = None,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    query = db.query(Application).filter(Application.user_id == current_user.id)
    if status and status != "全部":
        query = query.filter(Application.status == status)

    apps = query.order_by(Application.id.desc()).all()
    return ResponseModel(data=[build_app_out(a) for a in apps])

@router.get("/applications/{id}", response_model=ResponseModel[ApplicationOut])
def get_application_detail(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="求职申请记录不存在")

    # SEC-01 & SEC-02 check: must be owner or company member with access
    if app.user_id != current_user.id:
        user_roles = [r.role_code for r in current_user.roles]
        is_admin = "PLATFORM_ADMIN" in user_roles or "SUPER_ADMIN" in user_roles
        is_company = any(r.company_id == app.job.company_id for r in current_user.roles if r.company_id)
        if not (is_admin or is_company):
            raise HTTPException(status_code=403, detail="无权查看该投递记录")

    return ResponseModel(data=build_app_out(app))

@router.post("/applications/{id}/withdraw", response_model=ResponseModel[dict])
def withdraw_application(
    id: int,
    req: ApplicationWithdrawRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="投递记录不存在")

    if app.status == "HIRED":
        raise HTTPException(status_code=400, detail="已录用状态不可直接撤回，请联系企业 HR 协调")
    if app.status in ["REJECTED", "WITHDRAWN"]:
        raise HTTPException(status_code=400, detail="当前状态不可撤回")

    old_status = app.status
    app.status = "WITHDRAWN"
    app.withdraw_reason = req.reason
    app.updated_at = datetime.utcnow()

    # Record history
    hist = ApplicationStatusHistory(
        application_id=app.id,
        from_status=old_status,
        to_status="WITHDRAWN",
        actor_id=current_user.id,
        note=f"求职者主动撤回：{req.reason}"
    )
    db.add(hist)

    # Notify enterprise
    if app.job and app.job.company:
        for m in app.job.company.members:
            noti = Notification(
                user_id=m.user_id,
                type="APPLICATION_PROGRESS",
                title="候选人撤回了求职投递",
                content=f"候选人撤回了岗位【{app.job.title}】的申请，原因：{req.reason}",
                link=f"/enterprise/candidates/{app.id}"
            )
            db.add(noti)

    db.commit()
    if app.job and app.job.company:
        for m in app.job.company.members:
            manager.publish(m.user_id, {"type": "new_notification"})
    log_operation(db, current_user.id, current_user.email, "PERSONAL", "WITHDRAW_APPLICATION", "APPLICATION", app.id, f"撤回岗位【{app.job.title if app.job else ''}】申请")

    return ResponseModel(data={"message": "投递已成功撤回"})

@router.post("/interview-invitations/{id}/accept", response_model=ResponseModel[dict])
def accept_invitation(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    inv = db.query(InterviewInvitation).filter(InterviewInvitation.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="面试邀请不存在")

    app = db.query(Application).filter(Application.id == inv.application_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=403, detail="无权操作此面试邀请")

    inv.status = "ACCEPTED"

    # Create interview session if not existing
    if not inv.interview_id:
        interview = Interview(
            user_id=current_user.id,
            company_id=inv.company_id,
            job_id=app.job_id,
            application_id=app.id,
            type="ENTERPRISE_RECRUITMENT",
            mode="TECHNICAL",
            difficulty="MEDIUM",
            status="READY",
            total_questions=5,
            duration_minutes=30,
            privacy_scope="COMPANY_AUTHORIZED"
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        inv.interview_id = interview.id

    app.status = "ENTERPRISE_INTERVIEW"
    hist = ApplicationStatusHistory(
        application_id=app.id,
        from_status="AI_INTERVIEW_PENDING",
        to_status="ENTERPRISE_INTERVIEW",
        actor_id=current_user.id,
        note="求职者接受企业面试邀请"
    )
    db.add(hist)
    db.commit()

    return ResponseModel(data={
        "message": "已接受邀请",
        "interview_id": inv.interview_id,
        "session_url": f"/personal/interviews/{inv.interview_id}/session"
    })

@router.post("/interview-invitations/{id}/decline", response_model=ResponseModel[dict])
def decline_invitation(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    inv = db.query(InterviewInvitation).filter(InterviewInvitation.id == id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="面试邀请不存在")

    app = db.query(Application).filter(Application.id == inv.application_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=403, detail="无权操作此面试邀请")

    inv.status = "DECLINED"
    db.commit()

    return ResponseModel(data={"message": "已婉拒面试邀请"})
