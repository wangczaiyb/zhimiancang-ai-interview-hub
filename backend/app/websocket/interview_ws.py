import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.interview import (
    Interview, InterviewQuestion, InterviewAnswer, AnswerEvaluation, InterviewReport
)
from app.models.profile import CompetencyHistory, UserCompetency
from app.models.user import User
from app.ai.provider import ai_provider
from app.api.v1.interviews import (
    load_interview_context, build_question_payload, build_ai_reference_points,
    next_fallback_question, PROFESSIONAL
)
from app.api.v1.personal import generate_and_store_learning_plan, resolve_target_job

logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, interview_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[interview_id] = websocket

    def disconnect(self, interview_id: int):
        if interview_id in self.active_connections:
            del self.active_connections[interview_id]

    async def send_json(self, interview_id: int, message: Dict[str, Any]):
        ws = self.active_connections.get(interview_id)
        if ws:
            await ws.send_text(json.dumps(message, ensure_ascii=False))

manager = ConnectionManager()

async def handle_interview_websocket(websocket: WebSocket, interview_id: int):
    await manager.connect(interview_id, websocket)
    db: Session = SessionLocal()
    try:
        # Load interview
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "面试记录不存在"
            }))
            await websocket.close()
            return

        # 加载 JD 与简历上下文（与 REST 通道保持一致）
        jd_text, resume_context = load_interview_context(interview, db)
        # 仅面试结束后下发参考答案，作答过程中保持闭卷
        reveal = interview.status in ("COMPLETED", "CANCELLED", "EXPIRED")

        # Send connected event
        await manager.send_json(interview_id, {
            "type": "connected",
            "interview_id": interview_id,
            "status": interview.status,
            "current_seq": interview.current_question_seq,
            "total_questions": interview.total_questions
        })

        # Send current question
        current_q = db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview_id,
            InterviewQuestion.seq == interview.current_question_seq
        ).first()

        if current_q:
            payload = build_question_payload(current_q, reveal_reference=reveal)
            payload["type"] = "question"
            await manager.send_json(interview_id, payload)

        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            event_type = data.get("type")

            if event_type == "transcript_partial":
                # Forward to client as live transcript echo
                await manager.send_json(interview_id, {
                    "type": "transcript_partial",
                    "text": data.get("text", "")
                })

            elif event_type == "transcript_final":
                answer_text = data.get("text", "")
                q_id = data.get("question_id") or (current_q.id if current_q else None)

                if not q_id or not answer_text:
                    continue

                q_obj = db.query(InterviewQuestion).filter(InterviewQuestion.id == q_id).first()
                if not q_obj:
                    continue

                # Save answer
                answer = db.query(InterviewAnswer).filter(InterviewAnswer.question_id == q_id).first()
                if not answer:
                    answer = InterviewAnswer(
                        question_id=q_id,
                        interview_id=interview_id,
                        user_id=interview.user_id,
                        text=answer_text,
                        duration_sec=data.get("duration_sec", 45),
                        speaking_rate=data.get("speaking_rate", 160),
                        filler_count=data.get("filler_count", 1)
                    )
                    db.add(answer)
                    db.commit()
                    db.refresh(answer)

                await manager.send_json(interview_id, {
                    "type": "answer_saved",
                    "answer_id": answer.id
                })

                # Real-time feedback
                await manager.send_json(interview_id, {
                    "type": "feedback",
                    "tip": "回答条理清晰，建议在后半段加入具体高并发指标佐证"
                })

                # Evaluate answer (JD + resume + 题库参考答案 aware，与 REST 通道一致)
                ws_ref_points = None
                if q_obj.reference_points_json:
                    try:
                        parsed = json.loads(q_obj.reference_points_json)
                        ws_ref_points = parsed if isinstance(parsed, list) else None
                    except Exception:
                        ws_ref_points = None
                eval_res = await ai_provider.evaluate_answer(
                    q_obj.text, answer_text, q_obj.seq,
                    jd_text=jd_text or None,
                    resume_context=resume_context or None,
                    reference_points=ws_ref_points
                )

                # Save answer evaluation
                evaluation = AnswerEvaluation(
                    answer_id=answer.id,
                    interview_id=interview_id,
                    total_score=eval_res["score"],
                    dimensions_json=json.dumps(eval_res["dimensions"], ensure_ascii=False),
                    evidence_json=json.dumps(eval_res["evidence"], ensure_ascii=False),
                    weaknesses_json=json.dumps(eval_res["weaknesses"], ensure_ascii=False),
                    missing_knowledge_json=json.dumps(eval_res["missing_knowledge"], ensure_ascii=False),
                    suggestions_json=json.dumps(eval_res["suggestions"], ensure_ascii=False),
                    next_action=eval_res.get("next_action", "CHANGE_TOPIC")
                )
                db.add(evaluation)
                db.commit()

                # Check if finished
                if q_obj.seq >= interview.total_questions:
                    # Mark completed
                    interview.status = "COMPLETED"
                    db.commit()

                    # Generate report (transcript-aware)
                    all_evals = db.query(AnswerEvaluation).filter(AnswerEvaluation.interview_id == interview_id).all()
                    scores = [e.total_score for e in all_evals] or [eval_res["score"]]
                    job_title = interview.job.title if interview.job else "Java后端开发工程师"
                    qa_pairs = []
                    for q in sorted(interview.questions, key=lambda x: x.seq):
                        if q.answer and q.answer.evaluation:
                            qa_pairs.append({
                                "seq": q.seq,
                                "question": q.text,
                                "answer": q.answer.text,
                                "score": q.answer.evaluation.total_score
                            })
                    report_data = await ai_provider.generate_report(
                        interview_id, interview.total_questions, scores,
                        qa_pairs=qa_pairs or None,
                        job_title=job_title
                    )

                    rep = InterviewReport(
                        interview_id=interview_id,
                        user_id=interview.user_id,
                        total_score=report_data["total_score"],
                        performance_level=report_data["performance_level"],
                        dimension_scores_json=json.dumps(report_data["dimension_scores"], ensure_ascii=False),
                        strengths_json=json.dumps(report_data["strengths"], ensure_ascii=False),
                        weaknesses_json=json.dumps(report_data["weaknesses"], ensure_ascii=False),
                        suggestions_json=json.dumps(report_data["suggestions"], ensure_ascii=False),
                        summary=report_data["summary"],
                        status="COMPLETED"
                    )
                    db.add(rep)

                    # Update competency history
                    comp_hist = CompetencyHistory(
                        user_id=interview.user_id,
                        competency_name=q_obj.skill_name,
                        score=report_data["total_score"],
                        source_type="INTERVIEW",
                        source_id=interview_id
                    )
                    db.add(comp_hist)

                    # Update or insert user_competency
                    u_comp = db.query(UserCompetency).filter(
                        UserCompetency.user_id == interview.user_id,
                        UserCompetency.competency_name == q_obj.skill_name
                    ).first()
                    if u_comp:
                        u_comp.score = report_data["total_score"]
                    else:
                        u_comp = UserCompetency(
                            user_id=interview.user_id,
                            competency_name=q_obj.skill_name,
                            score=report_data["total_score"]
                        )
                        db.add(u_comp)

                    # Auto generate staged learning tasks based on target job (from user's career preference)
                    user = db.query(User).filter(User.id == interview.user_id).first()
                    target_job_title = resolve_target_job(user) if user else job_title
                    await generate_and_store_learning_plan(
                        db, user, target_job_title,
                        jd_text=jd_text or None,
                        gaps=report_data.get("weaknesses"),
                        replace=True
                    )
                    db.commit()

                    await manager.send_json(interview_id, {
                        "type": "finished",
                        "interview_id": interview_id,
                        "report_status": "COMPLETED",
                        "report_url": f"/personal/interviews/{interview_id}/report"
                    })
                else:
                    # Generate or load next question
                    next_seq = q_obj.seq + 1
                    interview.current_question_seq = next_seq
                    db.commit()

                    next_q = db.query(InterviewQuestion).filter(
                        InterviewQuestion.interview_id == interview_id,
                        InterviewQuestion.seq == next_seq
                    ).first()

                    if not next_q:
                        # 卷面已预生成，此处仅在缺题时兜底（与 REST 通道逻辑一致）
                        job_title = interview.job.title if interview.job else "Java后端开发工程师"
                        q_data = await ai_provider.generate_question(
                            job_title=job_title,
                            seq=next_seq,
                            difficulty=interview.difficulty,
                            last_question=q_obj.text,
                            last_answer=answer_text,
                            last_score=eval_res.get("score") if eval_res else None,
                            jd_text=jd_text or None,
                            resume_context=resume_context or None
                        )
                        text = q_data.get("question") or ""
                        if not text:
                            fb = next_fallback_question(
                                [q.text for q in interview.questions],
                                interview.total_questions, next_seq
                            )
                            text = fb["text"]
                            q_data = {**fb, "question": text}
                        next_q = InterviewQuestion(
                            interview_id=interview_id,
                            parent_question_id=q_obj.id,
                            seq=next_seq,
                            stage=q_data.get("stage") or "专业基础",
                            question_type=q_data.get("question_type") or PROFESSIONAL,
                            skill_name=q_data.get("skill_name") or job_title,
                            text=text,
                            difficulty=q_data.get("difficulty") or interview.difficulty,
                            hints=q_data.get("hints"),
                            time_limit_sec=q_data.get("time_limit_sec") or 180,
                            reference_points_json=json.dumps(
                                build_ai_reference_points(job_title, text), ensure_ascii=False
                            ),
                            source="AI_GENERATED"
                        )
                        db.add(next_q)
                        db.commit()
                        db.refresh(next_q)

                    current_q = next_q
                    payload = build_question_payload(next_q, reveal_reference=False)
                    payload["type"] = "next_question"
                    await manager.send_json(interview_id, payload)

            elif event_type == "pause":
                interview.status = "PAUSED"
                db.commit()
                await manager.send_json(interview_id, {"type": "paused"})

            elif event_type == "resume":
                interview.status = "IN_PROGRESS"
                db.commit()
                await manager.send_json(interview_id, {"type": "resumed"})

            elif event_type == "finish":
                interview.status = "COMPLETED"
                db.commit()
                await manager.send_json(interview_id, {
                    "type": "finished",
                    "interview_id": interview_id,
                    "report_url": f"/personal/interviews/{interview_id}/report"
                })

    except WebSocketDisconnect:
        manager.disconnect(interview_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(interview_id)
    finally:
        db.close()
