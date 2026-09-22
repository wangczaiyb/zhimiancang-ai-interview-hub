import json
import os
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.deps import require_auth, log_operation
from app.models.user import User
from app.models.resume import (
    Resume, ResumeEducation, ResumeProject, ResumeWorkExperience,
    ResumeSkill, ResumeAIAnalysis
)
from app.models.application import Application
from app.schemas.common import ResponseModel
from app.schemas.resume import (
    ResumeCreate, ResumeUpdate, ResumeOut, EducationItem, ProjectItem,
    WorkExperienceItem, SkillItem, ResumeAIParseResult, ResumeAIOptimizeResult,
    ResumeOptimizeApplyResult
)
from app.ai.provider import ai_provider

router = APIRouter(tags=["简历中心"])

def extract_file_text(file_url: str) -> str:
    """从已上传的简历文件中抽取纯文本，供 AI 解析/诊断使用。

    支持 PDF(pypdf) 与 DOCX(python-docx)；未安装依赖或抽取失败时返回空串，
    由调用方回退到结构化字段拼装的文本。
    """
    if not file_url:
        return ""
    rel = file_url.replace("/uploads/", "", 1).lstrip("/")
    path = os.path.join(settings.UPLOAD_DIR, rel)
    if not os.path.exists(path):
        return ""

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(path)
            return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
        if ext in (".docx", ".doc"):
            import docx
            document = docx.Document(path)
            return "\n".join(p.text for p in document.paragraphs).strip()
    except Exception:
        return ""
    return ""

def build_resume_text(resume: Resume) -> str:
    """将结构化简历拼装为文本，作为文件抽取失败时的回退上下文。"""
    lines = [f"简历名称：{resume.name}", f"目标岗位：{resume.target_job_title}"]
    for e in resume.educations:
        lines.append(f"教育：{e.school} {e.major} {e.degree}（{e.start_date}~{e.end_date}）")
    for w in resume.work_experiences:
        lines.append(f"工作：{w.company} - {w.title}（{w.start_date}~{w.end_date}）：{w.description}")
    for p in resume.projects:
        lines.append(f"项目：{p.name}（{p.role}，{p.technologies}）：{p.description}")
    if resume.skills:
        lines.append("技能：" + "、".join(f"{s.skill_name}({s.level})" + (f"：{s.evidence}" if s.evidence else "") for s in resume.skills))
    return "\n".join(lines)

def resolve_resume_text(resume: Resume) -> str:
    """优先使用上传文件的真实文本，否则回退到结构化字段文本。"""
    return extract_file_text(resume.file_url) or build_resume_text(resume)

def calculate_completeness(resume: Resume) -> int:
    """根据实际填写内容量动态计算完整度（0-100）。

    不再只判断“有没有”，而是按 模块存在性 + 条目数量 + 描述丰富度 综合加权：
      基础分 5
      教育背景 15（每段 5，上限 15）
      项目经历 30（每段 10，上限 20；描述每满 60 字 +2，上限 10）
      工作经历 20（每段 10，上限 10；描述每满 60 字 +2，上限 10）
      技能 20（每项 4，上限 12；有佐证说明每项 +2，上限 8）
      目标岗位/名称 5
    """
    score = 5

    # 目标岗位与名称
    if resume.target_job_title and resume.target_job_title.strip():
        score += 5

    # 教育背景
    edu_count = len(resume.educations)
    score += min(15, edu_count * 5)

    # 项目经历（条目数 + 描述丰富度）
    projects = resume.projects or []
    score += min(20, len(projects) * 10)
    proj_desc_chars = sum(len((p.description or "").strip()) for p in projects)
    score += min(10, proj_desc_chars // 60 * 2)

    # 工作经历
    works = resume.work_experiences or []
    score += min(10, len(works) * 10)
    work_desc_chars = sum(len((w.description or "").strip()) for w in works)
    score += min(10, work_desc_chars // 60 * 2)

    # 技能
    skills = resume.skills or []
    score += min(12, len(skills) * 4)
    evidenced = sum(1 for s in skills if (s.evidence or "").strip())
    score += min(8, evidenced * 2)

    return max(0, min(100, score))

def build_resume_out(r: Resume) -> ResumeOut:
    return ResumeOut(
        id=r.id,
        user_id=r.user_id,
        name=r.name,
        is_default=r.is_default,
        file_url=r.file_url,
        file_name=r.file_name,
        status=r.status,
        target_job_id=r.target_job_id,
        target_job_title=r.target_job_title,
        completeness=r.completeness,
        created_at=r.created_at,
        updated_at=r.updated_at,
        educations=[
            EducationItem(school=e.school, major=e.major, degree=e.degree, start_date=e.start_date, end_date=e.end_date)
            for e in r.educations
        ],
        projects=[
            ProjectItem(name=p.name, role=p.role, description=p.description, technologies=p.technologies, start_date=p.start_date, end_date=p.end_date)
            for p in r.projects
        ],
        work_experiences=[
            WorkExperienceItem(company=w.company, title=w.title, description=w.description, start_date=w.start_date, end_date=w.end_date)
            for w in r.work_experiences
        ],
        skills=[
            SkillItem(skill_name=s.skill_name, level=s.level, evidence=s.evidence)
            for s in r.skills
        ]
    )

@router.get("/resumes", response_model=ResponseModel[List[ResumeOut]])
def list_my_resumes(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id,
        Resume.is_deleted == False
    ).order_by(Resume.id.desc()).all()

    return ResponseModel(data=[build_resume_out(r) for r in resumes])

@router.post("/resumes", response_model=ResponseModel[ResumeOut])
def create_resume(req: ResumeCreate, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    # If set default, clear existing default
    if req.is_default:
        db.query(Resume).filter(Resume.user_id == current_user.id).update({"is_default": False})

    new_resume = Resume(
        user_id=current_user.id,
        name=req.name,
        is_default=req.is_default,
        target_job_title=req.target_job_title,
        file_url=req.file_url,
        file_name=req.file_name,
        completeness=0
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    for edu in req.educations:
        db.add(ResumeEducation(resume_id=new_resume.id, **edu.model_dump()))
    for proj in req.projects:
        db.add(ResumeProject(resume_id=new_resume.id, **proj.model_dump()))
    for work in req.work_experiences:
        db.add(ResumeWorkExperience(resume_id=new_resume.id, **work.model_dump()))
    for sk in req.skills:
        db.add(ResumeSkill(resume_id=new_resume.id, **sk.model_dump()))

    # 先落库再刷新关系集合，确保完整度按真实内容量计算
    db.commit()
    db.refresh(new_resume)
    new_resume.completeness = calculate_completeness(new_resume)
    db.commit()
    db.refresh(new_resume)

    log_operation(db, current_user.id, current_user.email, "PERSONAL", "CREATE_RESUME", "RESUME", new_resume.id, f"创建新简历【{new_resume.name}】")
    return ResponseModel(data=build_resume_out(new_resume))

@router.get("/resumes/{id}", response_model=ResponseModel[ResumeOut])
def get_resume(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == id, Resume.is_deleted == False).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # SEC-01 check: User must own resume OR be an enterprise recruiter reviewing candidate application
    if resume.user_id != current_user.id:
        user_roles = [r.role_code for r in current_user.roles]
        is_admin = "PLATFORM_ADMIN" in user_roles or "SUPER_ADMIN" in user_roles
        is_recruiter = any(r in ["ENTERPRISE_OWNER", "ENTERPRISE_ADMIN", "RECRUITER", "INTERVIEWER", "HIRING_MANAGER"] for r in user_roles)
        if not (is_admin or is_recruiter):
            raise HTTPException(status_code=403, detail="无权访问该简历内容")

    return ResponseModel(data=build_resume_out(resume))

@router.put("/resumes/{id}", response_model=ResponseModel[ResumeOut])
def update_resume(id: int, req: ResumeUpdate, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id, Resume.is_deleted == False).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在或无修改权限")

    resume.name = req.name
    resume.target_job_title = req.target_job_title
    if req.file_url:
        resume.file_url = req.file_url
    if req.file_name:
        resume.file_name = req.file_name
    if req.is_default and not resume.is_default:
        db.query(Resume).filter(Resume.user_id == current_user.id).update({"is_default": False})
        resume.is_default = True

    # Clear and replace relations
    db.query(ResumeEducation).filter(ResumeEducation.resume_id == id).delete()
    db.query(ResumeProject).filter(ResumeProject.resume_id == id).delete()
    db.query(ResumeWorkExperience).filter(ResumeWorkExperience.resume_id == id).delete()
    db.query(ResumeSkill).filter(ResumeSkill.resume_id == id).delete()

    for edu in req.educations:
        db.add(ResumeEducation(resume_id=id, **edu.model_dump()))
    for proj in req.projects:
        db.add(ResumeProject(resume_id=id, **proj.model_dump()))
    for work in req.work_experiences:
        db.add(ResumeWorkExperience(resume_id=id, **work.model_dump()))
    for sk in req.skills:
        db.add(ResumeSkill(resume_id=id, **sk.model_dump()))

    # 先落库再刷新关系集合，确保完整度按真实内容量计算
    db.commit()
    db.refresh(resume)
    resume.completeness = calculate_completeness(resume)
    resume.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(resume)

    return ResponseModel(data=build_resume_out(resume))

@router.delete("/resumes/{id}", response_model=ResponseModel[dict])
def delete_resume(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id, Resume.is_deleted == False).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # Check if used in active applications
    active_apps = db.query(Application).filter(
        Application.resume_id == id,
        Application.status.notin_(["HIRED", "REJECTED", "WITHDRAWN"])
    ).count()

    if active_apps > 0:
        # Soft delete per specification to protect active enterprise applications
        resume.is_deleted = True
        db.commit()
        return ResponseModel(data={"message": "简历已归档（因存在进行中投递，已保留历史快照）"})
    else:
        resume.is_deleted = True
        db.commit()
        return ResponseModel(data={"message": "简历删除成功"})

@router.post("/resumes/{id}/parse", response_model=ResponseModel[ResumeAIParseResult])
async def parse_resume_ai(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 读取真实简历文本（优先文件抽取，回退结构化字段）
    resume_text = resolve_resume_text(resume)
    parsed = await ai_provider.parse_resume(resume_text)

    # Record analysis
    analysis = ResumeAIAnalysis(
        resume_id=resume.id,
        analysis_type="STRUCTURAL_PARSE",
        result_json=json.dumps(parsed, ensure_ascii=False),
        prompt_version="v1.0",
        model="real-llm" if ai_provider.is_real else "mock-ai"
    )
    db.add(analysis)

    # 将解析结果回写到结构化字段（若原有内容为空则填充）
    for e in parsed.get("education", []):
        db.add(ResumeEducation(resume_id=resume.id, **e))
    for p in parsed.get("projects", []):
        db.add(ResumeProject(
            resume_id=resume.id,
            name=p.get("name", "项目经历"),
            role=p.get("role", "核心开发"),
            description=p.get("description", ""),
            technologies=p.get("technologies", ""),
            start_date=p.get("start_date", ""),
            end_date=p.get("end_date", "")
        ))
    for w in parsed.get("work_experience", []):
        db.add(ResumeWorkExperience(resume_id=resume.id, **w))
    for s in parsed.get("skills", []):
        db.add(ResumeSkill(
            resume_id=resume.id,
            skill_name=s.get("skill_name", "技能"),
            level=s.get("level", "熟练"),
            evidence=s.get("evidence")
        ))
    db.commit()
    db.refresh(resume)
    resume.completeness = calculate_completeness(resume)
    db.commit()

    return ResponseModel(data=ResumeAIParseResult(
        educations=[EducationItem(**e) for e in parsed.get("education", [])],
        projects=[ProjectItem(name=p["name"], role=p["role"], description=p["description"], technologies=p.get("technologies", ""), start_date=p["start_date"], end_date=p["end_date"]) for p in parsed.get("projects", [])],
        work_experiences=[WorkExperienceItem(**w) for w in parsed.get("work_experience", [])],
        skills=[SkillItem(skill_name=s["skill_name"], level=s["level"], evidence=s.get("evidence")) for s in parsed.get("skills", [])],
        warnings=parsed.get("warnings", [])
    ))

@router.post("/resumes/{id}/optimize", response_model=ResponseModel[ResumeAIOptimizeResult])
async def optimize_resume_ai(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 接入真实 AI 模型进行简历深度诊断（不可达时自动回退 mock）
    res = await ai_provider.optimize_resume(resolve_resume_text(resume), resume.target_job_title)

    # 记录本次诊断
    analysis = ResumeAIAnalysis(
        resume_id=resume.id,
        analysis_type="COMPREHENSIVE",
        result_json=json.dumps(res, ensure_ascii=False),
        prompt_version="v2.0",
        model="real-llm" if ai_provider.is_real else "mock-ai"
    )
    db.add(analysis)
    db.commit()

    # 完整度以实际内容量为准
    res["completeness_score"] = resume.completeness

    return ResponseModel(data=ResumeAIOptimizeResult(**res))

@router.post("/resumes/{id}/optimize/apply", response_model=ResponseModel[ResumeOptimizeApplyResult])
async def apply_resume_optimization(id: int, current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """AI 一键优化：在不虚构事实的前提下改写项目/工作/技能表述并落库。"""
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    rewrite = await ai_provider.rewrite_resume(resolve_resume_text(resume), resume.target_job_title)
    changes = rewrite.get("changes") or []

    # 按名称匹配回写改写后的项目描述
    proj_map = {p.get("name"): p for p in rewrite.get("projects", []) if p.get("name")}
    for proj in resume.projects:
        new_p = proj_map.get(proj.name)
        if new_p:
            if new_p.get("description"):
                proj.description = new_p["description"]
            if new_p.get("technologies"):
                proj.technologies = new_p["technologies"]

    # 按公司+岗位匹配回写工作经历描述
    work_map = {(w.get("company"), w.get("title")): w for w in rewrite.get("work_experience", [])}
    for work in resume.work_experiences:
        new_w = work_map.get((work.company, work.title))
        if new_w and new_w.get("description"):
            work.description = new_w["description"]

    # 按技能名匹配回写技能佐证
    skill_map = {s.get("skill_name"): s for s in rewrite.get("skills", []) if s.get("skill_name")}
    for sk in resume.skills:
        new_s = skill_map.get(sk.skill_name)
        if new_s:
            if new_s.get("level"):
                sk.level = new_s["level"]
            if new_s.get("evidence"):
                sk.evidence = new_s["evidence"]

    resume.completeness = calculate_completeness(resume)
    resume.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(resume)

    log_operation(db, current_user.id, current_user.email, "PERSONAL", "OPTIMIZE_RESUME", "RESUME", resume.id, f"AI 一键优化简历【{resume.name}】")

    return ResponseModel(data=ResumeOptimizeApplyResult(
        resume=build_resume_out(resume),
        changes=changes
    ))
