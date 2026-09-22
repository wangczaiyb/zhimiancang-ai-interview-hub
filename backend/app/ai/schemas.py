from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ResumeParseSchema(BaseModel):
    education: List[Dict[str, str]] = []
    work_experience: List[Dict[str, str]] = []
    projects: List[Dict[str, Any]] = []
    skills: List[Dict[str, str]] = []
    certificates: List[str] = []
    warnings: List[str] = []

class JDParseSchema(BaseModel):
    title: str
    category: str
    city: str
    salary_min: int
    salary_max: int
    education: str
    experience: str
    type: str = "全职"
    description: str
    duties: str
    requirements: str
    bonus: str = ""
    skills: List[Dict[str, Any]] = []
    competencies: List[Dict[str, Any]] = []

class QuestionGenSchema(BaseModel):
    question: str
    skill_name: str
    stage: str
    difficulty: str
    hints: Optional[str] = None

class AnswerEvalSchema(BaseModel):
    score: float = Field(..., ge=0, le=100)
    dimensions: Dict[str, float] # professional, relevance, completeness, logic, depth, communication
    evidence: List[str]
    weaknesses: List[str]
    missing_knowledge: List[str]
    suggestions: List[str]
    next_action: str # FOLLOW_UP, DEEP, BASIC, CHANGE_TOPIC, FINISH

class ReportGenSchema(BaseModel):
    total_score: float
    performance_level: str
    dimension_scores: Dict[str, float] # 专业基础, 项目经验, 系统设计, 沟通表达, 综合素质
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    summary: str

class LearningPlanSchema(BaseModel):
    tasks: List[Dict[str, Any]]

class MatchExplainerSchema(BaseModel):
    match_score: int
    advantage_skills: List[str]
    missing_skills: List[str]
    explanation: str

class ResumeOptimizeSchema(BaseModel):
    completeness_score: int = Field(..., ge=0, le=100)
    strengths: List[str]
    improvements: List[str]
    suggested_modifications: List[Dict[str, Any]]
    keyword_enrichment: List[str]

class ResumeRewriteSchema(BaseModel):
    """AI 一键优化：改写后的结构化简历内容"""
    projects: List[Dict[str, Any]] = []
    skills: List[Dict[str, Any]] = []
    work_experience: List[Dict[str, Any]] = []
    changes: List[str] = []
