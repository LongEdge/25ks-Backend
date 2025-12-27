from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, conint, conlist, confloat

# ===== 教学语义枚举 =====

ExerciseCategory = Literal[
    "选择题",
    "填空题",
    "判断题",
    "简答题",
    "计算题",
    "综合题"
]

DifficultyLevel = Literal[
    "基础",
    "中等",
    "困难",
    "挑战"
]

CognitiveLevel = Literal[
    "记忆",
    "理解",
    "应用",
    "分析",
    "综合",
    "评价"
]


class ExerciseItem(BaseModel):
    """
    一道结构化的、可被自动生成 / 批改 / 分析的练习题。
    """

    # ===== 基本标识 =====

    question_id: str = Field(
        ...,
        description="题目在当前作业中的唯一标识（如：Q1, Q2）"
    )

    # ===== 题目内容 =====

    question_text: str = Field(
        ...,
        description="题目的完整描述文本，包含必要的已知条件与问题"
    )

    category: ExerciseCategory = Field(
        ...,
        description="题目类型"
    )

    options: Optional[List[str]] = Field(
        None,
        description="选择题或判断题的选项列表；非选择类题目为 None"
    )

    score: confloat(gt=0) = Field(
        ...,
        description="该题分值"
    )

    # ===== 标准答案与解析 =====

    correct_answer: str = Field(
        ...,
        description="题目的标准答案（选择题为选项标识，主观题为要点或步骤）"
    )

    answer_analysis: str = Field(
        ...,
        description="答案解析，说明解题思路、关键步骤和易错点"
    )

    # ===== 教学元数据（极其重要） =====

    subject: str = Field(
        ...,
        description="所属学科（如：高二物理、初中数学）"
    )

    topic: str = Field(
        ...,
        description="具体知识主题（如：牛顿第二定律、一元二次方程）"
    )

    knowledge_points: List[str] = Field(
        ...,
        description="该题直接考查的知识点列表"
    )

    difficulty: DifficultyLevel = Field(
        ...,
        description="题目难度等级"
    )

    cognitive_level: CognitiveLevel = Field(
        ...,
        description="认知层级（布鲁姆认知目标分类）"
    )

    # ===== 生成与追溯信息（为 AI 系统服务） =====

    required_context: Optional[str] = Field(
        None,
        description="生成此题所依赖的上下文或知识库内容（RAG 来源）"
    )

    generation_notes: Optional[str] = Field(
        None,
        description="生成备注（如：变式题、易错题、拔高题等）"
    )

    suggested_time_minutes: Optional[conint(ge=1)] = Field(
        None,
        description="建议学生完成此题所需时间（分钟）"
    )



class ExerciseSet(BaseModel):
    """
    一份完整的作业 / 练习集。
    """

    # ===== 基本标识 =====

    exercise_set_id: str = Field(
        ...,
        description="作业的唯一标识"
    )

    title: str = Field(
        ...,
        description="作业标题（如：'高二物理·牛顿定律课后练习'）"
    )

    subject: str = Field(
        ...,
        description="学科"
    )

    # ===== 教学目标与整体属性 =====

    overall_difficulty: DifficultyLevel = Field(
        "中等",
        description="作业整体难度"
    )

    total_score: float = Field(
        ...,
        description="作业总分"
    )

    exercise_count: int = Field(
        ...,
        description="题目总数"
    )

    covered_knowledge_points: List[str] = Field(
        ...,
        description="作业整体覆盖的知识点列表"
    )

    purpose: Optional[str] = Field(
        None,
        description="作业用途（如：课后巩固、单元检测、考前训练）"
    )

    # ===== 时间与生成信息 =====

    suggested_duration_minutes: Optional[int] = Field(
        None,
        description="建议完成整份作业的时间（分钟）"
    )

    generation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="生成时间"
    )

    generated_by: str = Field(
        "System AI",
        description="生成来源"
    )

    # ===== 核心内容 =====

    exercises: List[ExerciseItem] = Field(
        ...,
        description="题目列表"
    )

class ExerciseGenerationRequest(BaseModel):
    """
    用户或系统请求生成作业练习时的参数约束模型。
    """

    # ===== 必需条件 =====

    subject: str = Field(
        ...,
        description="学科（如：高二物理）"
    )

    topic: str = Field(
        ...,
        description="知识主题或范围"
    )

    num_questions: conint(ge=1, le=50) = Field(
        10,
        description="题目数量"
    )

    target_difficulty: DifficultyLevel = Field(
        "中等",
        description="目标难度"
    )

    # ===== 题型与结构约束 =====

    target_categories: Optional[
        conlist(ExerciseCategory, min_length=1)
    ] = Field(
        None,
        description="指定题型列表（不指定则自动分配）"
    )

    cognitive_distribution: Optional[dict[CognitiveLevel, int]] = Field(
        None,
        description="认知层级分布（如：{'理解':4, '应用':6}）"
    )

    # ===== 上下文与 RAG =====

    required_context: Optional[str] = Field(
        None,
        description="用于生成题目的知识库上下文或教材内容"
    )

    # ===== 业务信息 =====

    purpose: Optional[str] = Field(
        None,
        description="作业用途"
    )

    requestor_id: Optional[str] = Field(
        None,
        description="请求来源标识"
    )

class ExerciseRequest(BaseModel):
    # ===== Prompt2 核心字段 =====
    subject: str | None = None
    topic: str | None = None
    num_questions: int | None = None
    target_difficulty: str | None = None

    # ===== 可选但非常重要 =====
    target_categories: list[str] | None = None
    cognitive_distribution: dict | None = None
    required_context: str | None = None
    purpose: str | None = None


class ClarifyState(BaseModel):
    request: ExerciseRequest =Field(default_factory=ExerciseRequest)         # 结构化字段（填 Prompt2 用）
    confirm_md: str | None = None     # LLM 生成的 Markdown 草案
    confirm_md_final: str | None = None  # 前端编辑回传后的最终版（进入阶段2）
    stage: Literal["clarify", "confirm", "generate"] = "clarify"
