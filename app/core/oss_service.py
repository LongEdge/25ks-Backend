"""
阿里云 OSS 服务

提供文件上传、删除等功能
"""

import oss2
import uuid
from typing import Optional
from io import BytesIO
from app.core.config import settings


class AliyunOSSService:
    """阿里云 OSS 服务"""

    def __init__(self):
        self.access_key_id = settings.ALIYUN_ACCESS_KEY_ID
        self.access_key_secret = settings.ALIYUN_ACCESS_KEY_SECRET
        self.endpoint = settings.ALIYUN_OSS_ENDPOINT
        self.bucket_name = settings.ALIYUN_OSS_BUCKET
        self.domain = settings.ALIYUN_OSS_DOMAIN

        # 创建认证和 Bucket 对象
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(
            self.auth,
            f"https://{self.endpoint}",
            self.bucket_name
        )

    def upload_file(
        self,
        file_content: bytes,
        file_path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        上传文件到 OSS

        Args:
            file_content: 文件内容
            file_path: OSS 中的文件路径（如 avatars/user_1_xxx.jpg）
            content_type: 文件 MIME 类型

        Returns:
            文件的公开访问 URL
        """
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        self.bucket.put_object(file_path, BytesIO(file_content), headers=headers)

        # 返回文件 URL
        return f"{self.domain}/{file_path}"

    def upload_avatar(self, file_content: bytes, user_id: int, file_ext: str = "jpg") -> str:
        """
        上传用户头像

        Args:
            file_content: 图片内容
            user_id: 用户 ID
            file_ext: 文件扩展名

        Returns:
            头像 URL
        """
        # 生成唯一文件名
        unique_id = uuid.uuid4().hex[:8]
        file_path = f"avatars/user_{user_id}_{unique_id}.{file_ext}"

        # MIME 类型映射
        mime_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        content_type = mime_types.get(file_ext.lower(), "image/jpeg")

        return self.upload_file(file_content, file_path, content_type)

    def delete_file(self, file_path: str) -> bool:
        """
        删除 OSS 中的文件

        Args:
            file_path: 文件路径（相对于 Bucket 根目录）

        Returns:
            是否删除成功
        """
        try:
            self.bucket.delete_object(file_path)
            return True
        except Exception:
            return False

    def get_file_path_from_url(self, url: str) -> Optional[str]:
        """从 URL 提取文件路径"""
        if url and self.domain in url:
            return url.replace(f"{self.domain}/", "")
        return None


# 创建服务实例
oss_service = AliyunOSSService()
