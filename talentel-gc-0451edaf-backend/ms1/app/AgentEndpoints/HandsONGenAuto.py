import logging
import os
from fastapi import APIRouter, Body, Depends, HTTPException
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

async def run_handson_gen_auto(
    db: Session,
    tech_stack: str,
    topics: list,
    duration: int = 1
):
    try:
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

        # SRS Generation (no feedback loop)
        requirements_agent = RequirementsAgent(model_client, project_dir, FileSystemTool)
        srs_md = await requirements_agent.generate_srs(tech_stack, topics)

        # Assignment
        assignment_agent = AssignmentAgent(model_client, project_dir, FileSystemTool)
        assignment_md = await assignment_agent.generate_assignment(f"Skill Upgrade {tech_stack}", srs_md)

        assignment_path = Path(project_dir) / "ASSIGNMENT.md"
        FileSystemTool.write_file(assignment_path, assignment_md)

        # README
        readme_agent = ReadmeAgent(model_client, project_dir, FileSystemTool)
        readme_md = await readme_agent.generate_readme(srs_md)

        readme_path = Path(project_dir) / "README.md"
        FileSystemTool.write_file(readme_path, readme_md)

        # Boilerplate
        boilerplate_agent = BoilerplateAgent(model_client, project_dir, FileSystemTool, tech_stack)
        files = await boilerplate_agent.generate_boilerplate(srs_md)

        for filename, code in files.items():
            file_path = Path(project_dir) / filename
            FileSystemTool.write_file(file_path, code)

        # Store metadata in DB
        tech_stack_id = db.query(TechStack.id).filter(TechStack.name == tech_stack).scalar()
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
            path_id=unique_id
        )
        db.add(db_handson)
        db.commit()
        db.refresh(db_handson)

        return {
            "success": True,
            "handson_id": db_handson.id,
            "tech_stack": tech_stack,
            "topics": topics,
            "duration": duration,
            "path_id": unique_id,
            "project_dir": project_dir,
            "srs_md": srs_md,
            "assignment_path": str(assignment_path),
            "readme_path": str(readme_path),
            "boilerplate_files": list(files.keys()),
            "message": "All files generated and saved. Metadata stored in DB."
        }
    except Exception as e:
        logging.error(f"Error in auto-generate workflow: {e}")
        db.rollback()
        return {
            "success": False,
            "handson_id": None,
            "error": str(e),
            "message": "Failed to auto-generate HandsOn. See logs for details."
        }

@router.post("/handson/auto-generate")
def auto_generate_handson(
    handson: dict = Body(...),
    db: Session = Depends(get_db)
):
    return run_handson_gen_auto(
        db=db,
        tech_stack=handson.get("tech_stack"),
        topics=handson.get("topics", []),
        duration=handson.get("duration", 1)
    )
