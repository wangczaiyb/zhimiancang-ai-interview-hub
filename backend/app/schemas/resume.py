from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class EducationItem(BaseModel):
    school: str
    major: str
    degree: str = "本科"
    start_date: str
    end_date: str

class ProjectItem(BaseModel):
    name: str
    role: str = "核心开发"
    description: str
    technologies: str
    start_date: str
    end_date: str

class WorkExperienceItem(BaseModel):
    company: str
    title: str
    description: str
    start_date: str
    end_date: str

class SkillItem(BaseModel):
    skill_name: str
    level: str = "熟练"
    evidence: Optional[str] = None

class ResumeCreate(BaseModel):
    name: str = "我的个人简历"
    target_job_title: str = "Java后端开发工程师"
    is_default: bool = False
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    educations: List[EducationItem] = []
    projects: List[ProjectItem] = []
    work_experiences: List[WorkExperienceItem] = []
    skills: List[SkillItem] = []

class ResumeUpdate(ResumeCreate):
    pass

class ResumeOut(BaseModel):
    id: int
    user_id: int
    name: str
    is_default: bool
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    status: str
    target_job_id: Optional[int] = None
    target_job_title: str
    completeness: int
    created_at: datetime
    updated_at: datetime
    educations: List[EducationItem] = []
    projects: List[ProjectItem] = []
    work_experiences: List[WorkExperienceItem] = []
    skills: List[SkillItem] = []

class ResumeAIParseResult(BaseModel):
    educations: List[EducationItem]
    projects: List[ProjectItem]
    work_experiences: List[WorkExperienceItem]
    skills: List[SkillItem]
    warnings: List[str] = []

class ResumeAIOptimizeResult(BaseModel):
    completeness_score: int
    strengths: List[str]
    improvements: List[str]
    suggested_modifications: List[dict]
    keyword_enrichment: List[str]

class ResumeOptimizeApplyResult(BaseModel):
    resume: ResumeOut
    changes: List[str] = []
