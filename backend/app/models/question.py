from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text

from app.core.database import Base


class QuestionBank(Base):
    """结构化面试题库。

    组卷引擎从本表按「题型配比 + 岗位技能匹配 + 难度就近」抽题，
    抽题结果会固化到 InterviewQuestion / InterviewPlan.paper_json，
    因此题库后续被编辑也不会影响历史面试卷面的可复现性。
    """

    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 适用岗位大类；"通用" 表示跨岗位通用题
    job_category = Column(String(50), default="通用", nullable=False, index=True)
    # PROFESSIONAL 专业题 / GENERAL 通用题 / STRESS 压力题
    question_type = Column(String(20), default="PROFESSIONAL", nullable=False, index=True)
    # 考察技能（Java / Redis / MySQL / Vue3 ...），通用题为"综合素养"
    skill_name = Column(String(100), default="综合素养", nullable=False, index=True)
    # 面试阶段（专业基础 / 深度探究 / 项目深挖 / 系统设计 / 综合素养 / 压力应对）
    stage = Column(String(50), default="专业基础", nullable=False)
    difficulty = Column(String(20), default="MEDIUM", nullable=False)  # EASY, MEDIUM, HARD

    text = Column(Text, nullable=False)
    # 参考答案要点（JSON 字符串数组），用于逐题复盘对照
    reference_points_json = Column(Text, nullable=True)
    hints = Column(String(255), nullable=True)  # 临场答题提示
    # 逐题建议限时（秒），用于面试间倒计时
    time_limit_sec = Column(Integer, default=180, nullable=False)

    source = Column(String(30), default="SEED", nullable=False)  # SEED, MANUAL, AI_GENERATED
    enabled = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)  # 抽题时用于均衡出题

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
