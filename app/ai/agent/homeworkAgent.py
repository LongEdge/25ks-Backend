"""
作业服务Agent，进行作业任务
"""
from app.ai.agent.base import BaseAgent


class TeachingAgent(BaseAgent):

    def run(self, user_input: str) -> str:
        messages = self.memory.build_messages(user_input)

        while True:
            response = self.llm.chat(messages, tools=self.tools.schemas)

            if response.is_tool_call:
                result = self.tools.execute(response)
                messages.append(result)
            elif response.is_exit:
                return response.content
