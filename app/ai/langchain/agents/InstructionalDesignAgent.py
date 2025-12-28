from typing import List

from langchain_community.chat_models import ChatZhipuAI
from langchain_core.tools import Tool

from app.core.config import settings


def build_exercise_agent(out_tools:List[Tool]):
    llm = ChatZhipuAI(model="glm-4-flashx-250414", temperature=0.3,zhipuai_api_key=settings.AI_API_KEY)

    parser = PydanticOutputParser(pydantic_object=ExerciseSet)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", SYSTEM_PROMPT2_WITH_MD),
        ("assistant", "{format_instructions}"),
        ("placeholder", "{agent_scratchpad}")
    ]).partial(format_instructions=parser.get_format_instructions())

    # 修复工具列表拼接问题
    tools = KG_TOOLS + [zhipu_rag_search]+out_tools

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