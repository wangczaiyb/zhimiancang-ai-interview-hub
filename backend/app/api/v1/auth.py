import logging
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.deps import get_current_user, require_auth, log_operation
from app.models.user import User, Role, UserRole
from app.models.profile import PersonalProfile, CareerPreference, UserCompetency
from app.models.company import Company, CompanyMember
from app.models.system import UserSession
from app.schemas.auth import (
    LoginRequest, TokenResponse, RegisterPersonalRequest,
    RegisterEnterpriseRequest, OnboardingRequest, UserInfoOut,
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
)
from app.schemas.common import ResponseModel

logger = logging.getLogger("auth")
router = APIRouter(tags=["认证鉴权"])

RESET_TOKEN_EXPIRE_MINUTES = 30


def issue_token_with_session(db: Session, user: User, role_codes, company_id=None) -> str:
    """生成带 jti 的访问令牌并落库会话记录，供强制下线校验使用。"""
    jti = uuid.uuid4().hex
    token = create_access_token(
        subject=user.id,
        extra_claims={
            "account_type": user.account_type,
            "role_codes": role_codes,
            "company_id": company_id,
            "jti": jti
        }
    )
    db.add(UserSession(user_id=user.id, jti=jti, device="浏览器", ip="127.0.0.1"))
    return token


def _send_reset_email(email: str, reset_token: str) -> bool:
    """发送密码重置邮件；未配置 SMTP 时回退为记录日志并返回 False。"""
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_FROM):
        logger.warning(f"[找回密码] SMTP 未配置，跳过邮件发送。邮箱={email} reset_token={reset_token}")
        return False

    subject = "【智面舱】重置您的登录密码"
    reset_link = f"http://localhost:5173/forgot-password?token={reset_token}"
    body = f"您好，\n\n请点击以下链接重置密码（{RESET_TOKEN_EXPIRE_MINUTES} 分钟内有效）：\n{reset_link}\n\n若非本人操作，请忽略本邮件。"
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = settings.SMTP_FROM
        msg["To"] = email
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [email], msg.as_string())
        return True
    except Exception as e:
        logger.error(f"发送重置邮件失败: {e}")
        return False

@router.post("/auth/login", response_model=ResponseModel[TokenResponse])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # Support login by email or phone
    user = db.query(User).filter(
        (User.email == req.account) | (User.phone == req.account)
    ).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账号或密码错误"
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系客服处理"
        )

    user.last_login_at = datetime.utcnow()
    db.commit()

    role_codes = [r.role_code for r in user.roles]
    name = user.email.split("@")[0]
    avatar_url = None
    company_id = None

    if user.profile:
        name = user.profile.name or name
        avatar_url = user.profile.avatar_url

    membership = db.query(CompanyMember).filter(
        CompanyMember.user_id == user.id,
        CompanyMember.status == "ACTIVE"
    ).first()
    if membership:
        company_id = membership.company_id

    access_token = issue_token_with_session(db, user, role_codes, company_id)
    refresh_token = create_refresh_token(subject=user.id)

    db.commit()

    log_operation(db, user.id, name, user.account_type, "USER_LOGIN", "USER", user.id, "用户成功登录")

    return ResponseModel(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        account_type=user.account_type,
        role_codes=role_codes,
        user_id=user.id,
        name=name,
        avatar_url=avatar_url,
        company_id=company_id
    ))

@router.post("/auth/refresh", response_model=ResponseModel[dict])
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=401, detail="用户状态异常")

    role_codes = [r.role_code for r in user.roles]
    new_access = issue_token_with_session(db, user, role_codes, None)
    db.commit()
    return ResponseModel(data={"access_token": new_access})

@router.post("/auth/logout", response_model=ResponseModel[dict])
def logout(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    log_operation(db, current_user.id, current_user.email, current_user.account_type, "USER_LOGOUT", "USER", current_user.id, "用户退出登录")
    return ResponseModel(data={"message": "登出成功"})

@router.get("/auth/me", response_model=ResponseModel[UserInfoOut])
def get_me(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    role_codes = [r.role_code for r in current_user.roles]
    name = current_user.email.split("@")[0]
    avatar_url = None
    profile_type = None
    target_job_title = None

    if current_user.profile:
        name = current_user.profile.name
        avatar_url = current_user.profile.avatar_url
        profile_type = current_user.profile.profile_type

    if current_user.career_preference:
        target_job_title = current_user.career_preference.target_job_title

    company_id = None
    company_name = None
    membership = db.query(CompanyMember).filter(
        CompanyMember.user_id == current_user.id,
        CompanyMember.status == "ACTIVE"
    ).first()
    if membership:
        company_id = membership.company_id
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            company_name = company.name

    return ResponseModel(data=UserInfoOut(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        account_type=current_user.account_type,
        status=current_user.status,
        roles=role_codes,
        name=name,
        avatar_url=avatar_url,
        company_id=company_id,
        company_name=company_name,
        profile_type=profile_type,
        target_job_title=target_job_title
    ))

@router.post("/auth/change-password", response_model=ResponseModel[dict])
def change_password(req: ChangePasswordRequest, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于 6 位")

    current_user.password_hash = get_password_hash(req.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    log_operation(db, current_user.id, current_user.email, current_user.account_type, "CHANGE_PASSWORD", "USER", current_user.id, "用户修改登录密码")
    return ResponseModel(data={"message": "密码修改成功，请使用新密码重新登录"})

@router.post("/auth/forgot-password", response_model=ResponseModel[dict])
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # 防用户枚举：无论邮箱是否存在均返回统一提示
    user = db.query(User).filter(User.email == req.email).first()
    dev_reset_token: str = None
    if user:
        reset_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
            extra_claims={"type": "reset", "purpose": "reset_password"}
        )
        sent = _send_reset_email(req.email, reset_token)
        if not sent:
            # 开发/未配置 SMTP 时，将令牌直接返回以便本地联调
            dev_reset_token = reset_token

    data = {"message": "若该邮箱已注册，重置链接已发送，请查收（30 分钟内有效）"}
    if dev_reset_token:
        data["dev_reset_token"] = dev_reset_token
    return ResponseModel(data=data)

@router.post("/auth/reset-password", response_model=ResponseModel[dict])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.token)
    if not payload or payload.get("type") != "reset" or payload.get("purpose") != "reset_password":
        raise HTTPException(status_code=400, detail="重置链接无效或已过期")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="重置链接无效或已过期")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="用户不存在")

    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于 6 位")

    user.password_hash = get_password_hash(req.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()

    log_operation(db, user.id, user.email, user.account_type, "RESET_PASSWORD", "USER", user.id, "用户通过邮件重置密码")
    return ResponseModel(data={"message": "密码已重置，请使用新密码登录"})

@router.post("/auth/register/personal", response_model=ResponseModel[TokenResponse])
def register_personal(req: RegisterPersonalRequest, db: Session = Depends(get_db)):
    if not req.agreed:
        raise HTTPException(status_code=400, detail="请阅读并勾选用户协议与隐私条款")
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于 6 位")

    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册，请直接登录")

    new_user = User(
        email=req.email,
        phone=req.phone,
        password_hash=get_password_hash(req.password),
        account_type="PERSONAL",
        status="ACTIVE"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Assign role
    user_role = UserRole(user_id=new_user.id, role_code="PERSONAL_USER")
    db.add(user_role)

    # Initialize empty profile & preference
    initial_name = (req.name or "").strip() or req.email.split("@")[0]
    profile = PersonalProfile(
        user_id=new_user.id,
        profile_type="STUDENT",
        name=initial_name,
        education="本科",
        school="待填写学校",
        major="计算机",
        work_years=0
    )
    pref = CareerPreference(
        user_id=new_user.id,
        target_job_title="Java后端开发工程师",
        target_cities="北京,上海,深圳",
        salary_min=15,
        salary_max=25
    )
    db.add(profile)
    db.add(pref)
    db.commit()

    access_token = issue_token_with_session(db, new_user, ["PERSONAL_USER"], None)
    refresh_token = create_refresh_token(subject=new_user.id)
    db.commit()

    log_operation(db, new_user.id, initial_name, "PERSONAL", "USER_REGISTER", "USER", new_user.id, "个人用户完成注册")

    return ResponseModel(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        account_type="PERSONAL",
        role_codes=["PERSONAL_USER"],
        user_id=new_user.id,
        name=initial_name
    ))

@router.post("/auth/register/enterprise", response_model=ResponseModel[TokenResponse])
def register_enterprise(req: RegisterEnterpriseRequest, db: Session = Depends(get_db)):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于 6 位")

    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已存在，请更换或直接登录")

    existing_company = db.query(Company).filter(Company.name == req.company_name).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="该企业名称已存在，若为误占请联系平台进行申诉认证")

    new_user = User(
        email=req.email,
        phone=req.phone,
        password_hash=get_password_hash(req.password),
        account_type="ENTERPRISE",
        status="ACTIVE"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create company (Default UNVERIFIED per spec)
    company = Company(
        name=req.company_name,
        industry=req.industry,
        size="50-150人",
        city=req.city,
        intro="企业资料正在完善中...",
        status="UNVERIFIED"
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    # Assign ENTERPRISE_OWNER role
    user_role = UserRole(user_id=new_user.id, role_code="ENTERPRISE_OWNER", company_id=company.id)
    db.add(user_role)

    # Add as OWNER member
    member = CompanyMember(
        company_id=company.id,
        user_id=new_user.id,
        role_code="OWNER",
        status="ACTIVE"
    )
    db.add(member)
    db.commit()

    access_token = issue_token_with_session(db, new_user, ["ENTERPRISE_OWNER"], company.id)
    refresh_token = create_refresh_token(subject=new_user.id)
    db.commit()

    log_operation(db, new_user.id, req.contact_name, "ENTERPRISE", "ENTERPRISE_REGISTER", "COMPANY", company.id, f"企业【{company.name}】注册成功")

    return ResponseModel(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        account_type="ENTERPRISE",
        role_codes=["ENTERPRISE_OWNER"],
        user_id=new_user.id,
        name=req.contact_name,
        company_id=company.id
    ))

@router.put("/personal/onboarding", response_model=ResponseModel[dict])
def update_onboarding(req: OnboardingRequest, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    profile = current_user.profile
    if not profile:
        profile = PersonalProfile(user_id=current_user.id, name=req.name)
        db.add(profile)

    profile.profile_type = req.profile_type
    profile.name = req.name
    profile.gender = req.gender
    profile.education = req.education
    profile.school = req.school
    profile.major = req.major
    profile.graduation_year = req.graduation_year

    pref = current_user.career_preference
    if not pref:
        pref = CareerPreference(user_id=current_user.id)
        db.add(pref)

    pref.target_job_title = req.target_job_title
    pref.target_cities = req.target_cities
    pref.salary_min = req.salary_min
    pref.salary_max = req.salary_max
    pref.job_status = req.job_status

    db.commit()
    log_operation(db, current_user.id, req.name, "PERSONAL", "UPDATE_ONBOARDING", "PROFILE", profile.id, "完成首次求职引导设置")
    return ResponseModel(data={"message": "引导完成，档案与偏好已初始化"})
