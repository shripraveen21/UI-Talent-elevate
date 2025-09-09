from pydantic import BaseModel

class TopicCreate(BaseModel):
    name: str
    description:str # Or use an Enum if you have one

class TopicOut(BaseModel):
    topic_id:int
    name: str
    description:str

    class Config:
        orm_mode = True

class TopicRead(BaseModel):
    topic_id: int

    class Config:
        orm_mode = True