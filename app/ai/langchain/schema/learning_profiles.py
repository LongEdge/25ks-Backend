from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# OverallLevel = Literal["较弱", "中等", "较好"]
# FrequencyLevel = Literal["低", "中", "高"]

class LearningScope(BaseModel):
    subject: str = Field(..., description="学科")
    grade: str = Field(..., description="年级")
    class_name: Optional[str] = Field(None, description="班级名称")
    semester: Optional[str] = Field(None, description="学期")
    related_chapter: Optional[str] = Field(None, description="关联章节或知识主题")
    data_time_range: Optional[str] = Field(None, description="学情数据覆盖时间范围")

class OverallLearningLevel(BaseModel):
    # overall_level: OverallLevel = Field(..., description="整体学习水平")
    overall_level: str = Field(..., description="整体学习水平")
    strong_ratio: Optional[str] = Field(None, description="学习能力较强学生比例")
    average_ratio: Optional[str] = Field(None, description="中等学生比例")
    weak_ratio: Optional[str] = Field(None, description="学习能力偏弱学生比例")

class PriorKnowledge(BaseModel):
    mastered_knowledge_points: List[str] = Field(
        default_factory=list,
        description="已掌握的知识点"
    )
    partially_mastered_knowledge_points: List[str] = Field(
        default_factory=list,
        description="部分掌握的知识点"
    )

class CommonMistake(BaseModel):
    knowledge_point: str = Field(..., description="对应知识点")
    description: str = Field(..., description="错误或问题描述")
    # frequency: FrequencyLevel = Field(..., description="出现频率")
    frequency: str = Field(..., description="出现频率")

class LearningBehavior(BaseModel):
    # calculation_skill: Optional[OverallLevel] = Field(None, description="计算能力")
    # conceptual_understanding: Optional[OverallLevel] = Field(None, description="概念理解能力")
    # class_participation: Optional[OverallLevel] = Field(None, description="课堂参与度")
    # homework_completion: Optional[OverallLevel] = Field(None, description="作业完成情况")
    calculation_skill: Optional[str] = Field(None, description="计算能力")
    conceptual_understanding: Optional[str] = Field(None, description="概念理解能力")
    class_participation: Optional[str] = Field(None, description="课堂参与度")
    homework_completion: Optional[str] = Field(None, description="作业完成情况")
class LearningProfile(BaseModel):
    """
    班级学情分析（Learning Profile）
    用于教案生成、作业生成、教学策略优化
    """

    scope: LearningScope

    overall_learning_level: OverallLearningLevel

    prior_knowledge: PriorKnowledge = Field(
        default_factory=PriorKnowledge,
        description="已具备的前置知识"
    )

    common_mistakes: List[CommonMistake] = Field(
        default_factory=list,
        description="典型问题与易错点"
    )

    learning_behavior: Optional[LearningBehavior] = Field(
        None,
        description="学习行为特征"
    )

    teaching_suggestions: List[str] = Field(
        default_factory=list,
        description="教师给出的教学建议"
    )

    remarks: Optional[str] = Field(
        None,
        description="补充说明（自由文本）"
    )

    created_by: Optional[str] = Field(
        "teacher",
        description="学情来源（teacher / system / ai）"
    )

"""
EXAMPLE:
{
  "scope": {
    "subject": "语文",
    "grade": "高二",
    "class_name": "高二三班",
    "semester": "2024-2025 下学期",
    "related_chapter": "一元二次方程",
    "data_time_range": "第一单元，开学后一个月"
  },
  "overall_learning_level": {
    "overall_level": "中等",
    "strong_ratio": "20%",
    "average_ratio": "60%",
    "weak_ratio": "20%"
  },
  "prior_knowledge": {
    "mastered_knowledge_points": [
      "一元一次方程",
      "整式乘法"
    ],
    "partially_mastered_knowledge_points": [
      "因式分解（十字相乘法）"
    ]
  },
  "common_mistakes": [
    {
      "knowledge_point": "因式分解",
      "description": "符号处理错误",
      "frequency": "高"
    }
  ],
  "learning_behavior": {
    "calculation_skill": "中等",
    "conceptual_understanding": "较弱",
    "class_participation": "较好",
    "homework_completion": "中等"
  },
  "teaching_suggestions": [
    "新授时多结合具体实例",
    "板书中突出因式为零的思想"
  ]
}

"""

