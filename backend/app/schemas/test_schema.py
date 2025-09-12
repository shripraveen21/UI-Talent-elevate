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
    quiz_id: int
    debug_test_id: int
    
class TestOut(BaseModel):
    test_id: int
    name: str
    topic_id: int
    difficulty_id: int
    test_type: TestTypeEnum
    title: str
    created_date: str
    quiz_data: Optional[Any]
    handson_data: Optional[Any]
    debug_data: Optional[Any]

    class Config:
        from_attributes = True

class TestOut(BaseModel):
    id: int
    test_name: str
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
    created_from: Optional[datetime.date] = None
    created_to: Optional[datetime.date] = None
    page: int = 1
    page_size: int = 10

class AssignTestRequest(BaseModel):
    user_ids: List[int]
    test_id: int
    due_date: Optional[datetime.date] = None
    assigned_by: Optional[int] = None
