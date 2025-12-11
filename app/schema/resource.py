from fastapi import Path
from pydantic import BaseModel, Field

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class KnowledgeTypeEnum(int, Enum):
    """知识库类型枚举"""
    TITLE_PARAGRAPH = 1  # 按标题段落切
    QA_PAIR = 2  # 按问答对切片
    LINE_BY_LINE = 3  # 按行切片
    CUSTOM = 5  # 自定义切片
    PAGE_BY_PAGE = 6  # 按页切片
    SINGLE_CHUNK = 7  # 按单个切片


class UploadNordb(BaseModel):
    """
    上传文件到向量数据库实例
    """
    # 路径参数
    knowledge_base_id: str = Field(
        description="知识库ID",
        alias="id"  # 对应API路径中的{id}
    )

    # 文件字段（在API中是multipart/form-data的一部分）
    files: List[Any] = Field(
        description="要上传的文件列表",
        exclude=True  # 从JSON序列化中排除，因为文件需要特殊处理
    )

    # 正文参数
    knowledge_type: Optional[KnowledgeTypeEnum] = Field(
        default=None,
        description="""
        文档类型，不传则动态解析：
        1: 按标题段落切（支持txt,doc,pdf,url,docx,ppt,pptx,md）
        2: 按问答对切片（支持txt,doc,pdf,url,docx,ppt,pptx,md）
        3: 按行切片（支持xls,xlsx,csv）
        5: 自定义切片（支持txt,doc,pdf,url,docx,ppt,pptx,md）
        6: 按页切片（支持pdf,ppt,pptx）
        7: 按单个切片（支持xls,xlsx,csv）
        """
    )

    custom_separator: Optional[List[str]] = Field(
        default=None,
        description="自定义切片规则，仅在knowledge_type=5时生效"
    )

    sentence_size: Optional[int] = Field(
        default=300,
        description="自定义切片大小，仅在knowledge_type=5时生效",
        ge=20,
        le=2000
    )

    parse_image: bool = Field(
        default=False,
        description="是否解析图片中的文本"
    )

    callback_url: Optional[str] = Field(
        default=None,
        description="回调地址"
    )

    callback_header: Optional[Dict[str, str]] = Field(
        default=None,
        description="回调时header携带的键值对"
    )

    word_num_limit: Optional[str] = Field(
        default=None,
        description="文档字数上限，必须为数字字符串"
    )

    req_id: Optional[str] = Field(
        default=None,
        description="请求唯一ID"
    )

    class Config:
        use_enum_values = True  # 序列化时使用枚举的值而不是名称
        arbitrary_types_allowed = True  # 允许任意类型，用于文件字段

#--------------------------Response Model--------------------------
# 响应模型
class SuccessInfo(BaseModel):
    """上传成功的信息"""
    document_id: str = Field(alias="documentId")
    file_name: str = Field(alias="fileName")


class FailedInfo(BaseModel):
    """上传失败的信息"""
    file_name: str = Field(alias="fileName")
    fail_reason: str = Field(alias="failReason")


class UploadResponse(BaseModel):
    """上传响应"""
    data: Dict[str, SuccessInfo | FailedInfo] = Field(
        description="响应数据，包含成功和失败的信息"
    )
    code: int
    message: str
    timestamp: int



