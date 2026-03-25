from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI辅助教师备课系统"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./app.db"

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: List[str] = ["*"]

    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.example.com/v1"

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    CHROMA_DB_URL: str = "localhost:8000"

    REDIS_URL: str = "localhost:6379"
    REDIS_KEY: str = ""

    ZHIPU_API_KEY: str = ""
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-example.aliyuncs.com"
    ALIYUN_OSS_BUCKET: str = "your-bucket-name"
    ALIYUN_OSS_DOMAIN: str = "https://example-bucket.oss-cn-example.aliyuncs.com"

    KG_CSV_PATH: str = r"resources/out_v2_chinese_teaching.csv"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
