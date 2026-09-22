from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), default="SYSTEM", nullable=False) # ENTERPRISE, INVITATION, APPLICATION_PROGRESS, SYSTEM, LEARNING, SECURITY
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    interview = Column(Boolean, default=True, nullable=False)    # 面试邀请通知
    application = Column(Boolean, default=True, nullable=False)  # 申请状态变更
    report = Column(Boolean, default=True, nullable=False)       # AI 评测报告生成
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    device = Column(String(100), default="浏览器", nullable=False)
    ip = Column(String(50), default="127.0.0.1", nullable=False)
    location = Column(String(50), default="局域网", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bucket = Column(String(100), default="default", nullable=False)
    object_key = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(255), nullable=False)
    mime = Column(String(100), default="application/octet-stream", nullable=False)
    size = Column(Integer, default=0, nullable=False)
    visibility = Column(String(50), default="PRIVATE", nullable=False) # PRIVATE, PUBLIC
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_type = Column(String(50), nullable=False) # COMPANY, RECRUITER
    target_id = Column(Integer, nullable=False)
    scope = Column(String(100), default="RESUME_AND_INTERVIEW", nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_type = Column(String(50), nullable=False) # JOB, COMPANY, INTERVIEW
    target_id = Column(Integer, nullable=False)
    category = Column(String(100), default="虚假招聘", nullable=False) # 虚假招聘, 违规收费, 虚假公司, 骚扰信息
    description = Column(Text, nullable=False)
    evidence_url = Column(String(255), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, PROCESSING, RESOLVED, REJECTED
    handler_id = Column(Integer, nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(100), default="系统", nullable=False)
    role = Column(String(50), default="USER", nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    ip = Column(String(50), default="127.0.0.1", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AICallLog(Base):
    __tablename__ = "ai_call_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    business_type = Column(String(100), nullable=False) # RESUME_PARSE, QUESTION_GEN, EVALUATE, REPORT_GEN, JD_PARSE
    model = Column(String(50), default="mock-ai", nullable=False)
    prompt_version = Column(String(50), default="v1.0", nullable=False)
    tokens_in = Column(Integer, default=0, nullable=False)
    tokens_out = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=150, nullable=False)
    status = Column(String(50), default="SUCCESS", nullable=False)
    error_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
