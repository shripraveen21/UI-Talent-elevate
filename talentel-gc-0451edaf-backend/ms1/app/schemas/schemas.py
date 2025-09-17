from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List, Any,Union, Literal

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    tech_stack: Optional[Dict] = None
    experience_level: int

class EmployeeLogin(BaseModel):
    email: EmailStr
    password: str

class EmployeeOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True

class CollaboratorOut(BaseModel):
    email: str
    topics: bool
    test_create: bool
    test_assign: bool

    class Config:
        orm_mode = True


class QuizParams(BaseModel):
    topics: List[int]
    duration: int
    tech_stack: int
    num_questions: int

class MCQQuestion(BaseModel):
    correctAnswer: Union[str, List[str]]  
    explanation: str
    options: Dict[str, str]  
    question: str
    topics:List[str]

class QuizCreate(BaseModel):
    params: QuizParams
    questions: Dict[str, MCQQuestion]

class DebugExerciseParams(BaseModel):
    topics: List[str]
    num_questions: int
    duration: int
    difficulty: str = "medium"

class DebugExerciseItem(BaseModel):
    id: str
    title: str
    description: str
    technology: str
    difficulty: str
    code: str
    expectedBehavior: str
    currentBehavior: str
    hints: Dict[str, str]
    solution: str
    explanation: str
    learningObjectives: List[str]
    tags: List[str]
    estimatedTime: int

class DebugExerciseMetadata(BaseModel):
    totalQuestions: int
    totalDuration: int
    difficultyDistribution: Dict[str, int]
    topics: List[str]
    topics: List[str]

class DebugExercisesPayload(BaseModel):
    exercises: List[DebugExerciseItem]
    metadata: DebugExerciseMetadata

class DebugExerciseCreate(BaseModel):
    tech_stack_id: Optional[int] = None
    topic_ids: Optional[List[int]] = None
    num_questions: Optional[int] = None
    duration: Optional[int] = None
    exercises: Any

    model_config = {'arbitrary_types_allowed': True}

class TopicCreate(BaseModel):
    name: str
    difficulty: Literal['beginner', 'intermediate', 'advanced']
    tech_stack_id: int
class TopicOut(BaseModel):
    topic_id: int
    name: str
    difficulty: str  # Enum will be serialized as string
    tech_stack_id: int

    class Config:
        orm_mode = True

class TechStackRequest(BaseModel):
    name: str
    description: Optional[str]

class TechStackCreate(BaseModel):
    name: str
    description: Optional[str] = None
    topics : List[TopicCreate]

class SuggestionCreate(BaseModel):
    collaborator_id: int
    capability_leader_id: int
    tech_stack_id: int
    message: str

class SuggestionOut(BaseModel):
    id: int
    collaborator_id: int
    capability_leader_id: int
    tech_stack_id: int
    message: str
    raised_at: datetime

    class Config:
        orm_mode = True

class SuggestionForLeaderOut(BaseModel):
    id: int
    collaborator_id: int
    collaborator_name: str
    tech_stack_id: int
    tech_stack_name: Optional[str]
    message: str
    raised_at: datetime

    class Config:
        orm_mode = True