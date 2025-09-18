import logging
import os
from fastapi import APIRouter, Body, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..models.models import TechStack, Topic, HandsOn
from ..config.database import get_db
from ..Agents.HandsOnGen.HandsOnGenerator import RequirementsAgent, AssignmentAgent, ReadmeAgent, BoilerplateAgent
from ..Agents.DebugGen.FSTool import FileSystemTool
from pathlib import Path
import json
import uuid
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

router = APIRouter()

@router.post("/handson/store")
def store_handson(handson: dict = Body(...), db: Session = Depends(get_db)):
    try:
        tech_stack = handson.get("tech_stack")
        topics = handson.get("topics", [])
        duration = handson.get("duration")
        path_id = handson.get("path_id")

        tech_stack_id = db.query(TechStack.id).filter(TechStack.name.ilike(tech_stack)).scalar()
        topic_ids = [
            tid for (tid,) in db.query(Topic.topic_id).filter(
                Topic.name.in_(topics),
                Topic.tech_stack_id == tech_stack_id
            ).all()
        ]

        db_handson = HandsOn(
            tech_stack_id=tech_stack_id,
            topic_ids=topic_ids,
            duration=duration,
            path_id=path_id
        )
        db.add(db_handson)
        db.commit()
        db.refresh(db_handson)
        return {"success": True, "handson_id": db_handson.id}
    except Exception as e:
        logging.error(f"Error storing HandsOn: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store HandsOn record")


@router.websocket("/ws/create-handson")
async def srs_feedback_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        # Step 1: Receive initial project info
        data = await websocket.receive_json()
        print(data)
        tech_stack = data.get("tech_stack")
        topics = data.get("topics", [])
        duration = data.get("duration", 1)

        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )

        unique_id = str(uuid.uuid4())
        output_dir = os.getenv("HANDSON_DIR", "GeneratedHandsON")
        project_dir = f"{output_dir}/{unique_id}/project"
        Path(project_dir).mkdir(parents=True, exist_ok=True)

        requirements_agent = RequirementsAgent(model_client, project_dir, FileSystemTool)

        regen_count = 0
        max_regen = 3
        approved = False
        srs_md = None

        # SRS feedback loop
        while regen_count < max_regen and not approved:
            srs_md = await requirements_agent.generate_srs(tech_stack, topics)
            await websocket.send_json({
                "type": "srs_review",
                "srs_md": srs_md,
                "regen_count": regen_count + 1,
                "max_regen": max_regen
            })

            feedback = await websocket.receive_json()
            user_action = feedback.get("action")  # "approve" or "suggest"
            suggestions = feedback.get("suggestions", [])

            if user_action == "approve":
                approved = True
            else:
                if suggestions:
                    topics = list(set(topics + suggestions))
                regen_count += 1

        # SRS approved, run full workflow
        await websocket.send_json({"type": "status", "content": "SRS approved. Generating assignment, README, and boilerplate..."})
        srs_path = Path(project_dir) / "SRS.md"
        FileSystemTool.write_file(srs_path, srs_md)

        # Assignment
        assignment_agent = AssignmentAgent(model_client, project_dir, FileSystemTool)
        assignment_md = await assignment_agent.generate_assignment("Project", srs_md)
        assignment_path = Path(project_dir) / "ASSIGNMENT.md"
        FileSystemTool.write_file(assignment_path, assignment_md)
        await websocket.send_json({"type": "status", "content": "Assignment generated."})

        # README
        readme_agent = ReadmeAgent(model_client, project_dir, FileSystemTool)
        readme_md = await readme_agent.generate_readme(srs_md)
        readme_path = Path(project_dir) / "README.md"
        FileSystemTool.write_file(readme_path, readme_md)
        await websocket.send_json({"type": "status", "content": "README generated."})

        # Boilerplate
        boilerplate_agent = BoilerplateAgent(model_client, project_dir, FileSystemTool, tech_stack)
        files = await boilerplate_agent.generate_boilerplate(srs_md)
        for filename, code in files.items():
            file_path = Path(project_dir) / filename
            FileSystemTool.write_file(file_path, code)
        await websocket.send_json({"type": "status", "content": "Boilerplate code generated."})

        # Final message
        await websocket.send_json({
            "type": "final",
            "content": {
                "tech_stack": tech_stack,
                "topics": topics,
                "duration": duration,
                "path_id": unique_id,
                "project_dir": project_dir,
                "srs_md": srs_md,
                "assignment_path": str(assignment_path),
                "readme_path": str(readme_path),
                "boilerplate_files": list(files.keys())
            },
            "message": "All files generated and saved. You may now POST to /handson/store to save metadata."
        })
        await websocket.close()

    except Exception as e:
        logging.error(f"Error in SRS feedback workflow: {e}")
        try:
            await websocket.send_json({"type": "error", "content": f"Server error: {e}"})
        except Exception as send_err:
            logging.error(f"Could not send error message over WebSocket: {send_err}")
        try:
            await websocket.close()
        except Exception as close_err:
            logging.error(f"Could not close WebSocket: {close_err}")
