from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..services.tech_stack_service import get_all_techstacks, get_techstack_by_name, get_topics_of_techstack

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

