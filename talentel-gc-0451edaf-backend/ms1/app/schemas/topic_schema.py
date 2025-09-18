from typing import List
from pydantic import BaseModel
from ..models.models import DifficultyLevel

class TopicCreate(BaseModel):
    name: str
    difficulty: DifficultyLevel  # Use your Enum for validation
    tech_stack_id: int

class Topic(BaseModel):
    name: str
    difficulty: DifficultyLevel

class TopicsCreateRequest(BaseModel):
    tech_stack: str
    topics: List[Topic]

class TopicOut(BaseModel):
    topic_id: int
    name: str
    difficulty: DifficultyLevel
    tech_stack_id: int

    class Config:
        orm_mode = True

class TopicRead(BaseModel):
    topic_id: int

    class Config:
        orm_mode = True