from langchain_core.prompts import ChatPromptTemplate

CLARIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一个教学作业需求澄清助手。

目标：
- 通过多轮对话逐步澄清作业生成需求
- 信息不足时有针对性追问
- 信息足够时提示可以生成需求确认文档
"""),
    ("human", "{history}"),
    ("human", "{input}")
])


SUMMARY_PROMPT = """
请根据以上对话，产出两份内容：

1) REQUEST_JSON：
- 用于作业生成的结构化请求
- 缺失字段填 null
- 字段仅限：
  subject, topic, num_questions, target_difficulty,
  target_categories, cognitive_distribution, required_context, purpose

2) CONFIRM_MD：
- 一份用户可阅读/可编辑的 Markdown 需求确认文档
- 内容必须覆盖 REQUEST_JSON，且可以更详细
- 允许加入必要的解释与约束（例如注意事项、学情背景）
- 不能与 REQUEST_JSON 冲突

严格按以下格式输出，不要输出任何其它内容：

===REQUEST_JSON===
{...}
===CONFIRM_MD===
...
"""
