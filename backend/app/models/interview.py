from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    jd_text = Column(Text, nullable=True)  # 本次面试使用的岗位 JD 文本快照
    type = Column(String(50), default="PERSONAL_TRAINING", nullable=False) # PERSONAL_TRAINING, ENTERPRISE_RECRUITMENT
    mode = Column(String(50), default="COMPREHENSIVE", nullable=False)     # COMPREHENSIVE, TECHNICAL, PROJECT_DEEP_DIVE, BEHAVIORAL, STRESS
    difficulty = Column(String(50), default="MEDIUM", nullable=False)      # EASY, MEDIUM, HARD
    status = Column(String(50), default="CREATED", nullable=False)         # CREATED, READY, IN_PROGRESS, PAUSED, COMPLETED, CANCELLED, EXPIRED
    current_question_seq = Column(Integer, default=1, nullable=False)
    total_questions = Column(Integer, default=5, nullable=False)
    privacy_scope = Column(String(50), default="PRIVATE", nullable=False)  # PRIVATE, COMPANY_AUTHORIZED
    duration_minutes = Column(Integer, default=30, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="interviews")
    job = relationship("Job")
    application = relationship("Application", back_populates="interviews")
    plan = relationship("InterviewPlan", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")
    report = relationship("InterviewReport", back_populates="interview", uselist=False, cascade="all, delete-orphan")
    recruiter_evaluation = relationship("RecruiterEvaluation", back_populates="interview", uselist=False, cascade="all, delete-orphan")

class InterviewPlan(Base):
    __tablename__ = "interview_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    stages_json = Column(Text, nullable=False)
    total_questions = Column(Integer, default=5, nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)

    interview = relationship("Interview", back_populates="plan")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    parent_question_id = Column(Integer, nullable=True)
    seq = Column(Integer, nullable=False)
    stage = Column(String(50), default="专业基础", nullable=False)
    skill_id = Column(Integer, nullable=True)
    skill_name = Column(String(100), default="Java", nullable=False)
    text = Column(Text, nullable=False)
    difficulty = Column(String(50), default="MEDIUM", nullable=False)
    source = Column(String(50), default="AI_GENERATED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), unique=True, nullable=False)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    audio_file_id = Column(String(100), nullable=True)
    duration_sec = Column(Integer, default=45, nullable=False)
    speaking_rate = Column(Integer, default=160, nullable=False)  # words per min
    filler_count = Column(Integer, default=2, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    question = relationship("InterviewQuestion", back_populates="answer")
    evaluation = relationship("AnswerEvaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")

class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    answer_id = Column(Integer, ForeignKey("interview_answers.id"), unique=True, nullable=False)
    interview_id = Column(Integer, nullable=False)
    total_score = Column(Float, nullable=False)
    # Rubric: 准确度(30%), 相关性(20%), 完整性(15%), 逻辑结构(15%), 实践深度(15%), 表达能力(5%)
    dimensions_json = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=False)
    weaknesses_json = Column(Text, nullable=False)
    missing_knowledge_json = Column(Text, nullable=False)
    suggestions_json = Column(Text, nullable=False)
    next_action = Column(String(50), default="NEXT", nullable=False) # FOLLOW_UP, DEEP, BASIC, CHANGE_TOPIC, FINISH
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    answer = relationship("InterviewAnswer", back_populates="evaluation")

class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_score = Column(Float, default=82.0, nullable=False)
    performance_level = Column(String(50), default="表现良好", nullable=False)
    # 5 radar dimensions: 专业基础, 项目经验, 系统设计, 沟通表达, 综合素质
    dimension_scores_json = Column(Text, nullable=False)
    strengths_json = Column(Text, nullable=False)
    weaknesses_json = Column(Text, nullable=False)
    suggestions_json = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interview = relationship("Interview", back_populates="report")

class InterviewInvitation(Base):
    __tablename__ = "interview_invitations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interview_id = Column(Integer, nullable=True)
    note = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, ACCEPTED, DECLINED, EXPIRED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RecruiterEvaluation(Base):
    __tablename__ = "recruiter_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=True)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evaluator_name = Column(String(100), default="主面试官", nullable=False)
    # technical, project, problem_solving, communication, job_fit, total_score
    dimensions_json = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    recommendation = Column(String(50), default="PASS", nullable=False) # PASS, REVIEW, REJECT
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    interview = relationship("Interview", back_populates="recruiter_evaluation")
