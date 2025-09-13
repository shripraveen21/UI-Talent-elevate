from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.topic_schema import TopicCreate, TopicOut
from ..services.topics_service import create_topic, get_all_topics, get_topic_by_id
from ..services.tech_stack_service import save_selected_topics
from ..services.rbac_service import require_roles
from ..models.models import RoleEnum
from ..config.database import get_db  # Assumes you have a get_db dependency

router = APIRouter(tags=["topics"])

@router.post("/topics/")
def api_create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db),
    user_payload=Depends(require_roles(RoleEnum.CapabilityLeader))
):
    # Only CapabilityLeader can create topics
    return create_topic(db, user_payload, topic_data)

@router.get("/topics/", response_model=List[TopicOut])
def get_topics_endpoint(
    db: Session = Depends(get_db),
    user_payload=Depends(require_roles(RoleEnum.CapabilityLeader, RoleEnum.ProductManager))
):
    return get_all_topics(db)

@router.get("/topics/{topic_id}/", response_model=TopicOut)
def get_topic_by_id_endpoint(
    topic_id: int,
    db: Session = Depends(get_db),
    user_payload=Depends(require_roles(RoleEnum.CapabilityLeader, RoleEnum.ProductManager))
):
    return get_topic_by_id(db, topic_id)

@router.post("/topics/save-selected")
def save_selected_topics_endpoint(
    topics_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Save selected topics to the database.
    Expected payload structure:
    {
        "topicName": "React",
        "description": "Frontend framework topics",
        "selectedTopics": [
            {"name": "Components", "level": "beginner"},
            {"name": "Hooks", "level": "intermediate"}
        ],
        "totalSelected": 2
    }
    """
    try:
        result = save_selected_topics(db=db, topics_data=topics_data)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")