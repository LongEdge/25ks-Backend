# app/schemas/exercise.py
from datetime import datetime

from pydantic import BaseModel, Field, conint, conlist
from typing import List, Literal, Optional

# 定义题型枚举，提高代码可读性和约束性
ExerciseCategory = Literal["选择题", "填空题", "简答题", "判断题", "计算题"]
DifficultyLevel = Literal["基础", "中等", "困难", "挑战"]


class ExerciseItem(BaseModel):
    """
    一个包含详细教学元数据的结构化练习题。
    """
    # --- 题目核心内容 ---

    question_id: str = Field(..., description="系统内部的唯一标识或题目序号（从1开始）")
    question_text: str = Field(..., description="练习题的完整题目内容")

    # --- 题型和选项 ---

    category: ExerciseCategory = Field(..., description="题目的具体类型，例如选择题、简答题等")
    options: Optional[List[str]] = Field(None,
                                         description="如果题目是选择题或判断题，提供选项列表（A, B, C, D等），否则为 None")
    score: float = Field(..., description="题目分数")


    # --- 答案与解析 ---

    correct_answer: str = Field(..., description="题目的标准正确答案，选择题为选项序号，简答题为核心知识点或步骤")
    answer_analysis: str = Field(..., description="详细的答案解析，解释考点、解题思路和步骤")

    # --- 教学元数据 ---

    subject: str = Field(..., description="与题目相关的主要学科或知识领域（如：物理、化学、生物等）")
    topic: str = Field(..., description="题目所属的主要主题或子主题（如：牛顿第一定律、向量运算等）")

    difficulty: DifficultyLevel = Field(..., description="题目在教学中的难度分级")
    knowledge_tags: List[str] = Field(...,
                                      description="与题目直接关联的核心知识点标签（如：牛顿第一定律、惯性、匀速直线运动）")
    required_context: Optional[str] = Field(None, description="生成此题时所依据的知识库内容（可选，用于教师回顾）")

    # --- 潜在扩展 ---
    suggested_time_minutes: Optional[int] = Field(None, description="建议学生完成此题所需的时间（分钟）")


class ExamExample(BaseModel):
    """
    一个完整的、包含教学和管理元数据的生成的习题试卷。
    """
    # --- 试卷基本标识与主题 ---

    exam_id: str = Field(..., description="系统内部的唯一标识或试卷序号")
    title: str = Field(..., description="试卷的名称或标题 (如：'高二物理期中测试卷')")
    subject: str = Field(..., description="学科（如：高二数学、初中化学）")
    total_score: float = Field(..., description="试卷的总分数")

    # --- 教学与架构元数据（新增/强化） ---

    difficulty_overall: DifficultyLevel = Field("中等",
                                                description="试卷整体的难度分级，用于快速筛选")
    exercise_count: int = Field(..., description="试卷中题目的总数量")
    generation_timestamp: datetime = Field(..., description="试卷的生成时间戳，精确到秒")
    generated_by: Optional[str] = Field("System AI", description="生成此试卷的系统或用户的标识")

    # --- 业务/使用上下文（新增） ---
    purpose: Optional[str] = Field(None, description="此试卷的用途（如：'单元测试'、'考前复习'）")
    required_knowledge_coverage: List[str] = Field(...,
                                                description="试卷要求覆盖的所有知识点大纲或标签列表")

    # --- 核心内容 ---
    exercises: List[ExerciseItem] = Field(..., description="试卷包含的练习题列表")


# 接上文继续定义 ExerciseRequest 类

class ExerciseRequest(BaseModel):
    """
    定义了用户请求 AI 或系统生成一套练习题时必须提供的参数和约束条件。
    """

    # --- 核心要求（必需） ---

    subject: str = Field(...,
                         min_length=2,
                         description="请求生成的题目所属学科（如：高二物理、初中数学）")

    topic: str = Field(...,
                       min_length=5,
                       description="请求生成题目的主要主题或知识点范围（如：电磁感应、一元二次方程）")

    # --- 数量和难度约束（必需，使用 Pydantic 约束） ---

    num_questions: conint(ge=1, le=50) = Field(10,
                                               description="请求生成的题目总数，范围限制在 1 到 50 之间。")

    difficulty_target: DifficultyLevel = Field("中等",
                                               description="请求生成的试卷或题目集的整体目标难度等级。")

    # --- 知识库或上下文约束（最佳实践） ---

    # 架构经验谈：通常，题目的生成需要基于特定的上下文或知识库
    required_context: Optional[str] = Field(None,
                                            description="为生成内容提供的具体上下文或文本片段（用于 RAG 增强）。")

    # --- 题型细分约束（可选/细化） ---

    # 使用 conlist(min_length=1) 确保如果用户提供了这个字段，它至少包含一个元素
    target_categories: Optional[conlist(ExerciseCategory, min_length=1)] = Field(
        None,
        description="请求包含的题型列表。如果为 None，则由系统自由分配题型。"
    )

    # --- 高级/扩展约束（可选） ---

    # conint(ge=1) 确保指定时长不小于 1 分钟
    suggested_duration_minutes: Optional[conint(ge=1, le=180)] = Field(
        None,
        description="建议学生完成这套题目的总时长（分钟），用于辅助 AI 调整题目难度和复杂度。"
    )

    # 业务经验谈：这个字段通常用于追踪请求来源或调用者
    requestor_id: Optional[str] = Field(None, description="发起请求的用户或系统标识符。")