import asyncio
import os
import uuid
import logging
import traceback

from contextlib import contextmanager
from pathlib import Path

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from fastapi import APIRouter, WebSocket, Depends
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..services.auth_service import JWT_SECRET
from ..Agents.DebugGen.BugInjectionWorkflow import bug_injection_workflow
from ..Agents.DebugGen.ProjectCreationWorkflow import write_project_files, CodeAgent, StructureAgent, BRDAgent
from ..config.database import get_db
from ..models.models import DebugExercise, Topic, TechStack, Test

router = APIRouter()


async def bug_injection_and_db_save(
        db, model_client, unique_id, final_topics, tech_stack,
        difficulty, project_dir, duration, user_feedback, test_id=None
):
    try:
        logging.info(f"[{unique_id}] Background task started.")

        # 1. Regenerate BRD if feedback is present
        brd_agent = BRDAgent(model_client, project_dir)
        if user_feedback:
            brd_data = await brd_agent.generate_brd(tech_stack, final_topics, feedback=user_feedback)
            logging.info(f"[{unique_id}] BRD regenerated with feedback.")
        else:
            brd_data = await brd_agent.generate_brd(tech_stack, final_topics)
            logging.info(f"[{unique_id}] BRD generated without feedback.")

        brd_text = brd_data["brd"]

        # 2. Generate project structure
        structure_agent = StructureAgent(model_client, project_dir)
        structure, rationale = await structure_agent.generate_structure(brd_text, final_topics)
        logging.info(f"[{unique_id}] Structure generated.")

        # 3. Generate code files
        code_agent = CodeAgent(model_client, project_dir)
        files = await code_agent.generate_code(structure, brd_text, final_topics)
        logging.info(f"[{unique_id}] Code files generated.")

        write_project_files(project_dir, files)
        logging.info(f"[{unique_id}] Project files written.")

        # 4. Bug injection workflow
        created = await bug_injection_workflow(model_client, unique_id, final_topics, difficulty)
        if created:
            tech_stack_id = db.query(TechStack.id).filter(TechStack.name == tech_stack).scalar()
            topic_ids = [
                tid for (tid,) in db.query(Topic.topic_id).filter(
                    Topic.name.in_(final_topics),
                    Topic.tech_stack_id==tech_stack_id
                ).all()
            ]
            logging.info(f"[{unique_id}] Saving DebugExercise: tech_stack_id={tech_stack_id}, topic_ids={topic_ids}, duration={duration}, path_id={unique_id}")
            logging.info(f"[{unique_id}] DebugExercise saved successfully.")
        else:
            logging.warning(f"[{unique_id}] Bug injection workflow did not create exercise.")
    except Exception as e:
        logging.error(f"[{unique_id}] Error in background task: {e}")
        logging.error(traceback.format_exc())

@router.websocket("/ws/debug-gen-ws")
async def debug_gen_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.send_json({"type": "error", "content": "Missing token"})
            await websocket.close()
            logging.error("Missing token in WebSocket connection.")
            return

        try:
            user_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            logging.info(f"User authenticated: {user_payload}")
        except JWTError:
            await websocket.send_json({"type": "error", "content": "Invalid or expired token"})
            await websocket.close()
            logging.error("Invalid or expired token.")
            return

        try:
            data = await websocket.receive_json()
            test_id = data.get("test_id")
            tech_stack = data.get("tech_stack")
            topics = data.get("topics", [])
            difficulty = data.get("difficulty", "intermediate")
            duration = data.get("duration", 1)
            logging.info(f"Received data: {data}")

            if not all([tech_stack, topics, difficulty]):
                await websocket.send_json({"type": "error", "content": "Missing required exercise parameters"})
                await websocket.close()
                logging.error("Missing required exercise parameters.")
                return

            model_client = AzureOpenAIChatCompletionClient(
                azure_deployment="gpt-4.1",
                model="gpt-4.1",
                api_version="2024-06-01",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            )

            unique_id = str(uuid.uuid4())
            gen_proj_dir = os.getenv("GEN_PROJ_DIR", "GeneratedProject")
            project_dir = f"{gen_proj_dir}/{unique_id}/project"
            Path(project_dir).mkdir(parents=True, exist_ok=True)
            logging.info(f"[{unique_id}] Project directory created: {project_dir}")

            # 1. Generate initial BRD and suggested topics
            brd_agent = BRDAgent(model_client, project_dir)
            brd_data = await brd_agent.generate_brd(tech_stack, topics)
            logging.info(f"[{unique_id}] Initial BRD generated.")

            # 2. Send BRD and suggested topics to client for feedback
            await websocket.send_json({
                "type": "brd_review",
                "brd": brd_data["brd"],
                "initial_topics": brd_data["topics"],
                "suggested_topics": brd_data["suggested_topics"]
            })

            # 3. Wait for client to send final topic list and feedback
            feedback = await websocket.receive_json()
            final_topics = feedback.get("final_topics")
            user_feedback = feedback.get("feedback", "")
            logging.info(f"[{unique_id}] Received feedback: {feedback}")

            if not final_topics:
                final_topics = brd_data["topics"] + [item["topic"] for item in brd_data["suggested_topics"]]
                logging.info(f"[{unique_id}] No final_topics provided, using all topics: {final_topics}")

            # 4. Send immediate 'accepted' response and start background task
            await websocket.send_json({
                "type": "accepted",
                "content": "Your selection has been accepted. Project generation will proceed in the background."
            })
            logging.info(f"[{unique_id}] Accepted response sent to client.")

            tech_stack_id = db.query(TechStack.id).filter(TechStack.name == tech_stack).scalar()
            topic_ids = [
                tid for (tid,) in db.query(Topic.topic_id).filter(
                    Topic.name.in_(final_topics),
                    Topic.tech_stack_id==tech_stack_id
                ).all()
            ]

            print("dataaa",tech_stack_id,topic_ids)

            debug_exercise = DebugExercise(
                tech_stack_id=tech_stack_id,
                topic_ids=topic_ids,
                duration=duration,
                path_id=unique_id,
            )
            db.add(debug_exercise)
            db.commit()
            print("idddd",debug_exercise.id)

            await websocket.send_json({
                "type": "final_id",
                "debug_exercise":debug_exercise.id
                })

            asyncio.create_task(
                bug_injection_and_db_save(
                    db, model_client, unique_id, final_topics, tech_stack,
                    difficulty, project_dir, duration, user_feedback,test_id
                )
            )


            await websocket.close()
            logging.info(f"[{unique_id}] WebSocket closed after accept.")

            return 

        except Exception as e:
            logging.error(f"Error during WebSocket workflow: {e}")
            logging.error(traceback.format_exc())
            await websocket.send_json({"type": "error", "content": f"Server error: {e}"})
            await websocket.close()

    except Exception as e:
        logging.error(f"Unexpected error in WebSocket endpoint: {e}")
        logging.error(traceback.format_exc())
        try:
            await websocket.send_json({"type": "error", "content": f"Unexpected server error: {e}"})
        except Exception:
            pass
        await websocket.close()
