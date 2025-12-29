# -*- coding: utf-8 -*-
"""
教案生成 Prompts 定义

包含：
1. 澄清阶段 Prompts
2. 各章节生成 Prompts
"""
from langchain_core.prompts import ChatPromptTemplate


# ========== 教案澄清 Prompt（原有，保留） ==========

LESSON_CLARIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
**角色设定**：你是一位专业的教学设计师，擅长分析课程需求，准确识别教学要素。

**任务**：基于给定的课程信息（可能不完整），填充以下课程澄清模型的字段。

**字段填充规则**：
1.  **核心原则**：严格遵循字段描述，只填充**确信且合理**的信息。对于没有明确依据的字段，保持为`null`。
2.  **学科/年级推断**：仅当文本中明确出现或可从课程名称/内容中**无歧义推断**时，才填充`subject`和`grade`。
3.  **避免过度推测**：不要根据常识"捏造"信息。例如，不能因为看到"牛顿定律"就推断学科是"物理"，除非上下文支持。

**需要处理的原始课程信息**：
```
{在这里放置用户提供的描述}
```

**输出要求**：
1.  **格式**：输出一个完整的、格式正确的JSON对象，与以下JSON Schema严格匹配。
2.  **内容**：只输出JSON，**不要**有任何解释、开场白或总结。
3.  **空值处理**：无法确定的字段，其值必须为`null`。

**JSON Schema（你的输出必须符合此结构）**：
```json
{
  "subject": null,
  "grade": null,
  "lesson_title": null,
  "lesson_type": null,
  "class_duration": null,
  "lesson_count": null,
  "teaching_goal_focus": null,
  "difficulty_level": null,
  "exam_related": null,
  "curriculum_standard": null,
  "constraints": null,
  "notes": null
}
```

**开始处理**：现在，根据上面的规则，分析提供的课程信息并输出JSON。

目标：
- 通过多轮对话逐步澄清教案生成需求
- 信息不足时有针对性追问
- 信息足够时提示可以生成需求确认文档
- 如果用户表示确认或者你认为信息足够了，直接输出end，不要有任何其他内容
"""),
    ("human", "{history}"),
    ("human", "{input}")
])


# ========== 对话式澄清 Prompt（用于多轮对话） ==========

LESSON_CHAT_CLARIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位专业的教学设计助手，正在帮助教师准备教案。

**你的任务**：
通过自然对话，逐步收集以下信息来生成教案：
- 学科（必需）
- 年级（必需）
- 课题名称（必需）
- 课程类型（新授/复习/实验/综合）
- 课时长度和数量
- 教学侧重点
- 难度水平
- 其他特殊要求

**对话规则**：
1. 每次只问1-2个问题，不要一次问太多
2. 根据用户回答推断相关信息
3. 已确认的信息不要重复询问
4. 当核心信息（学科、年级、课题）都已收集，询问是否确认开始生成

**当前已收集的信息**：
{clarify_json}

**对话历史**：
{history}
"""),
    ("human", "{input}")
])


# ========== 各章节生成 Prompts ==========

SECTION_SYSTEM_BASE = """
你是一位经验丰富的{subject}{grade}教师，正在为课题《{lesson_title}》编写教案。

**课程信息**：
- 学科：{subject}
- 年级：{grade}
- 课题：{lesson_title}
- 课型：{lesson_type}
- 课时：{lesson_count}课时，每课时{class_duration}分钟

**学情分析**（如有）：
{student_profile}

**已生成的教案内容**：
{partial_lesson}

请根据以上信息，生成教案的【{section_title}】部分。
"""

# 教学目标 Prompt
OBJECTIVES_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请从以下三个维度撰写教学目标：
1. **知识与技能目标**：学生需要掌握的知识点和技能
2. **过程与方法目标**：学生在学习过程中需要运用的方法
3. **情感态度与价值观目标**：学生情感、态度、价值观方面的发展

格式要求：
- 使用 Markdown 格式
- 每个维度2-3条具体目标
- 目标要具体、可测量、可达成
"""),
    ("human", "请生成教学目标")
])

# 教学重难点 Prompt
KEY_POINTS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请分别列出本节课的教学重点和教学难点：

1. **教学重点**：本课最核心的知识点，是学生必须掌握的内容
2. **教学难点**：学生理解和掌握上可能存在困难的内容

格式要求：
- 使用 Markdown 格式
- 重点和难点各2-3条
- 说明为什么是重点/难点
"""),
    ("human", "请生成教学重难点")
])

# 导入新课 Prompt
INTRODUCTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请设计本节课的导入环节（约5分钟），包含：

1. **导入方式**：情境导入/问题导入/复习导入/故事导入等
2. **具体内容**：导入的具体话语或活动
3. **设计意图**：为什么这样设计，如何激发学生兴趣

格式要求：
- 使用 Markdown 格式
- 导入要新颖有趣，能吸引学生注意力
- 要自然过渡到新课内容
"""),
    ("human", "请生成导入新课环节")
])

# 新授环节 Prompt
MAIN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请设计本节课的新授环节（约25-30分钟），这是教学的核心部分。

内容应包含：
1. **知识讲解**：核心知识点的讲解顺序和方法
2. **师生互动**：设计的问题和预期的学生回答
3. **教学活动**：具体的教学活动安排
4. **板书设计提示**：关键内容的板书要点

格式要求：
- 使用 Markdown 格式
- 按教学步骤组织内容
- 包含教师活动和学生活动
- 注明每个环节的时间分配
"""),
    ("human", "请生成新授环节")
])

# 课堂练习 Prompt
PRACTICE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请设计本节课的课堂练习环节（约10分钟），包含：

1. **练习题目**：2-3道典型练习题，由易到难
2. **练习形式**：独立完成/小组讨论/互批互改等
3. **预期答案**：每道题的参考答案或评分要点
4. **错误分析**：常见错误及纠正方法

格式要求：
- 使用 Markdown 格式
- 练习要紧扣教学重点
- 难度要适中，体现分层
"""),
    ("human", "请生成课堂练习环节")
])

# 课堂小结 Prompt
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请设计本节课的小结环节（约3-5分钟），包含：

1. **知识梳理**：本节课核心知识点的归纳总结
2. **方法总结**：学习方法或思维方法的提炼
3. **拓展延伸**：与后续学习内容的联系

格式要求：
- 使用 Markdown 格式
- 简洁明了，突出重点
- 可以设计学生参与的小结方式
"""),
    ("human", "请生成课堂小结")
])

# 作业布置 Prompt
HOMEWORK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请设计本节课的课后作业，包含：

1. **必做作业**：全体学生必须完成的基础练习
2. **选做作业**：供学有余力的学生挑战
3. **预习任务**：下节课的预习要求（如有）

格式要求：
- 使用 Markdown 格式
- 作业量适中，约15-20分钟可完成
- 体现分层设计
"""),
    ("human", "请生成作业布置")
])

# 板书设计 Prompt
BOARD_DESIGN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请设计本节课的板书，要求：

1. **标题区**：课题名称
2. **主体区**：核心知识框架
3. **副板书区**：补充内容或学生回答

格式要求：
- 使用纯文本或简单符号表示布局
- 板书要简洁、清晰、有层次
- 突出重点和难点
"""),
    ("human", "请生成板书设计")
])

# 教学反思 Prompt
REMARKS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECTION_SYSTEM_BASE + """
**输出要求**：
请准备教学反思的框架，包含以下几个方面的思考点：

1. **教学效果**：目标达成情况的预判
2. **亮点设计**：本节课设计的创新点
3. **改进空间**：可能需要改进的地方
4. **学生反馈**：需要关注的学生反应

格式要求：
- 使用 Markdown 格式
- 提供思考框架，课后可填充具体内容
"""),
    ("human", "请生成教学反思框架")
])


# ========== Prompt 注册表 ==========

SECTION_PROMPTS = {
    "objectives": OBJECTIVES_PROMPT,
    "key_points": KEY_POINTS_PROMPT,
    "teaching_flow.introduction": INTRODUCTION_PROMPT,
    "teaching_flow.main": MAIN_PROMPT,
    "teaching_flow.practice": PRACTICE_PROMPT,
    "teaching_flow.summary": SUMMARY_PROMPT,
    "homework": HOMEWORK_PROMPT,
    "board_design": BOARD_DESIGN_PROMPT,
    "remarks": REMARKS_PROMPT,
}


def get_section_prompt(stage: str) -> ChatPromptTemplate:
    """获取指定章节的 Prompt"""
    if stage not in SECTION_PROMPTS:
        raise ValueError(f"未知的章节: {stage}")
    return SECTION_PROMPTS[stage]

