from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..models.models import TechStack, DifficultyLevel, Topic
from fastapi import HTTPException


def get_all_techstacks(db: Session):
    return db.query(TechStack).all()

def get_techstack_by_name(db: Session, name: str):
    return db.query(TechStack).filter(TechStack.name == name).first()

def get_topics_of_techstack(db: Session, techstack_name: str, difficulty_level: Optional[DifficultyLevel]):
    techstack = get_techstack_by_name(db=db, name=techstack_name)
    if difficulty_level is not None:
        return db.query(Topic).filter(Topic.difficulty == difficulty_level).all()

    return db.query(Topic).filter(Topic.tech_stack_id == techstack.id).all()

def save_selected_topics(db: Session, topics_data: Dict[str, Any], user_id):
    """
    Save selected topics to the database.
    This function creates new Topic entries for the selected topics.
    """
    try:
        # Get or create tech stack
        tech_stack_name = topics_data.get('topicName')
        if not tech_stack_name:
            raise HTTPException(status_code=400, detail="Tech stack name is required")
        
        tech_stack = get_techstack_by_name(db=db, name=tech_stack_name)
        created_by = topics_data.get('created_by')
        if not tech_stack:
            # Create new tech stack if it doesn't exist
            tech_stack = TechStack(name=tech_stack_name, created_by=user_id)
            db.add(tech_stack)
            db.commit()
            db.refresh(tech_stack)
        else:
            # If tech stack exists and created_by is missing, update it
            if not tech_stack.created_by and created_by:
                tech_stack.created_by = created_by
                db.commit()
        
        selected_topics = topics_data.get('selectedTopics', [])
        if not selected_topics:
            raise HTTPException(status_code=400, detail="No topics selected")
        
        saved_topics = []
        skipped_topics = []
        
        for topic_data in selected_topics:
            # Check if topic already exists
            existing_topic = db.query(Topic).filter(
                Topic.name == topic_data['name'],
                Topic.tech_stack_id == tech_stack.id,
                Topic.difficulty == DifficultyLevel(topic_data['level'])
            ).first()
            
            if not existing_topic:
                # Create new topic
                new_topic = Topic(
                    name=topic_data['name'],
                    difficulty=DifficultyLevel(topic_data['level']),
                    tech_stack_id=tech_stack.id
                )
                db.add(new_topic)
                saved_topics.append(new_topic)
            else:
                skipped_topics.append(topic_data['name'])
        
        db.commit()
        
        # Refresh all saved topics to get their IDs
        for topic in saved_topics:
            db.refresh(topic)
   
        return {
            "success": True,
            "message": f"Successfully saved {len(saved_topics)} new topics",
            "tech_stack_id": tech_stack.id,
            "saved_topics_count": len(saved_topics),
            "total_selected": len(selected_topics),
            "skipped_topics": skipped_topics
        }
        
    except Exception as e:
        db.rollback()
        print(f"[tech_stack_service] Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save topics: {str(e)}")
