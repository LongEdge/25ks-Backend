import json
from sqlalchemy.orm import Session

from app.ai.langchain.schema.learning_profiles import LearningProfilesSet, LearningProfile
from app.models.learning_profiles_model import LearningProfileModel
from app.models.user import User
from app.schema.learning_profiles_schema import LearningProfileCreate


def create_learning_profile(
    db: Session,
    teacher_id: int,
    data: LearningProfileCreate
):
    profile = LearningProfileModel(
        teacher_id=teacher_id,
        title=data.title,
        subject=data.profile.scope.subject,
        grade=data.profile.scope.grade,
        related_chapter=data.profile.scope.related_chapter,
        profile_json=data.profile.model_dump_json()
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def list_learning_profiles(db: Session, teacher_id: int):
    return (
        db.query(LearningProfileModel)
        .filter(LearningProfileModel.teacher_id == teacher_id)
        .order_by(LearningProfileModel.updated_at.desc())
        .all()
    )

def get_learning_profile(db: Session, profile_id: int, teacher_id: int):
    return (
        db.query(LearningProfileModel)
        .filter(
            LearningProfileModel.id == profile_id,
            LearningProfileModel.teacher_id == teacher_id
        )
        .first()
    )

def update_learning_profile(
    db: Session,
    profile_id: int,
    teacher_id: int,
    data: LearningProfileCreate
):
    profile = get_learning_profile(db, profile_id, teacher_id)
    if not profile:
        return None

    profile.title = data.title
    profile.subject = data.profile.scope.subject
    profile.grade = data.profile.scope.grade
    profile.related_chapter = data.profile.scope.related_chapter
    profile.profile_json = data.profile.model_dump_json()

    db.commit()
    db.refresh(profile)
    return profile

def delete_learning_profile(db: Session, profile_id: int, teacher_id: int):
    profile = get_learning_profile(db, profile_id, teacher_id)
    if not profile:
        return False

    db.delete(profile)
    db.commit()
    return True

def get_LA(db: Session, teacher:User,msg:str):
    from app.ai.langchain.agents.LearnAnalysisAgent import get_LA_chain
    chain=get_LA_chain(db, teacher)
    result=chain.invoke({"input":msg})
    return result

def build_learning_profiles_set(
    db: Session,
    teacher_id: int
) -> LearningProfilesSet:
    models = list_learning_profiles(db=db, teacher_id=teacher_id)

    learning_profiles = [
        LearningProfile.model_validate_json(m.profile_json)
        for m in models
    ]

    return LearningProfilesSet(
        teacher_id=str(teacher_id),
        lps=learning_profiles
    )

