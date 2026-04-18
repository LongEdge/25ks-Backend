# 03. 教案生成 Prompt 模板

**文件**: `app/ai/langchain/prompts/LESSON.py` (待读)

## 职责概述

提供各生成阶段的 Prompt 模板，供 Orchestrator 调用 `get_section_prompt(stage)` 获取。

## 模板结构

每个章节的 Prompt 包含：

1. **System Prompt**：设定 AI 角色（经验丰富的教师）
2. **User Prompt**：包含课题信息、学情、已有内容

## 章节 Prompt 要素

| 章节 | Prompt 包含 |
|------|------------|
| `objectives` | 三维目标（知识与技能、过程与方法、情感态度价值观） |
| `key_points` | 教学重点、教学难点 |
| `teaching_flow.introduction` | 导入方式设计 |
| `teaching_flow.main` | 新授环节完整流程 |
| `teaching_flow.practice` | 课堂练习设计 |
| `teaching_flow.summary` | 课堂小结方式 |
| `homework` | 分层作业设计 |
| `board_design` | 板书布局 |
| `remarks` | 教学反思要点 |

## Prompt 变量

```python
prompt_vars = {
    "subject": "数学",
    "grade": "初三",
    "lesson_title": "二次函数",
    "lesson_type": "新授课",
    "lesson_count": 2,
    "class_duration": 45,
    "section_title": "教学目标",
    "student_profile": "学情分析...",
    "partial_lesson": "已生成内容..."
}
```

## 设计原则

- **角色设定**：System Prompt 始终强调"经验丰富的教师"
- **few-shot**：可包含示例输出引导格式
- **格式控制**：要求输出 Markdown 格式，便于前端渲染
- **长度控制**：通过 `max_tokens` 约束输出长度
- **一致性**：通过低 `temperature=0.3` 保证同类型内容风格一致
