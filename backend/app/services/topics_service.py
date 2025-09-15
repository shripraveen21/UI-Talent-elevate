from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.models import Topic, RoleEnum

def create_topic(db: Session, user_payload, topic_data):
    new_topic = Topic(
        name=topic_data.name,
        difficulty=topic_data.difficulty,
        tech_stack_id=topic_data.tech_stack_id
    )
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    return new_topic

def get_all_topics(db: Session):
    return db.query(Topic).all()

def get_topic_by_id(db: Session, topic_id: int):
    topic = db.query(Topic).filter_by(topic_id=topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
