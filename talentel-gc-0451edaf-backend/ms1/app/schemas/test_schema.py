import datetime
from pydantic import BaseModel
from typing import List, Optional, Any
from enum import Enum

class TestTypeEnum(str, Enum):
    quiz = "quiz"
    handson = "handson"
    debug = "debug"

class QuizQuestion(BaseModel):
    question_text: str
    options: List[str]
    answer: str

class QuizDataIn(BaseModel):
    questions: List[QuizQuestion]

class HandsonDataIn(BaseModel):
    srd_document: bytes  # Should be base64-encoded in JSON

class DebugDataIn(BaseModel):
    prompt: Any
    solution: Any

class TestCreate(BaseModel):
    test_name: str
    description: str
    duration: int
    created_by : int
    quiz_id: Optional[int] = None
    debug_test_id: Optional[int] = None
    handson_test_id : Optional[int] = None

class TestOut(BaseModel):
    id: int
    test_name: str  # Maps to test_name in SQLAlchemy
    description: Optional[str] = None
    duration: Optional[int] = None
    created_at: datetime
    created_by: int
    quiz_id: Optional[int] = None
    debug_test_id: Optional[int] = None
 
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class TestFilter(BaseModel):
    search: Optional[str] = None
    page: int = 1
    page_size: int = 10

class AssignTestRequest(BaseModel):
    user_ids: List[int]
    test_id: int
    due_date: Optional[datetime.date] = None

class SkillUpgradeRequest(BaseModel):
    tech_stack: str
    level: str
