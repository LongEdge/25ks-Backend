from pydantic import Field
from sqlalchemy import Column, String, Boolean, Integer,JSON
from app.models.base import BaseModel

class ClassModel(BaseModel):
    __tablename__="class"
    class_id:int = Column(Integer,primary_key=True,autoincrement=True)
    class_name:str = Column(String,nullable=False,index=True,unique=True,comment="班级名")
    class_year:int = Column(Integer,nullable=False,index=True,comment="<UNK>")
    teacher_name:str = Column(String,nullable=False,index=True,comment="<UNK>")
    study_status:str=Column(JSON,nullable=False,index=True,comment="<UNK>")
    