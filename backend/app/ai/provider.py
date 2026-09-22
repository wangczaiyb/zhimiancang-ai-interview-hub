import time
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings
from app.ai.schemas import (
    ResumeParseSchema, JDParseSchema, QuestionGenSchema,
    AnswerEvalSchema, ReportGenSchema, LearningPlanSchema,
    MatchExplainerSchema, ResumeOptimizeSchema, ResumeRewriteSchema
)
from app.ai.mock_data import (
    MOCK_RESUME_PARSED, MOCK_JD_PARSED, INTERVIEW_QUESTION_POOL,
    generate_mock_evaluation, generate_adaptive_mock_question,
    generate_mock_report, generate_mock_learning_tasks
)

logger = logging.getLogger("ai_provider")

class AIProvider:
    def __init__(self):
        self.mode = (settings.AI_MODE or "real").strip().lower()
        self.base_url = settings.LLM_BASE_URL
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    @property
    def is_real(self) -> bool:
        """仅当显式开启 real 且配置了 Key 时才调用真实模型。"""
        return self.mode != "mock" and bool(self.api_key)

    async def _call_llm_json(self, prompt: str, schema_class) -> Dict[str, Any]:
        """Calls real LLM API with fallback to mock if unreachable or unconfigured."""
        if not self.is_real:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional AI interview engine. Output ONLY valid JSON matching the requested structure."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    # Validate schema
                    validated = schema_class(**parsed)
                    return validated.model_dump()
        except Exception as e:
            logger.warning(f"Real LLM call failed, falling back to mock: {e}")
            return None
        return None

    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Parses resume text into structured entities."""
        prompt = f"Parse this resume into JSON:\n{resume_text}"
        real_res = await self._call_llm_json(prompt, ResumeParseSchema)
        if real_res:
            return real_res
        # Mock mode fallback
        validated = ResumeParseSchema(**MOCK_RESUME_PARSED)
        return validated.model_dump()

    async def parse_jd(self, jd_text: str) -> Dict[str, Any]:
        """Parses enterprise JD text into job fields and skill requirements."""
        prompt = f"Parse this Job Description into JSON:\n{jd_text}"
        real_res = await self._call_llm_json(prompt, JDParseSchema)
        if real_res:
            return real_res
        validated = JDParseSchema(**MOCK_JD_PARSED)
        return validated.model_dump()

    async def generate_question(
        self,
        job_title: str,
        stage: str = "专业基础",
        difficulty: str = "MEDIUM",
        seq: int = 1,
        last_question: str = None,
        last_answer: str = None,
        last_score: float = None,
        jd_text: str = None,
        resume_context: str = None,
        question_type: str = None
    ) -> Dict[str, Any]:
        """Dynamically generates interview question based on JD, resume and candidate's previous response."""
        type_hint = ""
        if question_type:
            type_desc = {
                "PROFESSIONAL": "a role-specific technical/professional question grounded in the JD skills",
                "GENERAL": "a general/behavioral question (project deep-dive, collaboration, learning ability)",
                "STRESS": "a pressure question that simulates a high-stress scenario (production incident, hostile challenge, tight deadline)"
            }.get(question_type.upper(), "")
            if type_desc:
                type_hint = f"\nRequired question type: {question_type.upper()} — {type_desc}."

        prompt = (
            f"You are an expert technical interviewer conducting an interview for '{job_title}'.\n"
            f"Question sequence: {seq}\n"
            f"Target stage: {stage} | Difficulty: {difficulty}{type_hint}\n\n"
            f"=== Job Description (JD) ===\n{(jd_text or 'N/A')[:2000]}\n\n"
            f"=== Candidate Resume ===\n{(resume_context or 'N/A')[:2000]}\n\n"
            f"Last question asked: {last_question or 'N/A'}\n"
            f"Candidate's last answer: {last_answer or 'N/A'}\n"
            f"Last answer score: {last_score if last_score is not None else 'N/A'}\n\n"
            f"Requirements:\n"
            f"- Ground the question in the JD's required skills and the candidate's actual resume/projects.\n"
            f"- If the candidate answered with high technical depth, generate a deep follow-up probing edge cases, concurrency, or architectural trade-offs.\n"
            f"- If the candidate's answer was superficial or indicated lack of knowledge, generate a foundational question to diagnose core concepts.\n"
            f"- Output JSON adhering to: question, skill_name, stage, difficulty, hints, "
            f"question_type (PROFESSIONAL|GENERAL|STRESS), time_limit_sec (integer seconds, 120-300)."
        )
        real_res = await self._call_llm_json(prompt, QuestionGenSchema)
        if real_res:
            return real_res

        # Adaptive Mock Engine
        raw_q = generate_adaptive_mock_question(
            job_title=job_title,
            seq=seq,
            last_question=last_question,
            last_answer=last_answer,
            last_score=last_score
        )
        if question_type:
            raw_q["question_type"] = question_type
        else:
            # 按阶段推断题型，保证 mock 题也带题型标签
            inferred_stage = raw_q.get("stage") or ""
            if inferred_stage in ("综合素养", "基础素养"):
                raw_q["question_type"] = "GENERAL"
            elif inferred_stage == "压力应对":
                raw_q["question_type"] = "STRESS"
            else:
                raw_q["question_type"] = "PROFESSIONAL"
        validated = QuestionGenSchema(**raw_q)
        return validated.model_dump()

    async def evaluate_answer(
        self, question_text: str, answer_text: str, seq: int, jd_text: str = None,
        resume_context: str = None, reference_points: List[str] = None
    ) -> Dict[str, Any]:
        """Evaluates single answer using the 6-dimension Rubric with JSON Schema validation."""
        ref_block = ""
        if reference_points:
            points = "\n".join(f"- {p}" for p in reference_points[:6])
            ref_block = (
                "\n=== Reference Key Points (grading rubric anchor) ===\n"
                f"{points}\n"
                "Judge coverage of these key points explicitly: reward genuinely covered points, "
                "and list uncovered ones in missing_knowledge.\n"
            )

        prompt = (
            "You are a strict but fair technical interview evaluator.\n"
            "Score the candidate's answer on a 0-100 scale across 6 dimensions: "
            "professional(30%), relevance(20%), completeness(15%), logic(15%), depth(15%), communication(5%).\n\n"
            f"=== Job Description (JD) ===\n{(jd_text or 'N/A')[:1500]}\n\n"
            f"=== Candidate Resume ===\n{(resume_context or 'N/A')[:1500]}\n"
            f"{ref_block}\n"
            f"Question #{seq}: {question_text}\n"
            f"Candidate answer: {answer_text}\n\n"
            "Output JSON with keys: score (0-100 float), dimensions "
            "(professional, relevance, completeness, logic, depth, communication), "
            "evidence (list of strings), weaknesses (list), missing_knowledge (list), "
            "suggestions (list), next_action (one of FOLLOW_UP, DEEP, BASIC, CHANGE_TOPIC, FINISH)."
        )
        real_res = await self._call_llm_json(prompt, AnswerEvalSchema)
        if real_res:
            return real_res

        raw_eval = generate_mock_evaluation(question_text, answer_text, seq)
        validated = AnswerEvalSchema(**raw_eval)
        return validated.model_dump()

    async def generate_report(
        self, interview_id: int, total_questions: int, scores: List[float] = None,
        qa_pairs: List[Dict[str, Any]] = None, job_title: str = None
    ) -> Dict[str, Any]:
        """Generates comprehensive interview post-review report with radar scores."""
        if qa_pairs:
            transcript = "\n".join(
                f"Q{item.get('seq')}: {item.get('question')}\nA: {item.get('answer')}\nScore: {item.get('score')}"
                for item in qa_pairs
            )
            prompt = (
                f"You are a senior interview coach writing a post-interview review report for '{job_title or '技术岗位'}'.\n"
                f"Here is the full transcript with per-question scores:\n{transcript[:4000]}\n\n"
                "Output JSON with keys: total_score (0-100 float), performance_level (中文), "
                "dimension_scores (dict of 专业基础, 项目经验, 系统设计, 沟通表达, 综合素质 -> float), "
                "strengths (list of 中文 strings), weaknesses (list), suggestions (list), summary (中文 string)."
            )
            real_res = await self._call_llm_json(prompt, ReportGenSchema)
            if real_res:
                return real_res

        raw_report = generate_mock_report(interview_id, total_questions, scores)
        validated = ReportGenSchema(**raw_report)
        return validated.model_dump()

    async def generate_learning_plan(
        self, job_title: str, gaps: List[str] = None, jd_text: str = None, count: int = 6
    ) -> List[Dict[str, Any]]:
        """Generates staged, targeted tasks for personal growth roadmap based on target job/JD."""
        prompt = (
            f"You are a career coach building a staged learning roadmap for the target role '{job_title}'.\n"
            f"=== Job Description (JD) ===\n{(jd_text or 'N/A')[:2000]}\n\n"
            f"Known weak points / gaps: {', '.join(gaps) if gaps else 'N/A'}\n\n"
            f"Generate exactly {count} learning tasks ordered by stage.\n"
            "Output JSON: {\"tasks\": [{\"title\": str(中文), \"competency_name\": str, "
            "\"priority\": \"HIGH|MEDIUM|LOW\", \"reason\": str(中文), "
            "\"action_type\": \"INTERVIEW_PRACTICE|COURSE|READING|PROJECT\", \"stage\": str(中文阶段名)}]}"
        )
        real_res = await self._call_llm_json(prompt, LearningPlanSchema)
        if real_res and real_res.get("tasks"):
            return real_res["tasks"]

        tasks = generate_mock_learning_tasks()
        validated = LearningPlanSchema(tasks=tasks)
        return validated.model_dump()["tasks"]

    async def optimize_resume(self, resume_text: str, job_title: str = None) -> Dict[str, Any]:
        """Analyzes and diagnoses a resume, returning structured optimization advice."""
        prompt = (
            "You are a senior resume consultant. Analyze the resume below against the target role "
            f"'{job_title or '通用技术岗位'}'.\n\n"
            f"=== Resume ===\n{resume_text[:4000]}\n\n"
            "Output JSON with keys: completeness_score (0-100 int), strengths (list of 中文 strings), "
            "improvements (list of 中文 strings), suggested_modifications "
            "(list of {section, suggestion} objects), keyword_enrichment (list of 中文技术关键词)."
        )
        real_res = await self._call_llm_json(prompt, ResumeOptimizeSchema)
        if real_res:
            return real_res

        return {
            "completeness_score": 78,
            "strengths": [
                "教育背景清晰，专业技术对口",
                "项目描述具备 STAR 原则雏形，阐明了高并发和分布式锁的应用"
            ],
            "improvements": [
                "建议量化项目收益，例如支撑 QPS 从 800 提升至 5000+",
                "技能模块建议明确区分‘精通’与‘熟练’，突出核心竞争力"
            ],
            "suggested_modifications": [
                {"section": "项目经历", "suggestion": "在电商秒杀项目中补充‘利用 Redis Lua 脚本原子扣减库存’等细节"},
                {"section": "自我评价", "suggestion": "突出对分布式高可用与故障排查的热情与实操案例"}
            ],
            "keyword_enrichment": ["JVM调优", "Redis主从哨兵", "RocketMQ事务消息", "MySQL分库分表"]
        }

    async def rewrite_resume(self, resume_text: str, job_title: str = None) -> Dict[str, Any]:
        """Rewrites resume project/skill descriptions to be more compelling without fabricating facts."""
        prompt = (
            "You are a senior resume writer. Rewrite the descriptions in the resume below to be more "
            f"compelling for the role '{job_title or '通用技术岗位'}'.\n"
            "CRITICAL: Never fabricate experiences, companies, metrics or technologies not present. "
            "Only improve wording, structure (STAR) and clarity, and surface existing highlights.\n\n"
            f"=== Resume ===\n{resume_text[:4000]}\n\n"
            "Output JSON: {\"projects\": [{\"name\": str, \"description\": str, \"technologies\": str}], "
            "\"skills\": [{\"skill_name\": str, \"level\": str, \"evidence\": str}], "
            "\"work_experience\": [{\"company\": str, \"title\": str, \"description\": str}], "
            "\"changes\": [list of 中文 strings describing what was improved]}"
        )
        real_res = await self._call_llm_json(prompt, ResumeRewriteSchema)
        if real_res:
            return real_res
        return {"projects": [], "skills": [], "work_experience": [], "changes": []}

    async def explain_job_match(
        self, job_title: str, candidate_skills: List[str], required_skills: List[str]
    ) -> Dict[str, Any]:
        """Calculates deterministic match score and returns explanation."""
        c_set = set(s.lower() for s in candidate_skills)
        r_set = set(s.lower() for s in required_skills) if required_skills else {"java", "mysql", "redis", "spring boot"}

        adv = [s for s in required_skills if s.lower() in c_set]
        missing = [s for s in required_skills if s.lower() not in c_set]

        if not adv and not missing:
            adv = ["Java", "Spring Boot", "MySQL"]
            missing = ["分布式系统"]

        score = min(98, max(60, int(60 + len(adv) * 8 - len(missing) * 4)))

        data = {
            "match_score": score,
            "advantage_skills": adv or ["Java", "MySQL"],
            "missing_skills": missing or ["大型分布式实战"],
            "explanation": f"候选人与【{job_title}】匹配度为 {score}%。熟练掌握核心技能 {', '.join(adv or ['Java'])}，但在 {', '.join(missing or ['分布式'])} 方面仍有深度拓展空间。"
        }
        validated = MatchExplainerSchema(**data)
        return validated.model_dump()

ai_provider = AIProvider()
