from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_job_id = Column(Integer, nullable=True)
    target_job_title = Column(String(100), default="Java后端开发工程师", nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tasks = relationship("LearningTask", back_populates="plan", cascade="all, delete-orphan")

class LearningTask(Base):
    __tablename__ = "learning_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    competency_name = Column(String(100), default="Redis", nullable=False)
    stage = Column(String(100), default="第一阶段 · 基础夯实", nullable=False)  # 分阶段学习路线
    priority = Column(String(50), default="HIGH", nullable=False) # HIGH, MEDIUM, LOW
    status = Column(String(50), default="TODO", nullable=False)   # TODO, COMPLETED, SKIPPED
    progress = Column(Integer, default=0, nullable=False)         # 0-100%
    reason = Column(String(255), nullable=True)
    action_type = Column(String(50), default="INTERVIEW_PRACTICE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    plan = relationship("LearningPlan", back_populates="tasks")
