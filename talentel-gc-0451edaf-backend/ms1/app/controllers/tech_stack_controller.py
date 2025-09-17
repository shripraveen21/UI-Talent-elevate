from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..services.tech_stack_service import get_all_techstacks, get_techstack_by_name, get_topics_of_techstack, save_selected_topics
from typing import Dict, Any
from ..models.models import Employee
from ..schemas.schemas import TechStackRequest
from ..services.rbac_service import RBACService
from ..utils.email import send_tech_stack_request_email


router = APIRouter()

@router.get('/tech-stacks')
def get_tech_stacks(db:Session = Depends(get_db)):
    tech_stacks = get_all_techstacks(db=db)
    return tech_stacks


@router.get('/tech-stacks/{tech_stack_name}')
def get_tech_stack_by_name(
        tech_stack_name: str, db: Session = Depends(get_db)
):
    tech_stack = get_techstack_by_name(name=tech_stack_name, db=db)
    return tech_stack

@router.get('/topics/{tech_stack_name}')
def get_topics_by_techstack_name(
        tech_stack_name: str,
        difficulty: str = None,
        db: Session = Depends(get_db),
):
    print(f'Fetching topics for: {tech_stack_name}')
    topics = get_topics_of_techstack(
        techstack_name=tech_stack_name,
        difficulty_level=difficulty,
        db=db
    )
    return topics

@router.post('/topics/save-selected')
def save_selected_topics_endpoint(
    topics_data: Dict[str, Any],
    db: Session = Depends(get_db),
    curr_user = Depends(RBACService.get_current_user)
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
        print(topics_data, curr_user)
        curr_user_id = db.query(Employee.user_id).filter(
            Employee.email==curr_user.get('sub')
        ).scalar()
        if not curr_user_id:
            raise HTTPException(404, detail="User not found")
        result = save_selected_topics(db=db, topics_data=topics_data, user_id=curr_user_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@router.post('/request/techstack')
def create_tech_stack_request(
        tech_stack_payload: TechStackRequest,
        db: Session = Depends(get_db),
        curr_user = Depends(RBACService.get_current_user),
):

    user = db.query(Employee).filter_by(email=curr_user.get('sub')).first()
    if not user:
        raise HTTPException(status_code=401, detail='Not Allowed')

    existing_tech_stack = get_techstack_by_name(db=db, name=tech_stack_payload.name)
    if existing_tech_stack:
        raise HTTPException(status_code=400, detail='TechStack already exists')

    send = send_tech_stack_request_email(
        db=db, tech_stack=tech_stack_payload, user=curr_user,
        description=tech_stack_payload.description,
    )
    if not send:
        raise HTTPException(status_code=500, detail='Unable to send email')

    return {
        "message": "Request sent successfully",
    }

