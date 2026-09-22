import os
import sys
import json
import argparse
from datetime import datetime, timedelta

# Ensure backend root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
import app.models

from app.models.user import User, Role, UserRole
from app.models.profile import PersonalProfile, CareerPreference, UserCompetency, CompetencyHistory
from app.models.company import Company, Department, CompanyMember, CompanyVerification
from app.models.job import Job, JobSkill, JobCompetency, JobFavorite
from app.models.resume import (
    Resume, ResumeEducation, ResumeProject, ResumeWorkExperience, ResumeSkill, ResumeAIAnalysis
)
from app.models.application import Application, ApplicationStatusHistory, CandidateTag
from app.models.interview import (
    Interview, InterviewPlan, InterviewQuestion, InterviewAnswer,
    AnswerEvaluation, InterviewReport, InterviewInvitation, RecruiterEvaluation
)
from app.models.learning import LearningPlan, LearningTask
from app.models.system import Notification, OperationLog

def seed(reset=True):
    print("=================================================================")
    print("智面舱 AI Interview Hub V2 - 高保真业务仿真数据初始化")
    print("=================================================================")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if reset:
        print("Clearing existing data for pristine environment...")
        for model in [
            CandidateTag, ApplicationStatusHistory, RecruiterEvaluation, AnswerEvaluation,
            InterviewAnswer, InterviewQuestion, InterviewPlan, InterviewReport, InterviewInvitation,
            Interview, Application, JobFavorite, JobCompetency, JobSkill, Job,
            CompanyVerification, CompanyMember, Department, Company,
            ResumeAIAnalysis, ResumeSkill, ResumeWorkExperience, ResumeProject, ResumeEducation, Resume,
            LearningTask, LearningPlan, CompetencyHistory, UserCompetency,
            CareerPreference, PersonalProfile, UserRole, Role, Notification, OperationLog, User
        ]:
            db.query(model).delete()
        db.commit()
    else:
        role_cnt = db.query(Role).count()
        user_cnt = db.query(User).count()
        job_cnt = db.query(Job).count()
        if role_cnt >= 8 and user_cnt >= 10 and job_cnt >= 10:
            print(f">>> [幂等性保护] 数据库已存在基准演示数据 (Roles: {role_cnt}, Users: {user_cnt}, Jobs: {job_cnt})，跳过重复初始化，无损保证幂等性。")
            db.close()
            return

    print("1. Seeding RBAC Roles...")
    roles = [
        Role(code="PERSONAL_USER", name="个人求职者", description="学生或社会求职者"),
        Role(code="ENTERPRISE_OWNER", name="企业负责人", description="企业拥有者，最高管理权限"),
        Role(code="ENTERPRISE_ADMIN", name="企业管理员", description="企业管理员"),
        Role(code="RECRUITER", name="招聘HR", description="招聘HR人员"),
        Role(code="INTERVIEWER", name="面试官", description="技术或业务面试官"),
        Role(code="HIRING_MANAGER", name="用人经理", description="部门用人负责人"),
        Role(code="PLATFORM_ADMIN", name="平台管理员", description="平台运营与审核管理"),
        Role(code="SUPER_ADMIN", name="超级管理员", description="系统超级管理员")
    ]
    db.add_all(roles)
    db.commit()

    common_pwd = get_password_hash("123456")

    print("2. Seeding 5 Verified Demo Companies...")
    companies_data = [
        {
            "name": "华为技术有限公司",
            "industry": "通信/云计算/智能终端",
            "size": "2000人以上",
            "city": "深圳",
            "intro": "全球领先的 ICT 基础设施与智能终端提供商，致力于把数字世界带入每个人、每个家庭、每个组织。",
            "logo": "https://img.icons8.com/color/96/huawei.png"
        },
        {
            "name": "腾讯科技",
            "industry": "社交/互动娱乐/数字医疗",
            "size": "2000人以上",
            "city": "深圳",
            "intro": "以科技向善为使命，连接十亿级用户的数字生态与前沿 AI 大模型应用。",
            "logo": "https://img.icons8.com/color/96/qq.png"
        },
        {
            "name": "阿里巴巴集团",
            "industry": "电子商务/阿里云/金融科技",
            "size": "2000人以上",
            "city": "杭州",
            "intro": "让天下没有难做的生意，构建未来数字商业与云基础设施。",
            "logo": "https://img.icons8.com/color/96/alibaba.png"
        },
        {
            "name": "字节跳动",
            "industry": "互联网/人工智能/内容中台",
            "size": "2000人以上",
            "city": "北京",
            "intro": "激发创造，丰富生活。核心产品涵盖抖音、今日头条、飞书及火山引擎。",
            "logo": "https://img.icons8.com/color/96/tiktok.png"
        },
        {
            "name": "小米集团",
            "industry": "消费电子/智能汽车/AIoT",
            "size": "2000人以上",
            "city": "北京",
            "intro": "让全球每个人都能享受科技带来的美好生活，手机×AIoT 核心战略。",
            "logo": "https://img.icons8.com/color/96/xiaomi.png"
        }
    ]

    companies = []
    for cd in companies_data:
        comp = Company(
            name=cd["name"],
            industry=cd["industry"],
            size=cd["size"],
            address=f"{cd['city']}市高新科技园区88号",
            city=cd["city"],
            intro=cd["intro"],
            logo_url=cd["logo"],
            status="VERIFIED"
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)
        companies.append(comp)

        dept = Department(company_id=comp.id, name="基础软件与云架构研发中心")
        db.add(dept)

        ver = CompanyVerification(
            company_id=comp.id,
            status="APPROVED",
            submitted_data_json=json.dumps({"license_number": "91110000123456789X", "legal_person": f"{cd['name']}法定代表人"}, ensure_ascii=False),
            opinion="企业营业执照核验一致，官方资质核验无误，予以认证通过",
            reviewed_at=datetime.utcnow() - timedelta(days=30)
        )
        db.add(ver)
        db.commit()

    primary_company = companies[0] # Huawei

    print("3. Seeding Enterprise Accounts for Huawei (Owner, Admin, Recruiter, Interviewer, Manager)...")
    ent_roles = [
        ("owner@example.com", "ENTERPRISE_OWNER", "OWNER", "李企业总负责人", "13800138002"),
        ("admin_corp@example.com", "ENTERPRISE_ADMIN", "ADMIN", "赵企业管理员", "13800138006"),
        ("hr@example.com", "RECRUITER", "RECRUITER", "王招聘主管HR", "13800138003"),
        ("interviewer@example.com", "INTERVIEWER", "INTERVIEWER", "刘技术面试官", "13800138004"),
        ("manager@example.com", "HIRING_MANAGER", "HIRING_MANAGER", "张用人部门经理", "13800138007")
    ]
    ent_users = {}
    for email, role_code, member_role, name, phone in ent_roles:
        u = User(email=email, phone=phone, password_hash=common_pwd, account_type="ENTERPRISE", status="ACTIVE")
        db.add(u)
        db.commit()
        db.refresh(u)
        db.add(UserRole(user_id=u.id, role_code=role_code, company_id=primary_company.id))
        db.add(CompanyMember(company_id=primary_company.id, user_id=u.id, role_code=member_role, status="ACTIVE"))
        db.add(PersonalProfile(user_id=u.id, name=name))
        ent_users[email] = u
    db.commit()

    # System Admin
    print("4. Seeding Platform Admin...")
    u_admin = User(email="admin@example.com", phone="13800138005", password_hash=common_pwd, account_type="ADMIN", status="ACTIVE")
    db.add(u_admin)
    db.commit()
    db.refresh(u_admin)
    db.add(UserRole(user_id=u_admin.id, role_code="PLATFORM_ADMIN"))
    db.add(UserRole(user_id=u_admin.id, role_code="SUPER_ADMIN"))
    db.add(PersonalProfile(user_id=u_admin.id, name="系统超级治理官"))
    db.commit()

    print("5. Seeding Primary Student (张同学 - student@example.com)...")
    u_student = User(email="student@example.com", phone="13800138001", password_hash=common_pwd, account_type="PERSONAL", status="ACTIVE")
    db.add(u_student)
    db.commit()
    db.refresh(u_student)
    db.add(UserRole(user_id=u_student.id, role_code="PERSONAL_USER"))
    db.add(PersonalProfile(
        user_id=u_student.id,
        profile_type="STUDENT",
        name="张同学",
        gender="男",
        education="本科",
        school="北京航空航天大学",
        major="计算机科学与技术",
        graduation_year=2024,
        work_years=0,
        bio="热爱后端基础架构与高并发调优，熟练掌握 Java、Spring Boot、Redis 与分布式系统设计。"
    ))
    db.add(CareerPreference(
        user_id=u_student.id,
        target_job_title="Java后端开发工程师",
        target_cities="长沙,深圳,上海",
        salary_min=12,
        salary_max=20,
        job_status="LOOKING"
    ))
    db.commit()

    print("6. Seeding 张同学 Specified Competency Radar...")
    # Exact required skills: Java 82, Spring Boot 76, MySQL 75, Redis 62, 计算机网络 65, 操作系统 60, 项目能力 78, 表达能力 72
    student_competencies = [
        ("Java", 82.0),
        ("Spring Boot", 76.0),
        ("MySQL", 75.0),
        ("Redis", 62.0),
        ("计算机网络", 65.0),
        ("操作系统", 60.0),
        ("项目能力", 78.0),
        ("表达能力", 72.0)
    ]
    for cname, score in student_competencies:
        db.add(UserCompetency(user_id=u_student.id, competency_name=cname, score=score, confidence=0.88))
    db.commit()

    # Redis Growth History: 43 -> 55 -> 69 (current is 62)
    redis_history = [
        (43.0, datetime.utcnow() - timedelta(days=21)),
        (55.0, datetime.utcnow() - timedelta(days=14)),
        (69.0, datetime.utcnow() - timedelta(days=7))
    ]
    for score, dt in redis_history:
        db.add(CompetencyHistory(
            user_id=u_student.id,
            competency_name="Redis",
            score=score,
            source_type="INTERVIEW",
            created_at=dt
        ))
    db.commit()

    print("7. Seeding Additional 14 Candidates for Talent Pipeline (Total 15+)...")
    candidates_meta = [
        ("chen@example.com", "陈天翔", "清华大学", "软件工程", "硕士"),
        ("wang@example.com", "王嘉尔", "北京大学", "智能科学与技术", "本科"),
        ("liu@example.com", "刘雨涵", "浙江大学", "计算机科学", "硕士"),
        ("zhao@example.com", "赵子明", "上海交通大学", "信息安全", "本科"),
        ("sun@example.com", "孙晓晴", "同济大学", "软件工程", "本科"),
        ("zhou@example.com", "周逸飞", "华中科技大学", "计算机应用", "硕士"),
        ("wu@example.com", "吴宏博", "西安电子科技大学", "通信工程", "本科"),
        ("zheng@example.com", "郑明", "哈尔滨工业大学", "计算机体系结构", "硕士"),
        ("feng@example.com", "冯一鸣", "电子科技大学", "网络工程", "本科"),
        ("han@example.com", "韩雪晴", "中南大学", "计算机科学", "本科"),
        ("qian@example.com", "钱学文", "湖南大学", "软件工程", "硕士"),
        ("tang@example.com", "唐小龙", "华南理工大学", "数据科学", "本科"),
        ("song@example.com", "宋子豪", "南京大学", "计算机科学", "硕士"),
        ("bai@example.com", "白羽洁", "东南大学", "信息工程", "本科")
    ]
    all_candidates = [u_student]
    for idx, (email, name, school, major, edu) in enumerate(candidates_meta):
        cu = User(email=email, phone=f"138001381{idx:02d}", password_hash=common_pwd, account_type="PERSONAL", status="ACTIVE")
        db.add(cu)
        db.commit()
        db.refresh(cu)
        db.add(UserRole(user_id=cu.id, role_code="PERSONAL_USER"))
        db.add(PersonalProfile(
            user_id=cu.id,
            profile_type="STUDENT",
            name=name,
            gender="男" if idx % 2 == 0 else "女",
            education=edu,
            school=school,
            major=major,
            graduation_year=2024,
            work_years=idx % 2,
            bio="积极进取，踏实肯干，对前沿工程架构具有浓厚兴趣。"
        ))
        db.add(CareerPreference(user_id=cu.id, target_job_title="Java后端开发工程师", target_cities="深圳,上海,北京", salary_min=14, salary_max=22))
        all_candidates.append(cu)
    db.commit()

    print("8. Seeding 20 Published Jobs Across 5 Companies...")
    job_templates = [
        ("Java后端开发工程师", "后端开发", "深圳", 15, 25, "本科及以上", "1-3年", "Java,Spring Boot,MySQL,Redis"),
        ("Java后端实习生", "后端开发", "深圳", 8, 12, "本科在读", "在校生", "Java,MySQL,计算机基础"),
        ("前端开发工程师", "前端开发", "深圳", 15, 25, "本科", "1-3年", "Vue3,TypeScript,CSS,Node.js"),
        ("测试开发工程师", "质量保障", "北京", 14, 24, "本科", "1-3年", "Python,Selenium,Pytest,CI/CD"),
        ("AI应用开发工程师", "人工智能", "北京", 25, 45, "本科及以上", "1-3年", "Python,LLM,LangChain,FastAPI"),
        ("Python开发工程师", "后端开发", "上海", 16, 28, "本科", "1-3年", "Python,Django,FastAPI,Redis"),
        ("数据分析师", "大数据", "杭州", 15, 26, "本科", "1-3年", "SQL,Python,Tableau,数据清洗"),
        ("产品经理", "产品规划", "北京", 18, 30, "本科及以上", "1-3年", "PRD,Axure,需求分析,AI应用"),
        ("运维工程师", "系统运维", "深圳", 14, 24, "本科", "1-3年", "Linux,Docker,K8s,Prometheus"),
        ("算法工程师", "人工智能", "北京", 30, 50, "硕士及以上", "应届生/1-3年", "PyTorch,深度学习,NLP,Transformer"),
        ("分布式中间件架构师", "后端开发", "北京", 28, 48, "本科及以上", "3-5年", "Java,Netty,Kafka,Zookeeper"),
        ("微服务系统开发工程师", "后端开发", "杭州", 18, 32, "本科及以上", "1-3年", "Java,Spring Cloud,Docker,K8s"),
        ("搜索与推荐中台开发", "后端开发", "上海", 20, 38, "本科及以上", "1-3年", "Java,Elasticsearch,Flink,MySQL"),
        ("移动端开发工程师", "客户端", "深圳", 16, 28, "本科", "1-3年", "Kotlin,Flutter,Android,Java"),
        ("大数据流批一体工程师", "大数据", "杭州", 22, 40, "本科及以上", "1-3年", "Spark,Flink,Hadoop,Hive"),
        ("分布式存储开发专家", "系统底层", "北京", 30, 50, "本科及以上", "3-5年", "C++,Linux,Ceph,Raft"),
        ("云原生SRE运维架构师", "运维架构", "深圳", 20, 36, "本科", "1-3年", "Go,Kubernetes,Prometheus,Linux"),
        ("安全与合规治理工程师", "信息安全", "上海", 18, 35, "本科及以上", "1-3年", "安全审计,渗透测试,Java,Spring"),
        ("电商业务中台研发", "后端开发", "杭州", 18, 32, "本科", "1-3年", "Java,MySQL,RocketMQ,Redis"),
        ("企业级低代码平台研发", "全栈研发", "深圳", 20, 35, "本科及以上", "1-3年", "Vue3,Java,Spring Boot,MySQL")
    ]

    all_jobs = []
    for idx, jt in enumerate(job_templates):
        comp = companies[idx % len(companies)]
        j = Job(
            company_id=comp.id,
            title=jt[0],
            category=jt[1],
            city=jt[2],
            salary_min=jt[3],
            salary_max=jt[4],
            education=jt[5],
            experience=jt[6],
            type="全职" if "实习" not in jt[0] else "实习",
            headcount=3,
            description=f"负责{comp.name}核心业务线【{jt[0]}】的产品技术演进与架构落地，支撑千万级高并发流量，保障系统持续稳定高可用。",
            duties="1. 参与核心业务微服务的设计、编码实现与单元测试；\n2. 深入排查系统运行中的性能瓶颈，解决分布式事务与并发一致性痛点；\n3. 协同产品与测试团队推动高质量敏捷交付。",
            requirements=f"1. 计算机及相关专业{jt[5]}学历；\n2. 深入掌握核心技术栈：{jt[7]}；\n3. 具备良好的工程素养、代码规范意识和优秀的团队沟通协同能力。",
            bonus="有知名互联网企业高并发实习背景，或在 GitHub 上有优质开源项目贡献者优先。",
            skills_required=jt[7],
            status="PUBLISHED"
        )
        db.add(j)
        db.commit()
        db.refresh(j)
        all_jobs.append(j)

        # Job Skills
        for sk in jt[7].split(","):
            db.add(JobSkill(job_id=j.id, skill_name=sk.strip(), level="熟练", required=True))

        # Job Competencies (Sum 100%)
        db.add(JobCompetency(job_id=j.id, competency_name="专业基础", weight=30.0, required_score=80.0))
        db.add(JobCompetency(job_id=j.id, competency_name="项目经验", weight=25.0, required_score=75.0))
        db.add(JobCompetency(job_id=j.id, competency_name="系统设计", weight=20.0, required_score=75.0))
        db.add(JobCompetency(job_id=j.id, competency_name="沟通表达", weight=15.0, required_score=80.0))
        db.add(JobCompetency(job_id=j.id, competency_name="综合素质", weight=10.0, required_score=80.0))

    db.commit()

    print("9. Seeding 3 High-Quality Resumes for 张同学...")
    # Resume 1: Java后端求职简历 (Default)
    r1 = Resume(
        user_id=u_student.id,
        name="Java后端求职简历",
        is_default=True,
        target_job_title="Java后端开发工程师",
        completeness=96
    )
    db.add(r1)
    db.commit()
    db.refresh(r1)

    db.add(ResumeEducation(
        resume_id=r1.id,
        school="北京航空航天大学",
        major="计算机科学与技术",
        degree="本科",
        start_date="2020-09",
        end_date="2024-06"
    ))
    db.add(ResumeProject(
        resume_id=r1.id,
        name="电商高并发秒杀与分布式锁中心",
        role="核心架构与后端主研",
        description="基于 Spring Boot + Redis 构建的高并发秒杀中台。设计基于 Redisson 的看门狗分布式锁防止超卖，利用本地缓存结合 Canal 监听 Binlog 保证双写一致性，系统压测 QPS 突破 4200+。",
        technologies="Java,Spring Boot,Redis,MySQL,Canal,Redisson",
        start_date="2023-03",
        end_date="2023-09"
    ))
    db.add(ResumeProject(
        resume_id=r1.id,
        name="微服务分布式配置与网关中心",
        role="技术骨干",
        description="集成 Spring Cloud Gateway 与 Nacos 实现灰度路由与动态限流熔断，使用 Sentinel 进行极端流量防护。",
        technologies="Spring Cloud,Nacos,Sentinel,JWT",
        start_date="2023-10",
        end_date="2024-01"
    ))
    db.add(ResumeWorkExperience(
        resume_id=r1.id,
        company="某知名互联网大厂基础架构部",
        title="Java 后端研发实习生",
        description="负责重构核心用户资产接口，优化 MySQL 慢查询执行计划，建立聚集索引覆盖，降低慢 SQL 比例 45%。",
        start_date="2023-09",
        end_date="2024-02"
    ))
    db.add(ResumeSkill(resume_id=r1.id, skill_name="Java", level="熟练", evidence="熟悉 JVM 内存模型、GC 调优与 JUC 并发编程框架"))
    db.add(ResumeSkill(resume_id=r1.id, skill_name="Spring Boot", level="熟练", evidence="熟练掌握微服务体系及 IOC/AOP 底层实现机制"))
    db.add(ResumeSkill(resume_id=r1.id, skill_name="Redis", level="熟练", evidence="熟练掌握分布式锁、缓存穿透/击穿/雪崩及延迟双删一致性"))
    db.add(ResumeSkill(resume_id=r1.id, skill_name="MySQL", level="熟练", evidence="深入理解 B+ 树聚集索引、事务隔离级别 MVCC 与 Explain 慢查优化"))
    db.add(ResumeSkill(resume_id=r1.id, skill_name="荣誉竞赛", level="精通", evidence="全国大学生计算机系统能力大赛二等奖、ACM-ICPC 区域赛银奖、校级优秀三好学生奖学金"))

    # Resume 2: AI应用开发简历
    r2 = Resume(
        user_id=u_student.id,
        name="AI应用开发简历",
        is_default=False,
        target_job_title="AI应用开发工程师",
        completeness=88
    )
    db.add(r2)
    db.commit()
    db.refresh(r2)
    db.add(ResumeEducation(resume_id=r2.id, school="北京航空航天大学", major="计算机科学与技术", degree="本科", start_date="2020-09", end_date="2024-06"))
    db.add(ResumeProject(
        resume_id=r2.id,
        name="企业级大模型知识库与智能问答 Agent",
        role="主创研发",
        description="基于 LangChain + FastAPI 构建的本地企业 RAG 知识库，结合 Milvus 向量检索和重排序算法，实现高准确率技术文档答疑。",
        technologies="Python,LangChain,FastAPI,Milvus,OpenAI API",
        start_date="2023-11",
        end_date="2024-04"
    ))
    db.add(ResumeSkill(resume_id=r2.id, skill_name="Python", level="熟练", evidence="精通异步编程与 FastAPI 接口开发"))
    db.add(ResumeSkill(resume_id=r2.id, skill_name="LLM/Agent", level="熟练", evidence="熟悉 Prompt Engineering、RAG 向量检索与 Function Calling"))

    # Resume 3: 综合实习简历
    r3 = Resume(
        user_id=u_student.id,
        name="综合实习简历",
        is_default=False,
        target_job_title="通用软件工程研发",
        completeness=85
    )
    db.add(r3)
    db.commit()
    db.refresh(r3)
    db.add(ResumeEducation(resume_id=r3.id, school="北京航空航天大学", major="计算机科学与技术", degree="本科", start_date="2020-09", end_date="2024-06"))
    db.add(ResumeProject(
        resume_id=r3.id,
        name="高校教学管理协同看板系统",
        role="全栈研发",
        description="采用 Vue 3 + Spring Boot 快速构建，支撑全校万名师生选课与成果管理。",
        technologies="Vue 3,Java,MySQL",
        start_date="2022-09",
        end_date="2023-01"
    ))
    db.commit()

    # Also seed resumes for other candidates
    candidate_resumes = [r1]
    for cu in all_candidates[1:]:
        cr = Resume(user_id=cu.id, name=f"{cu.profile.name}-核心求职简历", is_default=True, target_job_title="Java后端开发工程师", completeness=90)
        db.add(cr)
        db.commit()
        db.refresh(cr)
        db.add(ResumeEducation(resume_id=cr.id, school=cu.profile.school, major=cu.profile.major, degree=cu.profile.education, start_date="2020-09", end_date="2024-06"))
        db.add(ResumeProject(resume_id=cr.id, name="分布式数据流实时分析平台", role="研发工程师", description="基于 Flink + Kafka 进行海量日志统计分析与流式告警处理。", technologies="Java,Flink,Kafka,Redis", start_date="2023-03", end_date="2023-09"))
        db.add(ResumeSkill(resume_id=cr.id, skill_name="Java", level="熟练", evidence="精通并发和微服务开发"))
        candidate_resumes.append(cr)
    db.commit()

    print("10. Seeding 5 Specific Applications for 张同学 (Covering Timeline & History)...")
    # Required Applications for 张同学:
    # 1. Java后端开发工程师 (Huawei) -> ENTERPRISE_INTERVIEW
    # 2. Java后端实习生 (Tencent) -> AI_INTERVIEW_DONE
    # 3. Java开发工程师 (Alibaba) -> VIEWED
    # 4. 测试开发工程师 (ByteDance) -> SUBMITTED
    # 5. AI应用开发工程师 (Xiaomi) -> REJECTED
    student_apps_config = [
        (all_jobs[0], r1, "ENTERPRISE_INTERVIEW", 92, "HR与技术用人主管已完成两轮面试，处于入职终审评估阶段"),
        (all_jobs[1], r1, "AI_INTERVIEW_DONE", 88, "AI模拟面试综合评分88分，报告已授权用人单位查阅"),
        (all_jobs[5], r1, "VIEWED", 84, "企业招聘HR已查阅您的在线简历"),
        (all_jobs[3], r1, "SUBMITTED", 80, "投递成功，等待企业HR进行初步意向筛选"),
        (all_jobs[4], r2, "REJECTED", 72, "感谢您的关注，当前岗位因招聘名额已满暂时关闭")
    ]

    huawei_student_app = None
    for job, res, st, score, note in student_apps_config:
        app = Application(
            user_id=u_student.id,
            job_id=job.id,
            resume_id=res.id,
            resume_snapshot_json=json.dumps({
                "candidate_name": u_student.profile.name,
                "school": u_student.profile.school,
                "major": u_student.profile.major,
                "education": u_student.profile.education,
                "skills": [{"name": "Java", "level": "熟练"}, {"name": "Redis", "level": "熟练"}, {"name": "MySQL", "level": "熟练"}]
            }, ensure_ascii=False),
            status=st,
            match_score=score,
            assigned_recruiter_id=ent_users["hr@example.com"].id
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        if job.id == all_jobs[0].id:
            huawei_student_app = app

        # Build timeline history
        db.add(ApplicationStatusHistory(
            application_id=app.id,
            from_status=None,
            to_status="SUBMITTED",
            actor_id=u_student.id,
            note="候选人主动投递简历",
            created_at=datetime.utcnow() - timedelta(days=12)
        ))
        if st != "SUBMITTED":
            db.add(ApplicationStatusHistory(
                application_id=app.id,
                from_status="SUBMITTED",
                to_status=st,
                actor_id=ent_users["hr@example.com"].id,
                note=note,
                created_at=datetime.utcnow() - timedelta(days=2)
            ))

        # Add tags & invitation
        db.add(CandidateTag(company_id=job.company_id, application_id=app.id, tag="985高材生"))
        db.add(CandidateTag(company_id=job.company_id, application_id=app.id, tag="高并发实战强"))

    db.commit()

    print("11. Seeding Remaining Applications for Huawei to fill 15+ Pipeline...")
    # Pipeline stages: SUBMITTED, VIEWED, AI_SCREENING, AI_INTERVIEW_PENDING, ENTERPRISE_INTERVIEW, OFFER, HIRED, REJECTED
    stages_cycle = ["SUBMITTED", "AI_SCREENING", "AI_INTERVIEW_PENDING", "ENTERPRISE_INTERVIEW", "OFFER", "HIRED"]
    for idx, cu in enumerate(all_candidates[1:]):
        res = candidate_resumes[idx + 1]
        target_job = all_jobs[idx % 3] # Huawei's first 3 jobs
        stage = stages_cycle[idx % len(stages_cycle)]
        app = Application(
            user_id=cu.id,
            job_id=target_job.id,
            resume_id=res.id,
            resume_snapshot_json=json.dumps({
                "candidate_name": cu.profile.name,
                "school": cu.profile.school,
                "major": cu.profile.major,
                "education": cu.profile.education,
                "skills": [{"name": "Java", "level": "熟练"}, {"name": "Spring Boot", "level": "熟练"}]
            }, ensure_ascii=False),
            status=stage,
            match_score=80 + (idx % 18),
            assigned_recruiter_id=ent_users["hr@example.com"].id
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        db.add(ApplicationStatusHistory(
            application_id=app.id,
            from_status=None,
            to_status="SUBMITTED",
            actor_id=cu.id,
            note="候选人提交申请",
            created_at=datetime.utcnow() - timedelta(days=10 - (idx % 5))
        ))
        if stage != "SUBMITTED":
            db.add(ApplicationStatusHistory(
                application_id=app.id,
                from_status="SUBMITTED",
                to_status=stage,
                actor_id=ent_users["hr@example.com"].id,
                note=f"流程更新至【{stage}】",
                created_at=datetime.utcnow() - timedelta(days=1)
            ))
        if stage == "AI_INTERVIEW_PENDING":
            db.add(InterviewInvitation(
                company_id=primary_company.id,
                application_id=app.id,
                note="诚邀您参与华为 AI 智能面试筛选",
                expires_at=datetime.utcnow() + timedelta(days=4),
                status="PENDING"
            ))
        db.add(CandidateTag(company_id=primary_company.id, application_id=app.id, tag="技术功底好" if idx % 2 == 0 else "学历背景优"))
    db.commit()

    print("12. Seeding 5 Personal Training Interviews + 2 Enterprise Interviews (10+ Questions Each)...")
    # 5 Personal Interviews for 张同学 with progressive scores: 68 -> 76 -> 82 -> 84 -> 86
    interview_scores = [68.0, 76.0, 82.0, 84.0, 86.0]

    # Pre-defined 10 deep questions & answers for high-fidelity review
    qa_templates = [
        (
            1, "专业基础", "Redis",
            "请详细介绍在你的高并发秒杀项目中，如何利用 Redis 优化性能？在高并发读写下又是如何保障缓存与数据库一致性的？",
            "在项目中我们核心热点数据全部由 Redis 承载。读请求优先查缓存，未命中时查数据库并回写缓存。对于双写一致性，我们采用了延迟双删结合 Canal 监听 Binlog 异步补偿的策略，最大程度降低并发脏读窗口。",
            85.0,
            ["准确分析了缓存读写模型与性能收益", "对延迟双删与 Canal 方案阐述清晰"],
            ["未详细分析分布式事务 TCC 或两阶段在极端故障下的兜底"],
            ["Redisson 锁续期机制", "缓存击穿 Mutex 互斥锁实现"],
            "建议结合压测指标补充更详细的吞吐提升比例数据",
            "FOLLOW_UP"
        ),
        (
            2, "深度探究", "Redis",
            "如果在突发极端流量下，热点 Key 发生失效导致‘缓存击穿’，你会采取什么具体方案来防范？互斥锁与逻辑过期在实践中各有什么优劣取舍？",
            "防范缓存击穿核心有两种方案：第一种是互斥锁（如基于 Redisson 分布式锁），只有抢到锁的线程才能查库重建缓存，优点是保证绝对一致性，缺点是并发性能受限；第二种是逻辑过期，由后台异步线程刷新缓存，优点是吞吐高可用好，缺点是有极小概率读到脏数据。我们会根据业务关键程度进行权衡。",
            88.0,
            ["对比了互斥锁与逻辑过期的优缺点", "展现出良好的技术选型取舍意识"],
            ["对异步线程刷新异常时的熔断恢复机制未深入阐述"],
            ["布隆过滤器预防穿透"],
            "可以结合 Sentinel 限流降级进行系统兜底架构补充",
            "NEXT_TOPIC"
        ),
        (
            3, "专业基础", "Java并发",
            "请谈谈 Java 中的 volatile 关键字底层实现原理是什么？它能保证原子性吗？在 DCL 单例模式中它起到了什么关键作用？",
            "volatile 保证可见性和有序性，底层通过 CPU 内存屏障（Memory Barrier）禁止指令重排并强制刷新工作内存到主内存。它不能保证原子性，复合操作如 i++ 仍需 CAS 或 Synchronized。在 DCL 中，防止对象初始化过程中的指令重排导致其他线程拿到未完全初始化的半成品引用。",
            90.0,
            ["精准阐明内存屏障与指令重排机制", "对 DCL 对象实例化过程解析清晰透彻"],
            ["可进一步说明 x86 架构下 Lock 前缀指令的硬件总线锁原理"],
            ["happens-before 规则深度"],
            "回答非常扎实，保持这种深入源码的表达逻辑",
            "NEXT_TOPIC"
        ),
        (
            4, "系统设计", "MySQL",
            "为什么 MySQL InnoDB 存储引擎选择 B+ 树作为索引结构，而不是二叉树、红黑树或哈希表？",
            "哈希表不支持范围查询；二叉树和红黑树树高较高，在磁盘 IO 场景下寻道次数过多。而 B+ 树每个节点能存储大量键值，扇出非常大，树高通常只有 3~4 层即可支撑千万级数据，极大地减少了磁盘 IO；且所有叶子节点形成双向链表，非常利于范围遍历与排序。",
            92.0,
            ["对比了哈希、平衡树与 B+ 树的优缺点", "准确论述了磁盘 IO 与树高、双向链表范围查的关系"],
            ["无明显硬伤，逻辑完整"],
            [],
            "表达自然流畅，要点齐全",
            "NEXT_TOPIC"
        ),
        (
            5, "系统设计", "分布式锁",
            "使用 Redis 实现分布式锁时，如果业务处理时间超过了锁的超时时间怎么办？Redisson 是如何优雅解决锁续期问题的？",
            "如果业务耗时超过超时时间，锁会被提前释放导致并发安全失控。Redisson 提供了 Watchdog（看门狗）机制，当客户端获取锁成功后，后台会启动一个定时调度任务（默认每 10 秒），只要当前业务线程未释放锁，就会自动延长锁的过期时间，直到业务完成显式 unlock() 关闭看门狗。",
            88.0,
            ["精准指出锁提前释放的并发隐患", "清晰阐释看门狗的延期机制与关闭时机"],
            ["可补充主从切换极端场景下的 Redlock 算法优缺点讨论"],
            ["Redlock 算法"],
            "对 Redisson 源码掌握扎实，继续保持",
            "NEXT_TOPIC"
        ),
        (
            6, "项目深挖", "高并发设计",
            "在电商秒杀场景中，面对每秒万级的突发写流量，你如何设计多级缓存与库存防超卖架构？",
            "我们采用分层过滤与削峰设计：前端验证码打散流量，Nginx + Lua 读取本地缓存进行防刷校验；核心库存放在 Redis 中通过 Lua 脚本执行原子性校验与扣减，扣减成功后异步发 MQ 消息给下游创建订单进行削峰填谷，最终在 MySQL 层面使用带有 version 乐观锁条件的 UPDATE 语句做最后兜底。",
            89.0,
            ["架构层次感极强，覆盖了接入层、缓存层、消息队列到 DB 的全链路", "Lua 脚本原子性与乐观锁兜底设计到位"],
            ["可进一步补充对恶意黑产机器人的风控防御细节"],
            ["分布式限流令牌桶算法"],
            "体现了极佳的端到端架构实战意识",
            "NEXT_TOPIC"
        ),
        (
            7, "专业基础", "计算机网络",
            "请详细描述 TCP 三次握手和四次挥手的全过程，为什么握手需要三次而挥手需要四次？",
            "三次握手：客户端 SYN 发送，服务端 SYN+ACK 响应，客户端 ACK 确认，确保双方的发送与接收能力均正常且同步初始序号。挥手需要四次是因为 TCP 是全双工通信，当服务端收到 FIN 时可能仍有未发送完的数据，因此必须先发 ACK，待自身数据全部发送完毕后再单独发送 FIN，因此将 ACK 与 FIN 分开了两次。",
            86.0,
            ["清晰阐述了全双工连接关闭的半关闭状态", "状态迁移术语使用准确"],
            ["可补充 TIME_WAIT 状态的作用与 2MSL 持续时间的原因"],
            ["TIME_WAIT 危害与调优"],
            "基础功底过硬，建议强化网络极端边界场景",
            "NEXT_TOPIC"
        ),
        (
            8, "专业基础", "操作系统",
            "操作系统的进程与线程有什么本质区别？什么是协程？进程间通信（IPC）有哪几种常见方式？",
            "进程是系统资源分配的基本单位，拥有独立的虚拟地址空间；线程是 CPU 调度执行的基本单位，共享所在进程的资源。协程是用户态轻量级线程，由用户程序调度，避免内核态上下文切换。IPC 常见方式包括：管道（匿名/命名）、消息队列、共享内存、信号量、Socket 网络通信等，其中共享内存效率最高。",
            85.0,
            ["准确区分了进程、线程与用户态协程", "全面列举了常见 IPC 机制及共享内存的高效性"],
            ["对 Linux 进程写时复制（COW）机制未展开"],
            ["虚拟内存与页表机制"],
            "回答条理分明，知识面宽广",
            "NEXT_TOPIC"
        ),
        (
            9, "综合素质", "表达与抗压",
            "在项目中如果遇到了技术方案分歧或者上线前突发严重生产故障，你会如何应对和协同解决？",
            "面对技术分歧，我会基于客观事实与量化指标说话，列出各方案的成本、性能与风险收益进行对齐；如果遇到突发生产故障，首要原则是‘先止损，后排查’，第一时间通过服务降级、熔断或回滚将线上影响降到最低，随后再根据监控告警与全链路日志排查根因，最后输出故障复盘与长效防范机制。",
            88.0,
            ["‘先止损，后排查’的生产意识非常专业", "展现了成熟的团队协作与技术沟通情商"],
            ["无明显短板"],
            [],
            "具备优秀的工程成熟度与职场协同意识",
            "NEXT_TOPIC"
        ),
        (
            10, "综合素质", "学习规划",
            "你平时是通过什么途径保持技术前沿学习的？如果遇到完全陌生的技术难题，你的攻坚思路是什么？",
            "我主要通过阅读官方英文文档、精读优秀开源项目源码（如 Spring、Netty）以及关注技术社区与大厂工程博客来学习。遇到陌生难题时，我通常先定位官方 Spec 与错误日志，通过最小可复现 Demo 隔离变量排查，必要时单步断点跟踪源码，并善于借助 AI 助手拓宽解决思路，最后沉淀为技术博客。",
            87.0,
            ["学习渠道正规权威，排查思路结构化", "善于使用最小复现 Demo 隔离变量"],
            ["无"],
            [],
            "学习热情与钻研精神值得肯定",
            "FINISH"
        )
    ]

    # Seed 5 Personal Interviews for 张同学
    for p_idx, p_score in enumerate(interview_scores):
        p_interview = Interview(
            user_id=u_student.id,
            company_id=None,
            job_id=all_jobs[0].id,
            type="PERSONAL_TRAINING",
            mode="TECHNICAL",
            difficulty="MEDIUM",
            status="COMPLETED",
            current_question_seq=10,
            total_questions=10,
            duration_minutes=28,
            privacy_scope="PRIVATE",
            started_at=datetime.utcnow() - timedelta(days=21 - p_idx * 4, hours=2),
            ended_at=datetime.utcnow() - timedelta(days=21 - p_idx * 4, hours=1, minutes=32)
        )
        db.add(p_interview)
        db.commit()
        db.refresh(p_interview)

        # Plan
        stages = [
            {"stage": "专业基础", "questions_count": 4},
            {"stage": "深度探究", "questions_count": 2},
            {"stage": "系统设计", "questions_count": 2},
            {"stage": "综合素质", "questions_count": 2}
        ]
        db.add(InterviewPlan(interview_id=p_interview.id, stages_json=json.dumps(stages, ensure_ascii=False), total_questions=10, duration_minutes=30))

        # Add 10 Questions and Answers
        for q_tpl in qa_templates:
            q = InterviewQuestion(
                interview_id=p_interview.id,
                seq=q_tpl[0],
                stage=q_tpl[1],
                skill_name=q_tpl[2],
                text=q_tpl[3],
                difficulty="MEDIUM" if q_tpl[0] <= 5 else "HARD",
                source="AI_GENERATED"
            )
            db.add(q)
            db.commit()
            db.refresh(q)

            a = InterviewAnswer(
                question_id=q.id,
                interview_id=p_interview.id,
                user_id=u_student.id,
                text=q_tpl[4],
                duration_sec=50 + q_tpl[0] * 2,
                speaking_rate=158 + (q_tpl[0] % 5),
                filler_count=q_tpl[0] % 2
            )
            db.add(a)
            db.commit()
            db.refresh(a)

            db.add(AnswerEvaluation(
                answer_id=a.id,
                interview_id=p_interview.id,
                total_score=q_tpl[5],
                dimensions_json=json.dumps({"professional": 88, "relevance": 90, "completeness": 85, "logic": 86, "depth": 82, "communication": 85}),
                evidence_json=json.dumps(q_tpl[6], ensure_ascii=False),
                weaknesses_json=json.dumps(q_tpl[7], ensure_ascii=False),
                missing_knowledge_json=json.dumps(q_tpl[8], ensure_ascii=False),
                suggestions_json=json.dumps([q_tpl[9]], ensure_ascii=False),
                next_action=q_tpl[10]
            ))

        # Interview Report
        dim_scores = {
            "专业基础": round(p_score + 2.0, 1),
            "项目经验": round(p_score + 4.0, 1),
            "系统设计": round(p_score - 4.0, 1),
            "沟通表达": round(p_score + 1.0, 1),
            "综合素质": round(p_score, 1)
        }
        rep = InterviewReport(
            interview_id=p_interview.id,
            user_id=u_student.id,
            total_score=p_score,
            performance_level="表现优异" if p_score >= 80 else "表现良好",
            dimension_scores_json=json.dumps(dim_scores, ensure_ascii=False),
            strengths_json=json.dumps([
                "Redis 核心机制理解扎实：对高并发缓存击穿、穿透与一致性策略剖析到位",
                "逻辑表达结构严谨：回答问题善于采用总分总结构，技术观点鲜明",
                "项目实操经验充实：能结合实际秒杀业务指标说明技术方案的选型取舍"
            ], ensure_ascii=False),
            weaknesses_json=json.dumps([
                "分布式极端容灾设计深度稍显欠缺：对千亿级超大流量极端网络分区与多活架构考量可进一步深化",
                "异步刷新异常时的降级熔断兜底方案可更加体系化"
            ], ensure_ascii=False),
            suggestions_json=json.dumps([
                "重点精读 Redisson 源码实现与 Sentinel 限流熔断策略",
                "深入掌握微服务分布式链路追踪与全局发号器算法演练"
            ], ensure_ascii=False),
            summary=f"综合评分 {p_score} 分。技术基础过硬，实践项目经验丰富，具备优秀的后台研发与架构潜质。",
            status="COMPLETED"
        )
        db.add(rep)

        # Update Competency History
        db.add(CompetencyHistory(
            user_id=u_student.id,
            competency_name="Java后端综合训练",
            score=p_score,
            source_type="INTERVIEW",
            source_id=p_interview.id,
            created_at=datetime.utcnow() - timedelta(days=21 - p_idx * 4)
        ))

    db.commit()

    # 2 Enterprise Recruitment Interviews (Authorized for Huawei)
    print("13. Seeding 2 Authorized Enterprise Interviews for Huawei...")
    for e_idx in range(2):
        ent_interview = Interview(
            user_id=u_student.id,
            company_id=primary_company.id,
            job_id=all_jobs[0].id,
            application_id=huawei_student_app.id if huawei_student_app else None,
            type="ENTERPRISE_RECRUITMENT",
            mode="TECHNICAL",
            difficulty="HARD",
            status="COMPLETED",
            current_question_seq=10,
            total_questions=10,
            duration_minutes=32,
            privacy_scope="COMPANY_AUTHORIZED",
            started_at=datetime.utcnow() - timedelta(days=3 - e_idx, hours=3),
            ended_at=datetime.utcnow() - timedelta(days=3 - e_idx, hours=2, minutes=28)
        )
        db.add(ent_interview)
        db.commit()
        db.refresh(ent_interview)

        # Add 10 Questions and Answers
        for q_tpl in qa_templates:
            eq = InterviewQuestion(
                interview_id=ent_interview.id,
                seq=q_tpl[0],
                stage=q_tpl[1],
                skill_name=q_tpl[2],
                text=q_tpl[3],
                difficulty="HARD",
                source="AI_GENERATED"
            )
            db.add(eq)
            db.commit()
            db.refresh(eq)

            ea = InterviewAnswer(
                question_id=eq.id,
                interview_id=ent_interview.id,
                user_id=u_student.id,
                text=q_tpl[4],
                duration_sec=55,
                speaking_rate=160,
                filler_count=1
            )
            db.add(ea)
            db.commit()
            db.refresh(ea)

            db.add(AnswerEvaluation(
                answer_id=ea.id,
                interview_id=ent_interview.id,
                total_score=88.0,
                dimensions_json=json.dumps({"professional": 90, "relevance": 92, "completeness": 86, "logic": 88, "depth": 85, "communication": 88}),
                evidence_json=json.dumps(q_tpl[6], ensure_ascii=False),
                weaknesses_json=json.dumps(q_tpl[7], ensure_ascii=False),
                missing_knowledge_json=json.dumps(q_tpl[8], ensure_ascii=False),
                suggestions_json=json.dumps([q_tpl[9]], ensure_ascii=False),
                next_action=q_tpl[10]
            ))

        # Report for Enterprise
        db.add(InterviewReport(
            interview_id=ent_interview.id,
            user_id=u_student.id,
            total_score=88.5,
            performance_level="表现优异",
            dimension_scores_json=json.dumps({
                "专业基础": 90.0, "项目经验": 91.0, "系统设计": 84.0, "沟通表达": 88.0, "综合素质": 89.0
            }, ensure_ascii=False),
            strengths_json=json.dumps([
                "华为高并发云业务契合度高：对分布式锁与高并发性能调优具有成熟经验",
                "逻辑严谨且具备良好团队沟通协同视野"
            ], ensure_ascii=False),
            weaknesses_json=json.dumps(["超大规模分布式中间件调优细节仍有打磨空间"], ensure_ascii=False),
            suggestions_json=json.dumps(["建议进入第二轮业务主管终面"], ensure_ascii=False),
            summary="综合评分 88.5 分。专业功底扎实，对高并发与分布式架构理解透彻，建议予以重点推进录用流程。",
            status="COMPLETED"
        ))

        # Recruiter Evaluation
        db.add(RecruiterEvaluation(
            application_id=huawei_student_app.id if huawei_student_app else 1,
            interview_id=ent_interview.id,
            evaluator_id=ent_users["interviewer@example.com"].id,
            evaluator_name="刘技术面试官",
            dimensions_json=json.dumps({"technical": 90, "project": 92, "problem_solving": 88, "communication": 89, "job_fit": 92}),
            summary="该候选人技术功底扎实，对 Redis 缓存架构和高并发有深入理解，抗压与表达出色，建议予以录用。",
            recommendation="PASS"
        ))

    db.commit()

    print("14. Seeding Required 7 Structured Learning Tasks for 张同学...")
    # Required tasks: Redis缓存穿透, Redis缓存击穿, 缓存一致性, MySQL索引优化, TCP三次握手, 项目STAR表达, 高并发基础
    # Mixed status: DONE, DOING, TODO
    l_plan = LearningPlan(user_id=u_student.id, target_job_title="Java后端开发工程师", status="ACTIVE")
    db.add(l_plan)
    db.commit()
    db.refresh(l_plan)

    tasks_data = [
        ("Redis缓存穿透与布隆过滤器实战", "Redis", "HIGH", "DONE", 100, "在模拟面试中对穿透极端恶意请求防范已完成系统性巩固"),
        ("Redis缓存击穿防范：互斥锁与逻辑过期对比", "Redis", "HIGH", "DOING", 60, "针对热点 Key 失效瞬时冲击，深入编码调试 Redisson 互斥锁"),
        ("缓存与数据库最终一致性保障方案", "Redis", "HIGH", "TODO", 0, "深入分析 Canal 监听 Binlog 与延迟双删的补偿机制"),
        ("MySQL 索引优化：慢查询日志与 Explain 执行计划", "MySQL", "HIGH", "DONE", 100, "熟练掌握覆盖索引、最左前缀原则与 B+ 树分裂"),
        ("TCP 三次握手与四次挥手状态机深度解析", "计算机网络", "MEDIUM", "DONE", 100, "强化全双工通道关闭状态以及 2MSL TIME_WAIT 避免机制"),
        ("项目经验 STAR 法则结构化表达演练", "项目能力", "MEDIUM", "DOING", 50, "针对高并发秒杀项目提炼出 Situation, Task, Action, Result 汇报模型"),
        ("高并发系统基础：防重幂等与全局唯一发号器", "系统设计", "MEDIUM", "TODO", 0, "掌握雪花算法、数据库唯一约束与分布式 Token 防重设计")
    ]

    for title, comp_name, priority, status, progress, reason in tasks_data:
        db.add(LearningTask(
            plan_id=l_plan.id,
            user_id=u_student.id,
            title=title,
            competency_name=comp_name,
            priority=priority,
            status=status,
            progress=progress,
            reason=reason
        ))
    db.commit()

    print("15. Seeding 10 Mixed (Read/Unread) Realistic Notifications...")
    notifications_data = [
        ("INVITATION", "收到华为技术有限公司 AI 面试邀请", "华为技术有限公司向您发出了【Java后端开发工程师】的 AI 模拟面试筛选邀请，请在 5 天内进入面试间完成作答。", "/personal/applications", None),
        ("APPLICATION_PROGRESS", "企业已查看您的求职简历", "阿里巴巴集团 HR 已查看您的【Java后端求职简历】，正在进行综合岗位匹配评估。", "/personal/applications", datetime.utcnow() - timedelta(hours=3)),
        ("SYSTEM", "面试复盘诊断报告已生成", "您于昨日完成的【Java后端开发工程师】模拟面试已生成深度复盘报告，综合得分 82 分，点击立即查看能力提升建议。", "/interviews/3/report", datetime.utcnow() - timedelta(hours=5)),
        ("APPLICATION_PROGRESS", "求职流程推进至企业面试", "恭喜！华为技术有限公司招聘主管已将您的应聘流程推进至【企业面试阶段】。", "/personal/applications", None),
        ("LEARNING", "今日学习任务进度提醒", "您有一项高优先级的【Redis缓存击穿防范】今日待办学习任务尚未完成，建议今日完成打卡。", "/personal/learning", None),
        ("SYSTEM", "AI 岗位准备度模型更新", "根据您最新的模拟面试实战表现，您的【Java后端开发工程师】岗位准备度提升至 82%！", "/personal/dashboard", datetime.utcnow() - timedelta(days=1)),
        ("ENTERPRISE", "腾讯科技向您投递的岗位发送了状态通知", "您投递的【Java后端实习生】职位已完成 AI 初筛评估，成绩表现良好。", "/personal/applications", datetime.utcnow() - timedelta(days=2)),
        ("SYSTEM", "账号安全登录提醒", "您的账号于今日 09:30 在 Windows Chrome 成功登录，如非本人操作请及时修改密码。", "/personal/settings", datetime.utcnow() - timedelta(days=2)),
        ("APPLICATION_PROGRESS", "岗位投递成功确认", "您已成功向字节跳动投递了【测试开发工程师】职位，简历已安全同步至企业招聘系统。", "/personal/applications", datetime.utcnow() - timedelta(days=3)),
        ("SYSTEM", "欢迎加入智面舱 AI Interview Hub", "恭喜开启您的智能求职与职业成长之旅！完善简历即可开启全真模拟面试与人岗精准匹配。", "/personal/profile", datetime.utcnow() - timedelta(days=10))
    ]

    for ntype, title, content, link, read_at in notifications_data:
        db.add(Notification(
            user_id=u_student.id,
            type=ntype,
            title=title,
            content=content,
            link=link,
            read_at=read_at,
            created_at=read_at if read_at else datetime.utcnow()
        ))
    db.commit()

    print("16. Seeding Structured Question Bank (题库组卷引擎数据源)...")
    # 题库独立于业务数据：reset 不清空，采用幂等 upsert，避免误删人工维护的题目
    try:
        from scripts.seed_question_bank import seed_question_bank
    except ImportError:
        from seed_question_bank import seed_question_bank
    qb_stat = seed_question_bank(db)
    print(f"    题库就绪：新增 {qb_stat['inserted']}，更新 {qb_stat['updated']}，总量 {qb_stat['total']}")

    print("=================================================================")
    print("智面舱 AI Interview Hub V2 完整仿真业务数据装载成功！")
    print("=================================================================")
    print("核心演示账号 (密码统一为: 123456):")
    print(" - 学生演示求职: student@example.com (张同学，本科/北航)")
    print(" - 企业负责人:   owner@example.com (华为技术)")
    print(" - 企业招聘HR:   hr@example.com (华为技术)")
    print(" - 技术面试官:   interviewer@example.com (华为技术)")
    print(" - 部门用人经理: manager@example.com (华为技术)")
    print(" - 平台超级治理: admin@example.com")
    print("-----------------------------------------------------------------")
    print(f"数据总览: 企业数={len(companies)}, 岗位数={len(all_jobs)}, 候选人数={len(all_candidates)}")
    print(f"简历数={len(candidate_resumes) + 2}, 投递数={len(all_candidates) + 4}, 面试场次=7(含5次训练+2次企业)")
    print("=================================================================")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智面舱 Demo 数据装载器")
    parser.add_argument("--reset", action="store_true", default=True, help="重置已有数据并重新装载")
    args = parser.parse_args()
    seed(reset=args.reset)
