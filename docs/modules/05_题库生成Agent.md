# 05. 题库生成 Agent

**文件**: `app/ai/langchain/agents/ExerciseAgent.py`

## 职责概述

使用 LangChain Agent 框架生成习题题库，支持：
- 批量生成多种题型（选择题、填空题、解答题）
- 控制难度和数量
- 生成解析和答案

## 核心流程

```
clarify_chat (多轮对话收集需求)
         ↓
clarify_confirm (用户确认)
         ↓
exercise_agent.invoke(payload)
         ↓
exercise_parser.parse(result["output"])
         ↓
save_exercise_set (落库)
```

## 支持的题型

| 题型 | 说明 |
|------|------|
| `choice` | 选择题（含选项和答案） |
| `fill` | 填空题 |
| `解答` | 解答题（含解题步骤） |

## 请求参数

```python
payload = {
    "subject": "数学",
    "knowledge_point": "二次函数",
    "difficulty": "medium",  # easy / medium / hard
    "count": 5,
    "exercise_types": ["choice", "fill"],
    "confirm_md_final": "确认生成5道中等难度选择题"
}
```

## 输出格式

```python
ExerciseSet:
  title: str           # 题库标题
  subject: str         # 学科
  overall_difficulty: str
  exercises: List[Exercise]
      Exercise:
          type: str
          question: str
          options: List[str]  # 选择题
          answer: str
          explanation: str
          difficulty: str
          knowledge_point: str
```

## Agent 架构

```python
exercise_agent, exercise_parser = build_exercise_agent()
```

- `exercise_agent`：LangChain Agent，负责与 LLM 交互
- `exercise_parser`：输出解析器，将 LLM 原始输出解析为结构化数据
