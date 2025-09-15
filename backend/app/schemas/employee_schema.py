from pydantic import BaseModel
from typing import List, Optional,Any

class EmployeeFilter(BaseModel):
    search: Optional[str] = None
    band: Optional[str] = None  # Use BandType Enum if you want stricter validation
    role: Optional[str] = None  # Use RoleEnum if you want stricter validation
    skills: Optional[List[str]] = None
    experience_level: Optional[str] = None
    page: int = 1
    page_size: int = 10

class EmployeeOut(BaseModel):
    user_id: int
    name: str
    email: str
    role: str  # Use RoleEnum if you want stricter validation
    band: str  # Use BandType if you want stricter validation
    tech_stack: Optional[Any] = None  # Use List[str] if always a list
    # skills: Optional[List[str]] = None
    experience_level: Optional[str] = None

    class Config:
        from_attributes = True