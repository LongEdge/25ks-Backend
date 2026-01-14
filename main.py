from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from app.api.v1 import auth, lesson, ai, learning_profile, media, template
from app.core.config import settings
from app.core.exception_handler import register_exception_handlers

app = FastAPI(
    title="AI辅助教师备课系统",
    description="基于FastAPI的AI辅助教师备课系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# 注册异常处理器
register_exception_handlers(app)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth 认证模块"])
app.include_router(lesson.router, prefix="/api/v1/lesson", tags=["Lesson 教案模块"])
app.include_router(template.router, prefix="/api/v1/template", tags=["Template 模板管理模块"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI 智能服务模块"])
app.include_router(learning_profile.router, prefix="/api/v1/learning_profile", tags=["Learning Profile 学习档案模块"])
app.include_router(media.router, prefix="/api/v1/media", tags=["Media 媒体生成模块"])

@app.get("/status/ping")
async def ping():
    return {"status": "ok", "message": "AI辅助教师备课系统API服务正常运行"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)