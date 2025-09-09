from typing import Optional
from sqlalchemy.orm import Session
from ..models.models import TechStack, DifficultyLevel, Topic


def get_all_techstacks(db: Session):
    return db.query(TechStack).all()

def get_techstack_by_name(db: Session, name: str):
    return db.query(TechStack).filter(TechStack.name == name).first()

def get_topics_of_techstack(db: Session, techstack_name: str, difficulty_level: Optional[DifficultyLevel]):
    techstack = get_techstack_by_name(db=db, name=techstack_name)
    if difficulty_level is not None:
        return db.query(Topic).filter(Topic.difficulty == difficulty_level).all()

    return db.query(Topic).filter(Topic.tech_stack_id == techstack.id).all()

