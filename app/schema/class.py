from pydantic import BaseModel, Field


class ClassProfile(BaseModel):
    id:int = Field(...)
    grade:str = Field(description="年级")
    student_count:int = Field(...)
    academic_level:str = Field(description="整体学情")
    study_status:list[str] = Field(...)