# 01. Master 主入口

**文件**: `main.py` (41 行)

## 职责概述

FastAPI 应用入口，负责：
1. 创建 FastAPI 实例（配置 Swagger UI）
2. 注册 CORS 中间件
3. 注册全局异常处理器
4. 注册所有 API 路由
5. 提供健康检查端点

## 核心代码解析

### 1. FastAPI 实例创建

```python
app = FastAPI(
    title="AI辅助教师备课系统",
    description="基于FastAPI的AI辅助教师备课系统API",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc"    # ReDoc 文档
)
```

### 2. CORS 配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 默认 ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. 路由注册

| 路由前缀 | 模块 | 说明 |
|---------|------|------|
| `/api/v1/auth` | auth | 认证相关 |
| `/api/v1/lesson` | lesson | 教案 CRUD |
| `/api/v1/template` | template | 模板管理 |
| `/api/v1/ai` | ai | AI 生成服务 |
| `/api/v1/learning_profile` | learning_profile | 学情档案 |
| `/api/v1/media` | media | 媒体生成 |

### 4. 健康检查

```python
@app.get("/status/ping")
async def ping():
    return {"status": "ok", "message": "AI辅助教师备课系统API服务正常运行"}
```

## 配置来源

所有配置来自 `app.core.config.Settings`，从 `.env` 文件加载。

## 扩展点

- 如需添加 JWT 中间件，可在此处统一注册
- 如需添加请求日志中间件，可在此处添加
- 路由注册顺序不影响功能，但异常处理器应在路由注册前
