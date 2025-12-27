from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class LearningProfileModel(Base):
    __tablename__ = "learn_teacher_profile"

    id = Column(Integer, primary_key=True, index=True)

    teacher_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    title = Column(String(255), nullable=False, comment="学情名称")

    subject = Column(String(50), nullable=False)
    grade = Column(String(50), nullable=False)
    related_chapter = Column(String(255), nullable=True)

    profile_json = Column(
        Text,  # SQLite 用 TEXT，Postgres 可换 JSONB
        nullable=False,
        comment="LearningProfile 完整 JSON"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


