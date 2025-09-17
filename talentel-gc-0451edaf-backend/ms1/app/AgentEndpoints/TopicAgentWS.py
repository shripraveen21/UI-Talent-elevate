import os
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from ..models.models import TechStack, Topic, RoleEnum, Employee, DifficultyLevel
from ..config.database import get_db
from ..Agents.TopicGenAgent import TopicGenerationSystem  # Your multi-agent system
from ..schemas.topic_schema import TopicsCreateRequest
from ..services.auth_service import JWT_SECRET
from ..services.rbac_service import require_roles

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/techstack/store")
def store_tech_stack(
    tech_stack: TopicsCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        # 1. Check if tech stack already exists by name
        db_tech_stack = db.query(TechStack).filter(TechStack.name == tech_stack.name).first()
        if not db_tech_stack:
            # If not, create it
            db_tech_stack = TechStack(
                name=tech_stack.name,
                description=tech_stack.description,
                created_by=1
            )
            db.add(db_tech_stack)
            db.commit()
            db.refresh(db_tech_stack)

        # 2. Add only new topics for this tech stack
        added_topics = []
        for topic in tech_stack.topics:
            # Check if topic already exists for this tech stack (by name and tech_stack_id)
            exists = db.query(Topic).filter(
                Topic.name == topic.name,
                Topic.tech_stack_id == db_tech_stack.id
            ).first()
            if not exists:
                db_topic = Topic(
                    name=topic.name,
                    description=topic.description,
                    difficulty=topic.difficulty,
                    tech_stack_id=db_tech_stack.id
                )
                db.add(db_topic)
                added_topics.append(topic.name)
        db.commit()

        return {
            "success": True,
            "tech_stack_id": db_tech_stack.id,
            "added_topics": added_topics
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store tech stack: {str(e)}")

@router.websocket("/ws/topic-generation")
async def topic_generation_review(
        websocket: WebSocket,
        db: Session = Depends(get_db)
):
    await websocket.accept()
    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_json({"type": "error", "content": "Missing token"})
        await websocket.close()
        return

    try:
        user_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        await websocket.send_json({"type": "error", "content": "Invalid or expired token"})
        await websocket.close()
        return

    email = user_payload.get("sub")
    role = user_payload.get("role")
    if not email or not role:
        await websocket.send_json({"type": "error", "content": "Invalid token payload"})
        await websocket.close()
        return

    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        await websocket.send_json({"type": "error", "content": "User not found"})
        await websocket.close()
        return

    if str(user.role.value) != RoleEnum.CapabilityLeader.value and str(user.role) != RoleEnum.CapabilityLeader.name:
        await websocket.send_json({"type": "error", "content": "Unauthorized"})
        await websocket.close()
        return

    user_id = user.user_id

    try:
        # Step 1: Receive tech stack input
        data = await websocket.receive_json()
        tech_stack_name = data.get("name")
        created_by = user_id

        if not tech_stack_name or not created_by:
            await websocket.send_json({"type": "error", "content": "Missing tech stack name or creator."})
            await websocket.close()
            return

        # Step 2: Setup TopicGenerationSystem
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        topic_system = TopicGenerationSystem(model_client)

        # Step 3: Generate initial topics
        concepts = await topic_system.generate_concepts(tech_stack_name)
        iteration = 0
        max_iterations = 3

        while iteration < max_iterations:
            # Send topics to frontend for review
            await websocket.send_json({
                "type": "review",
                "content": concepts,
                "iteration": iteration + 1
            })

            # Wait for user decision
            user_decision_msg = await websocket.receive_json()
            user_decision = user_decision_msg.get("decision", "").strip().upper()
            user_feedback = user_decision_msg.get("feedback", "")

            if user_decision == "APPROVE":
                # Don't automatically save topics here - let the frontend handle saving only selected topics
                # Just send the final message with the generated concepts
                await websocket.send_json({
                    "type": "final",
                    "content": {"topics": concepts}
                })
                await model_client.close()
                await websocket.close()
                return

            elif user_decision == "REJECT":
                concepts = await topic_system.generate_concepts(tech_stack_name)
                iteration = 0

            elif user_decision == "REFINE":
                concepts = await topic_system.refine_concepts(concepts, "Please improve the topic list.")

            elif user_decision.startswith("FEEDBACK"):
                specific_feedback = user_feedback or user_decision.replace("FEEDBACK:", "").strip()
                print(f"FEEDBACK received: {specific_feedback}")
                concepts = await topic_system.refine_concepts(concepts, specific_feedback)
                print(f"Refined concepts: {json.dumps(concepts, indent=2)}")

            else:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid decision. Please send APPROVE, REJECT, REFINE, or FEEDBACK."
                })
                continue

            iteration += 1

        # Max iterations reached, send current version
        await websocket.send_json({
            "type": "final",
            "content": concepts
        })
        await model_client.close()
        await websocket.close()

    except WebSocketDisconnect:
        logger.info("Client disconnected during topic generation review")
    except Exception as e:
        logger.error(f"Error in /ws/topic-generation: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
        await websocket.close()
