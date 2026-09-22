from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class InterviewCreate(BaseModel):
    job_id: Optional[int] = None
    resume_id: Optional[int] = None
    application_id: Optional[int] = None
    type: str = "PERSONAL_TRAINING" # PERSONAL_TRAINING, ENTERPRISE_RECRUITMENT
    mode: str = "COMPREHENSIVE"     # COMPREHENSIVE, TECHNICAL, PROJECT_DEEP_DIVE, BEHAVIORAL, STRESS
    difficulty: str = "MEDIUM"      # EASY, MEDIUM, HARD
    total_questions: int = 5
    duration_minutes: int = 30
    jd_text: Optional[str] = None   # 用户输入的/自动带出的岗位 JD 文本
    use_question_bank: bool = True  # 是否优先从结构化题库组卷（关闭则全部 AI 实时生成）
    selected_bank_ids: Optional[List[int]] = None  # 按已预览确认的考卷出题（题库题目 ID，按顺序）

class InterviewQuestionOut(BaseModel):
    id: int
    seq: int
    stage: str
    question_type: str = "PROFESSIONAL"  # PROFESSIONAL / GENERAL / STRESS
    skill_name: str
    text: str
    difficulty: str
    hints: Optional[str] = None
    time_limit_sec: int = 180
    source: str = "QUESTION_BANK"        # QUESTION_BANK / AI_GENERATED
    reference_points: List[str] = []     # 参考答案要点（仅复盘阶段下发）
    reveal_reference: bool = False       # 是否允许展示参考答案（作答中为 False）
    user_answer: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None

class PaperPreviewItem(BaseModel):
    seq: int
    bank_id: Optional[int] = None      # 题库题目 ID，回传可按此考卷开考
    question_type: str
    skill_name: str
    stage: str
    difficulty: str
    text: str
    time_limit_sec: int
    source: str

class PaperPreviewOut(BaseModel):
    mode: str
    total_questions: int
    ratio: Dict[str, int]          # 题型配比（专业/通用/压力）
    allocated: Dict[str, int]      # 分配到的各题型题数
    from_bank: int                 # 题库命中题数
    missing_for_ai: Dict[str, int] = {}  # 题库缺口（将由 AI 补足）
    matched_category: str
    job_skills: List[str] = []
    bank_available: int
    questions: List[PaperPreviewItem] = []

class InterviewOut(BaseModel):
    id: int
    user_id: int
    company_id: Optional[int] = None
    job_id: Optional[int] = None
    job_title: Optional[str] = None
    application_id: Optional[int] = None
    type: str
    mode: str
    difficulty: str
    status: str
    current_question_seq: int
    total_questions: int
    duration_minutes: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    questions: List[InterviewQuestionOut] = []
    current_question: Optional[InterviewQuestionOut] = None

class InterviewAnswerRequest(BaseModel):
    text: str
    duration_sec: int = 40
    speaking_rate: int = 160
    filler_count: int = 2

class AnswerEvaluationOut(BaseModel):
    answer_id: int
    total_score: float
    dimensions: Dict[str, float]
    evidence: List[str]
    weaknesses: List[str]
    missing_knowledge: List[str]
    suggestions: List[str]
    next_action: str  # FOLLOW_UP, DEEP, BASIC, CHANGE_TOPIC, FINISH
    next_question: Optional[InterviewQuestionOut] = None

class InterviewReportOut(BaseModel):
    id: int
    interview_id: int
    user_id: int
    job_title: Optional[str] = "Java后端开发工程师"
    interview_type: Optional[str] = "AI 全真模拟与能力复盘"
    duration_minutes: Optional[int] = 25
    total_score: float
    performance_level: str
    dimension_scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    summary: str
    status: str
    created_at: datetime
    questions_analysis: List[Dict[str, Any]] = []

class InterviewInvitationCreate(BaseModel):
    application_id: int
    interview_id: Optional[int] = None
    note: Optional[str] = None
    days_valid: int = 7

class RecruiterEvaluationCreate(BaseModel):
    application_id: int
    interview_id: Optional[int] = None
    technical_score: float = 85.0
    project_score: float = 80.0
    problem_solving_score: float = 85.0
    communication_score: float = 90.0
    job_fit_score: float = 85.0
    summary: str
    recommendation: str = "PASS" # PASS, REVIEW, REJECT
