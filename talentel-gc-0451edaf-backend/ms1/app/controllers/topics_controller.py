import os
from typing import List, Dict, Any

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..schemas.schemas import SuggestionCreate, SuggestionOut, SuggestionForLeaderOut
from ..schemas.topic_schema import TopicCreate, TopicOut
from ..services.topics_service import create_topic, get_all_topics, get_topic_by_id
from ..services.tech_stack_service import save_selected_topics
from ..models.models import RoleEnum, Employee, Collaborator, Topic, TechStack, Suggestion
from ..config.database import get_db
from ..Agents.TopicsFromPD import ProjectTechStackTopicAgent


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.rbac_service import RBACService
from ..models.models import Collaborator

router = APIRouter(tags=["topics"])
bearer_scheme = HTTPBearer()

def require_topic_permission(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    # Decode JWT and get user info
    payload = RBACService.get_current_user(credentials)
    email = payload.get("sub")
    role = payload.get("role")

    # Check if user is CapabilityLeader
    if role == RoleEnum.CapabilityLeader.value:
        return payload

    # Check if user is a Collaborator with topics permission
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    collab = db.query(Collaborator).filter(Collaborator.collaborator_id == user.user_id).first()
    if collab and collab.topics:
        return payload

    raise HTTPException(status_code=403, detail="No permission to create topics")

@router.post("/topics/")
def api_create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db),
    user_payload=Depends(require_topic_permission)
):
    # CapabilityLeader or Collaborator with topics permission can create topics
    return create_topic(db, user_payload, topic_data)

@router.get("/topics/by-leader-with-stack/{leader_id}", response_model=List[Dict[str, Any]])
def get_topics_with_stack_by_leader(
    leader_id: int,
    db: Session = Depends(get_db)
):
    # Get all tech stacks for the leader
    tech_stacks = db.query(TechStack).filter(TechStack.created_by == leader_id).all()
    tech_stack_ids = [ts.id for ts in tech_stacks]

    if not tech_stack_ids:
        return []

    # Get all topics for those tech stacks
    topics = db.query(Topic).filter(Topic.tech_stack_id.in_(tech_stack_ids)).all()

    # Build response: topic info + tech stack info
    result = []
    for topic in topics:
        stack = next((ts for ts in tech_stacks if ts.id == topic.tech_stack_id), None)
        result.append({
            "topic_id": topic.topic_id,
            "topic_name": topic.name,
            "difficulty": topic.difficulty,
            "tech_stack_id": topic.tech_stack_id,
            "tech_stack_name": stack.name if stack else None,
            "tech_stack_created_by": stack.created_by if stack else None,
        })
    return result

@router.get("/topics/", response_model=List[TopicOut])
def get_topics_endpoint(
    db: Session = Depends(get_db),
    user_payload=Depends(require_topic_permission)
):
    # Anyone with topic permission can view topics
    return get_all_topics(db)

@router.get("/topics/{topic_id}/", response_model=TopicOut)
def get_topic_by_id_endpoint(
    topic_id: int,
    db: Session = Depends(get_db),
    user_payload=Depends(require_topic_permission)
):
    return get_topic_by_id(db, topic_id)

@router.get("/topics/by-leader/{leader_id}", response_model=List[TopicOut])
def get_topics_by_leader(
    leader_id: int,
    db: Session = Depends(get_db)
):
    # 1. Get all tech_stack IDs created by this leader
    tech_stacks = db.query(TechStack).filter(TechStack.created_by == leader_id).all()
    tech_stack_ids = [ts.id for ts in tech_stacks]

    if not tech_stack_ids:
        return []  # No tech stacks, so no topics

    # 2. Get all topics for those tech stacks
    topics = db.query(Topic).filter(Topic.tech_stack_id.in_(tech_stack_ids)).all()
    return topics

@router.get("/topics/by-collaborator/{collaborator_id}", response_model=List[TopicOut])
def get_topics_by_collaborator(
    collaborator_id: int,
    db: Session = Depends(get_db),
    tech_stack_id: int = None
):
    # Get all collaborator records for this collaborator_id
    query = db.query(Collaborator).filter(Collaborator.collaborator_id == collaborator_id)
    if tech_stack_id:
        query = query.filter(Collaborator.tech_stack_id == tech_stack_id)
    collabs = query.all()
    if not collabs:
        return []
    # If tech_stack_id is provided, return topics for that stack only
    if tech_stack_id:
        topics = db.query(Topic).filter(Topic.tech_stack_id == tech_stack_id).all()
        return topics
    # Otherwise, return topics for all assigned tech stacks
    topics = []
    for collab in collabs:
        if collab.tech_stack_id:
            topics += db.query(Topic).filter(Topic.tech_stack_id == collab.tech_stack_id).all()
    return topics

@router.get("/tech-stacks/by-collaborator/{collaborator_id}", response_model=List[Dict[str, Any]])
def get_tech_stacks_by_collaborator(
    collaborator_id: int,
    db: Session = Depends(get_db)
):
    # Get all tech_stack_ids for this collaborator where topics permission is True
    collabs = db.query(Collaborator).filter(
        Collaborator.collaborator_id == collaborator_id,
        Collaborator.topics == True
    ).all()
    tech_stack_ids = [c.tech_stack_id for c in collabs if c.tech_stack_id]
    if not tech_stack_ids:
        return []
    tech_stacks = db.query(TechStack).filter(TechStack.id.in_(tech_stack_ids)).all()
    result = []
    for ts in tech_stacks:
        # Get capability leader name from Employee table
        leader = db.query(Employee).filter(Employee.user_id == ts.created_by).first()
        leader_name = leader.name if leader else None
        print(f"TechStack id={ts.id}, created_by={ts.created_by}, leader_name={leader_name}")
        result.append({
            "id": ts.id,
            "name": ts.name,
            "created_by": ts.created_by,
            "created_at": ts.created_at,
            "capability_leader_name": leader_name
        })
    return result

@router.get("/tech-stacks/id/{tech_stack_id}")
def get_tech_stack_by_id(
    tech_stack_id: int,
    db: Session = Depends(get_db)
):
    try:
        ts = db.query(TechStack).filter(TechStack.id == tech_stack_id).first()
        print("DEBUG: TechStack object:", ts)
        if not ts:
            return {}
        # Convert created_at to string if it's a datetime
        created_at = str(ts.created_at) if hasattr(ts.created_at, "isoformat") else ts.created_at
        return {
            "id": ts.id,
            "name": ts.name,
            "created_by": ts.created_by,
            "created_at": created_at
        }
    except Exception as e:
        print("ERROR in get_tech_stack_by_id:", e)
        return {"error": str(e)}

@router.post("/suggestion", response_model=SuggestionOut)
def create_suggestion(suggestion: SuggestionCreate, db: Session = Depends(get_db)):
    db_suggestion = Suggestion(
        collaborator_id=suggestion.collaborator_id,
        capability_leader_id=suggestion.capability_leader_id,
        tech_stack_id=suggestion.tech_stack_id,
        message=suggestion.message
    )
    db.add(db_suggestion)
    db.commit()
    db.refresh(db_suggestion)
    return db_suggestion

@router.get("/suggestions/for-leader/{leader_id}", response_model=List[SuggestionForLeaderOut])
def get_suggestions_for_leader(leader_id: int, db: Session = Depends(get_db)):
    suggestions = (
        db.query(Suggestion, Employee.name, TechStack.name)
        .join(Employee, Suggestion.collaborator_id == Employee.user_id)
        .join(TechStack, Suggestion.tech_stack_id == TechStack.id)
        .filter(Suggestion.capability_leader_id == leader_id)
        .order_by(Suggestion.raised_at.desc())
        .all()
    )
    return [
        SuggestionForLeaderOut(
            id=s.id,
            collaborator_id=s.collaborator_id,
            collaborator_name=collaborator_name,
            tech_stack_id=s.tech_stack_id,
            tech_stack_name=tech_stack_name,
            message=s.message,
            raised_at=s.raised_at
        )
        for s, collaborator_name, tech_stack_name in suggestions
    ]

@router.delete("/suggestion/{suggestion_id}")
def delete_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    db.delete(suggestion)
    db.commit()
    return {"detail": "Suggestion deleted"}


class PD(BaseModel):
    tech_stack: str
    description: str

@router.post("/topics-from-desc")
async def get_topics_from_desc(body: PD = Body(), db: Session = Depends(get_db)):
    try:
        desc = body.description
        tech_stack = body.tech_stack
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment="gpt-4.1",
            model="gpt-4.1",
            api_version="2024-06-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )

        agent = ProjectTechStackTopicAgent(model_client=model_client)
        topics = await agent.generate_topics(tech_stack, desc)
        return topics

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong")
