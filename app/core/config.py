from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 项目基本配置
    PROJECT_NAME: str = "AI辅助教师备课系统"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./teacher备课系统.db"
    
    # JWT配置
    SECRET_KEY: str = "secretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # AI服务配置
    AI_API_KEY: str = "your-ai-api-key"
    AI_BASE_URL: str = "https://api.example.com/v1"
    
    # 文件存储配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    # chormaDB配置
    CHROMA_DB_URL: str = "localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
