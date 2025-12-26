from pydantic import BaseModel, Field



class TeacherResponse(BaseModel):
    name:str
    email:str

class TeacherCreate(BaseModel):
    """
    教师基本信息、教师画像
    """
    name: str = Field(
        description="姓名",
    )
    email: str = Field(
        description="电子邮箱",
    )
    subject :str= Field(
        description="教学课程",
    )
    teaching_style :list[str] = Field(
        description="教学风格",
        examples=["探究","严肃"]
    )
    personal_desc:str = Field(
        description="个人简介",
    )
