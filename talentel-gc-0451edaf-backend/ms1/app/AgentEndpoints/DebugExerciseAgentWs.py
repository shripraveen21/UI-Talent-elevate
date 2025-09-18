import os
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from ..models.models import DebugExercise
from ..Agents.DebugExerciseAgent import DebugExerciseGenerator
from ..schemas.schemas import DebugExerciseCreate
from ..config.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/debug-exercise/store")
def store_debug_exercise(exercise: DebugExerciseCreate, db: Session = Depends(get_db)):
    try:
        db_exercise = DebugExercise(
            tech_stack_id=exercise.tech_stack_id,
            topic_ids=exercise.topic_ids,
            num_questions=exercise.num_questions,
            duration=exercise.duration,
            exercises=exercise.exercises
        )
        db.add(db_exercise)
        db.commit()
        db.refresh(db_exercise)
        return {"success": True, "exercise_id": db_exercise.id}
    except Exception as e:
        logger.error(f"Error storing debug exercise: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store debug exercise")

@router.websocket("/ws/debug-exercise")
async def debug_exercise_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        # Step 1: Receive exercise parameters from frontend
        print("recieved in backedn")
        data = await websocket.receive_json()
        tech_stack = data.get("tech_stack", [])
        concepts = data.get("concepts", [])
        num_questions = data.get("num_questions")
        duration = data.get("duration")
        difficulty = data.get("difficulty", None)
        print("got",tech_stack, concepts, num_questions, duration)
        if not all([tech_stack, concepts, num_questions, duration]):
            await websocket.send_json({"type": "error", "content": "Missing required exercise parameters"})
            await websocket.close()
            return
        print("all data")
        # Step 2: Setup DebugExerciseGenerator
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        generator = DebugExerciseGenerator(model_client)

        # Step 3: Generate exercises and calibration feedback
        print("Starting generating")
        result = await generator.generate_exercises(tech_stack, concepts, num_questions, duration, difficulty)
        if "error" in result:
            await websocket.send_json({"type": "error", "content": result["error"]})
            await model_client.close()
            await websocket.close()
            return
        print("finiishing generating")

        # calibration_result = await generator.calibrate_difficulty(result)
        # Step 4: Interactive human review loop
        max_iterations = 3
        iteration = 0
        # exercises_data = calibration_result.get("exercises", result)
        exercises_data = result

        while iteration < max_iterations:
            # Send exercises to frontend for review
            import json
            print("sedning data",exercises_data)
            await websocket.send_json({
                "type": "review",
                "content": exercises_data,
                "iteration": iteration + 1
            })
            print("Sent")
            # Wait for user decision
            user_decision_msg = await websocket.receive_json()
            user_decision = user_decision_msg.get("decision", "").strip()
            user_feedback = user_decision_msg.get("feedback", "")
            print("Watiting")
            if user_decision == "APPROVE":
                await websocket.send_json({
                    "type": "final",
                    "content": exercises_data
                })
                await model_client.close()
                await websocket.close()
                return
            elif user_decision == "REJECT":
                result = await generator.generate_exercises(tech_stack, concepts, num_questions, duration, difficulty)
                if "error" in result:
                    await websocket.send_json({"type": "error", "content": result["error"]})
                    await model_client.close()
                    await websocket.close()
                    return
                calibration_result = await generator.calibrate_difficulty(result)
                exercises_data = calibration_result.get("exercises", result)
                iteration = 0
            elif user_decision == "REFINE":
                calibration_result = await generator.calibrate_difficulty(exercises_data)
                exercises_data = calibration_result.get("exercises", exercises_data)
            elif user_decision.startswith("FEEDBACK"):
                specific_feedback = user_feedback or user_decision.replace("FEEDBACK:", "").strip()
                # For debug exercises, feedback can be used to regenerate or refine
                # Here, we simply regenerate with feedback as a concept/topic
                new_concepts = concepts + [specific_feedback] if specific_feedback else concepts
                result = await generator.generate_exercises(tech_stack, new_concepts, num_questions, duration, difficulty)
                if "error" in result:
                    await websocket.send_json({"type": "error", "content": result["error"]})
                    await model_client.close()
                    await websocket.close()
                    return
                calibration_result = await generator.calibrate_difficulty(result)
                exercises_data = calibration_result.get("exercises", result)
            else:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid decision. Please send APPROVE, REJECT, REFINE, or FEEDBACK."
                })
                continue
            iteration += 1

        # If max iterations reached, send current version
        await websocket.send_json({
            "type": "final",
            "content": exercises_data
        })
        await model_client.close()
        await websocket.close()

    except WebSocketDisconnect:
        logger.info("Client disconnected during debug exercise review")
    except Exception as e:
        logger.error(f"Error in /ws/debug-exercise: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
        await websocket.close()
