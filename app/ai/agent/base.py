"""
Agent基类，RUN/STEP/LOOP
"""

class BaseAgent:
    def __init__(self, llm, tools, memory):
        self.llm = llm
        self.tools = tools
        self.memory = memory

    def run(self, user_input: str) -> str:
        raise NotImplementedError
