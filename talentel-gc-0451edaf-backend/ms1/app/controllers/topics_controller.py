from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..schemas.topic_schema import TopicCreate, TopicOut
from ..services.topics_service import create_topic, get_all_topics, get_topic_by_id
from ..services.tech_stack_service import save_selected_topics
from ..models.models import RoleEnum, Employee, Collaborator
from ..config.database import get_db

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.rbac_service import RBACService

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

@router.post("/topics/save-selected")
def save_selected_topics_endpoint(
    topics_data: Dict[str, Any],
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    # Use same permission logic for saving selected topics
    require_topic_permission(db, credentials)
    try:
        result = save_selected_topics(db=db, topics_data=topics_data)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
