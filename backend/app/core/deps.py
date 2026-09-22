from typing import Generator, Optional, List
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.company import CompanyMember
from app.models.system import OperationLog, UserSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录凭证无效或已过期，请重新登录"
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录凭证异常"
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用或处于限制状态"
        )

    # 校验会话是否被强制下线（仅对携带 jti 的新令牌生效，向后兼容旧令牌）
    jti = payload.get("jti")
    if jti:
        session = db.query(UserSession).filter(UserSession.jti == jti).first()
        if session and session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="会话已被强制下线，请重新登录"
            )
        if session:
            session.last_active_at = datetime.utcnow()
            db.commit()

    return user

def require_auth(current_user: Optional[User] = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录后操作"
        )
    return current_user

def require_roles(allowed_roles: List[str]):
    def role_checker(
        current_user: User = Depends(require_auth),
        db: Session = Depends(get_db)
    ) -> User:
        user_roles = [r.role_code for r in current_user.roles]
        # Super admin always has bypass
        if "SUPER_ADMIN" in user_roles:
            return current_user
        # Check if any allowed role matches
        if any(role in allowed_roles for role in user_roles):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，您无权访问该资源或执行此操作"
        )
    return role_checker

def get_enterprise_member(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> CompanyMember:
    member = db.query(CompanyMember).filter(
        CompanyMember.user_id == current_user.id,
        CompanyMember.status == "ACTIVE"
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您未加入任何企业或企业账号已被停用"
        )
    return member

def log_operation(
    db: Session,
    actor_id: Optional[int],
    actor_name: str,
    role: str,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    detail: Optional[str] = None
):
    log = OperationLog(
        actor_id=actor_id,
        actor_name=actor_name,
        role=role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail
    )
    db.add(log)
    try:
        db.commit()
    except Exception:
        db.rollback()
