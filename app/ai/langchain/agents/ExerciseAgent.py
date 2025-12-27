from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.ai.langchain.prompts.EXERCISE import SYSTEM_PROMPT, SYSTEM_PROMPT2_WITH_MD
from app.ai.langchain.schema.exercise import ExerciseSet
from app.ai.langchain.tools.kg import KG_TOOLS
from app.ai.langchain.tools.rag_zhipu import zhipu_rag_search
from app.core.config import settings
import uuid


def build_exercise_agent():
    llm = ChatZhipuAI(model="glm-4-flashx-250414", temperature=0.3,zhipuai_api_key=settings.AI_API_KEY)

    parser = PydanticOutputParser(pydantic_object=ExerciseSet)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", SYSTEM_PROMPT2_WITH_MD),
        ("assistant", "{format_instructions}"),
        ("placeholder", "{agent_scratchpad}")
    ]).partial(format_instructions=parser.get_format_instructions())

    # 修复工具列表拼接问题
    tools = KG_TOOLS + [zhipu_rag_search]

    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    )

    return executor, parser