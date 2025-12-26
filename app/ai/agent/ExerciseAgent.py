"""
作业服务Agent，进行作业任务
1、和用户对话，得知用户意图，填充System_prompt2
2、请用户确认意图（返回一遍system_prompt2)，确认是否修改
3、如果需要修改，跳转到第一步，如果不需要修改，请用户输入额外提示
4、调用RAG增强检索和知识图谱搜索
5、校验格式
"""
from app.ai.agent.base import BaseAgent
from app.ai.tools import TOOLS_REGISTRY

def run_tool(tool_name: str, arguments: dict):
    if tool_name not in TOOLS_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOLS_REGISTRY[tool_name](**arguments)

class ExerciseAgent(BaseAgent):
    def __init__(self,llm,tools):
        super().__init__()
        self.llm=llm
        self.tools=tools or TOOLS_REGISTRY

    def run(self, user_input: str) -> str:
        messages = self.memory.build_messages(user_input)

        while True:
            response = self.llm.chat(messages, tools=self.tools.schemas)

            if response.is_tool_call:
                result = self.tools.execute(response)
                messages.append(result)
            elif response.is_exit:
                return response.content
