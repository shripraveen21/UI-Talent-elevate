import os
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from ..models.models import Quiz
from ..Agents.McqAgent import QuizGenerationSystem
from ..schemas.schemas import QuizCreate
from ..config.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/mcq/store")
def store_quiz(quiz: QuizCreate, db: Session = Depends(get_db)):
    print("hello")
    try:
        print("started")
        print(quiz)
        db_quiz = Quiz(
            tech_stack_id=quiz.params.tech_stack,
            topic_ids=quiz.params.topics,
            num_questions=quiz.params.num_questions,
            duration=quiz.params.duration,
            questions = [{
            key: value.dict() if hasattr(value, "dict") else value
            for key, value in quiz.questions.items()
        }]
        )
        print(quiz.questions)
        print(db_quiz)
        db.add(db_quiz)
        db.commit()
        db.refresh(db_quiz)
        return {"success": True, "quiz_id": db_quiz.id}
    except Exception as e:
        logger.error(f"Error storing quiz: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store quiz")

@router.websocket("/ws/mcq-review")
async def mcq_review(websocket: WebSocket):
    await websocket.accept()
    try:
        # Step 1: Receive quiz parameters from frontend
        data = await websocket.receive_json()
        tech_stack = data.get("tech_stack")
        topics = data.get("topics")
        num_questions = data.get("num_questions")
        duration = data.get("duration")
        experience_level = data.get("experience_level", "intermediate")
        if not all([tech_stack, topics, num_questions, duration]):
            await websocket.send_json({"type": "error", "content": "Missing required quiz parameters"})
            await websocket.close()
            return

        # Step 2: Setup QuizGenerationSystem
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        quiz_system = QuizGenerationSystem(model_client)

        # Step 3: Generate initial quiz and feedback/refinement
        quiz_params = f"""
        Tech Stack: {tech_stack}
        Topics: {topics}
        Number of Questions: {num_questions}
        Duration: {duration} minutes
        Experience Level: {experience_level}
        """
        quiz = await quiz_system.generate_initial_quiz(quiz_params, )
        feedback = await quiz_system.get_feedback(quiz)
        refined_quiz = await quiz_system.refine_quiz(quiz, feedback)

        # Step 4: Interactive human review loop
        max_iterations = 3
        iteration = 0
        while iteration < max_iterations:
            # Send quiz to frontend for review
            import json
            await websocket.send_json({
                "type": "review",
                "content": json.loads(refined_quiz),
                "iteration": iteration + 1
            })
            # Wait for user decision
            user_decision_msg = await websocket.receive_json()
            user_decision = user_decision_msg.get("decision", "").strip()
            user_feedback = user_decision_msg.get("feedback", "")

            if user_decision == "APPROVE":
                import json
                await websocket.send_json({
                    "type": "final",
                    "content": json.loads(refined_quiz)
                })
                await model_client.close()
                await websocket.close()
                return
            elif user_decision == "REJECT":
                quiz = await quiz_system.generate_initial_quiz(quiz_params)
                feedback = await quiz_system.get_feedback(quiz)
                refined_quiz = await quiz_system.refine_quiz(quiz, feedback)
                iteration = 0
            elif user_decision == "REFINE":
                additional_feedback = await quiz_system.get_feedback(refined_quiz)
                refined_quiz = await quiz_system.refine_quiz(refined_quiz, additional_feedback)
            elif user_decision.startswith("FEEDBACK"):
                specific_feedback = user_feedback or user_decision.replace("FEEDBACK:", "").strip()
                refined_quiz = await quiz_system.refine_quiz(refined_quiz, specific_feedback)
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid decision. Please send APPROVE, REJECT, REFINE, or FEEDBACK."
                })
                continue
            iteration += 1

        # If max iterations reached, send current version
        import json
        await websocket.send_json({
            "type": "final",
            "content": json.loads(refined_quiz)
        })
        await model_client.close()
        await websocket.close()

    except WebSocketDisconnect:
        logger.info("Client disconnected during mcq review")
    except Exception as e:
        logger.error(f"Error in /ws/mcq-review: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
        await websocket.close()
