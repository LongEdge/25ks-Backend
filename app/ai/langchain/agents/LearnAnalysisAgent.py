import json

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user
from sqlalchemy.testing import db

from app.ai.langchain.prompts.LPS import SYSTEM_PROMPT
from app.ai.langchain.utils.utils import escape_curly_braces
from app.core.config import settings
from app.models.user import User
from app.service.learning_profile import build_learning_profiles_set

def get_learning_profiles(db: Session, current_user: User)->str:
    # profiles = list_learning_profiles(db=db, teacher_id=current_user.id)
    profile_set = build_learning_profiles_set(db, current_user.id)
    # profiles=profiles.model_dump_json()
    profiles_json = json.dumps(profile_set.model_dump(), ensure_ascii=False, default=str)
    teacher_id=current_user.id
    return f"""
        "teacher_id": {teacher_id},
        "profiles": {profiles_json}
    """


def get_LA_chain(db: Session, current_user: User):
    llm = ChatZhipuAI(
        model="glm-4-flash",
        temperature=0.8,
        zhipuai_api_key=settings.ZHIPU_API_KEY or settings.AI_API_KEY,
        max_tokens=128000,
    )

    user_learn_profiles = get_learning_profiles(db, current_user)
    user_learn_profiles=escape_curly_braces(user_learn_profiles)

    # 创建普通的对话链
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", user_learn_profiles),
        MessagesPlaceholder(variable_name="history", optional=True),  # 如果需要历史记录
        ("human", "{input}"),  # 用户输入
    ])

    chain = prompt | llm

    return chain


def build_learning_analysis_tool(db: Session, current_user: User) -> Tool:
    def _learning_analysis(input: str) -> str:
        chain = get_LA_chain(db, current_user)
        result = chain.invoke({
            "input": input,
            "history": []
        })
        return result.content

    return Tool(
        name="learning_analysis",
        description="基于教师的学情画像进行学习情况分析与回答",
        func=_learning_analysis,
    )
