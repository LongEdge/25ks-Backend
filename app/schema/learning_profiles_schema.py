
from pydantic import BaseModel

from app.ai.langchain.schema.learning_profiles import LearningProfile


class LearningProfileCreate(BaseModel):
    title: str
    profile: LearningProfile

class LearningProfileOut(BaseModel):
    id: int
    title: str
    subject: str
    grade: str
    related_chapter: str | None
    profile: LearningProfile

    class Config:
        from_attributes = True
