import asyncio
import os
import uuid
import logging
import traceback

from pathlib import Path

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from sqlalchemy.orm import Session

from ..services.auth_service import JWT_SECRET
from ..Agents.DebugGen.BugInjectionWorkflow import bug_injection_workflow
from ..Agents.DebugGen.ProjectCreationWorkflow import write_project_files, CodeAgent, StructureAgent, BRDAgent
from ..config.database import get_db
from ..models.models import DebugExercise, Topic, TechStack

async def run_debug_gen_auto(
    db: Session,
    tech_stack: str,
    topics: list,
    difficulty: str = "intermediate",
    duration: int = 1,
    azure_deployment: str = "gpt-4.1",
    model: str = "gpt-4.1",
    api_version: str = "2024-06-01",
    azure_endpoint: str = None,
    api_key: str = None,
    gen_proj_dir: str = None,
    user_feedback: str = ""
):
    """
    Fully automated debug generation workflow.
    No human-in-the-loop. All topics and suggested topics are used.
    """
    try:
        if azure_endpoint is None:
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if api_key is None:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if gen_proj_dir is None:
            gen_proj_dir = os.getenv("GEN_PROJ_DIR", "GeneratedProject")

        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment=azure_deployment,
            model=model,
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=api_key,
        )

        unique_id = str(uuid.uuid4())
        project_dir = f"{gen_proj_dir}/{unique_id}/project"
        Path(project_dir).mkdir(parents=True, exist_ok=True)
        logging.info(f"[{unique_id}] Project directory created: {project_dir}")

        # 1. Generate initial BRD and suggested topics
        brd_agent = BRDAgent(model_client, project_dir)
        brd_data = await brd_agent.generate_brd(tech_stack, topics)
        logging.info(f"[{unique_id}] Initial BRD generated.")

        # 2. Automatically select all topics and suggested topics
        final_topics = brd_data["topics"] + [item["topic"] for item in brd_data["suggested_topics"]]
        brd_text = brd_data["brd"]

        # 3. Regenerate BRD if user_feedback is provided (optional, usually empty)
        if user_feedback:
            brd_data = await brd_agent.generate_brd(tech_stack, final_topics, feedback=user_feedback)
            brd_text = brd_data["brd"]
            logging.info(f"[{unique_id}] BRD regenerated with feedback.")

        # 4. Generate project structure
        structure_agent = StructureAgent(model_client, project_dir)
        structure, rationale = await structure_agent.generate_structure(brd_text, final_topics)
        logging.info(f"[{unique_id}] Structure generated.")

        # 5. Generate code files
        code_agent = CodeAgent(model_client, project_dir)
        files = await code_agent.generate_code(structure, brd_text, final_topics)
        logging.info(f"[{unique_id}] Code files generated.")

        write_project_files(project_dir, files)
        logging.info(f"[{unique_id}] Project files written.")

        # 6. Bug injection workflow
        created = await bug_injection_workflow(model_client, unique_id, final_topics, difficulty)
        if created:
            tech_stack_id = db.query(TechStack.id).filter(TechStack.name == tech_stack).scalar()
            topic_ids = [
                tid for (tid,) in db.query(Topic.topic_id).filter(
                    Topic.name.in_(final_topics),
                    Topic.tech_stack_id == tech_stack_id
                ).all()
            ]
            logging.info(f"[{unique_id}] Saving DebugExercise: tech_stack_id={tech_stack_id}, topic_ids={topic_ids}, duration={duration}, path_id={unique_id}")
            debug_exercise = DebugExercise(
                tech_stack_id=tech_stack_id,
                topic_ids=topic_ids,
                duration=duration,
                path_id=unique_id,
            )
            db.add(debug_exercise)
            db.commit()
            logging.info(f"[{unique_id}] DebugExercise saved successfully.")
        else:
            logging.warning(f"[{unique_id}] Bug injection workflow did not create exercise.")

    except Exception as e:
        logging.error(f"[{unique_id}] Error in automated debug generation: {e}")
        logging.error(traceback.format_exc())
