from app.core.database import Base
from app.models.user import User, Role, Permission, RolePermission, UserRole
from app.models.profile import PersonalProfile, CareerPreference, Competency, UserCompetency, CompetencyHistory
from app.models.company import Company, Department, CompanyMember, CompanyVerification
from app.models.job import Job, Skill, JobSkill, JobCompetency, JobFavorite
from app.models.resume import (
    Resume, ResumeEducation, ResumeProject, ResumeWorkExperience,
    ResumeSkill, ResumeAIAnalysis
)
from app.models.application import (
    Application, ApplicationStatusHistory, CandidatePipelineRecord, CandidateTag
)
from app.models.interview import (
    Interview, InterviewPlan, InterviewQuestion, InterviewAnswer,
    AnswerEvaluation, InterviewReport, InterviewInvitation, RecruiterEvaluation
)
from app.models.learning import LearningPlan, LearningTask
from app.models.question import QuestionBank
from app.models.system import (
    Notification, FileRecord, ConsentRecord, Complaint, OperationLog, AICallLog
)

__all__ = [
    "Base", "User", "Role", "Permission", "RolePermission", "UserRole",
    "PersonalProfile", "CareerPreference", "Competency", "UserCompetency", "CompetencyHistory",
    "Company", "Department", "CompanyMember", "CompanyVerification",
    "Job", "Skill", "JobSkill", "JobCompetency", "JobFavorite",
    "Resume", "ResumeEducation", "ResumeProject", "ResumeWorkExperience",
    "ResumeSkill", "ResumeAIAnalysis",
    "Application", "ApplicationStatusHistory", "CandidatePipelineRecord", "CandidateTag",
    "Interview", "InterviewPlan", "InterviewQuestion", "InterviewAnswer",
    "AnswerEvaluation", "InterviewReport", "InterviewInvitation", "RecruiterEvaluation",
    "LearningPlan", "LearningTask",
    "Notification", "FileRecord", "ConsentRecord", "Complaint", "OperationLog", "AICallLog"
]
