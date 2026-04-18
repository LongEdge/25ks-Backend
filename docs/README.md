# AI 辅助教师备课系统 - 文档总览

> 基于 FastAPI + LangChain 的智能教案生成平台

## 📚 文档目录

| 文档 | 说明 |
|------|------|
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | 系统架构设计、模块关系、数据流图 |
| **[API_REFERENCE.md](./API_REFERENCE.md)** | 完整 API 接口清单与使用示例 |
| **[DEPLOYMENT.md](./DEPLOYMENT.md)** | 部署指南、环境配置、Docker |
| **[USER_GUIDE.md](./USER_GUIDE.md)** | 用户使用手册、功能操作指南 |
| **[modules/README.md](./modules/README.md)** | 核心模块详细分析索引 |

## 🎯 项目概述

**25ks-Backend** 是一个 AI 辅助教师备课系统的后端服务，提供：

- 📝 **教案智能生成** — 基于 LangChain + 智谱 GLM-4，多阶段流水线生成完整教案
- 📚 **题库管理** — AI 批量生成习题，支持 CRUD 操作
- 🎨 **多媒体生成** — 智谱 CogView 图像生成 + CogVideo 视频生成
- 👤 **学习档案管理** — 学情分析与个性化教学建议
- 📋 **教案模板系统** — 内置标准模板 + 自定义模板
- ☁️ **文件存储** — 阿里云 OSS 对象存储集成

## 🔌 API 路由总览

| 前缀 | 模块 | 功能 |
|------|------|------|
| `/api/v1/auth` | Auth | 教师注册/登录/个人信息管理 |
| `/api/v1/lesson` | Lesson | 教案 CRUD、章节粒度更新、生成状态 |
| `/api/v1/template` | Template | 教案模板 CRUD |
| `/api/v1/ai` | AI | 教案生成、题库生成、学习档案分析 |
| `/api/v1/learning_profile` | Learning Profile | 学情档案 CRUD |
| `/api/v1/media` | Media | 图像/视频 AI 生成 |
| `/status/ping` | — | 服务健康检查 |

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **框架** | FastAPI + Uvicorn |
| **AI/LLM** | LangChain + ChatZhipuAI (GLM-4) |
| **数据库** | SQLAlchemy + SQLite/MySQL |
| **缓存/任务** | Redis |
| **向量数据库** | ChromaDB（预留） |
| **知识图谱** | DuckDB（预留） |
| **媒体生成** | 智谱 CogView-3 + CogVideoX |
| **存储** | 阿里云 OSS |
| **认证** | JWT (HS256) + Argon2 密码哈希 |

## 📁 目录结构

```
25ks-Backend/
├── main.py                     # FastAPI 应用入口
├── app/
│   ├── api/v1/                 # API 路由层
│   │   ├── auth.py             # 认证模块
│   │   ├── lesson.py           # 教案 CRUD
│   │   ├── template.py         # 模板管理
│   │   ├── ai.py               # AI 生成（教案/题库）
│   │   ├── learning_profile.py  # 学情档案
│   │   └── media.py            # 图像/视频生成
│   ├── core/                   # 核心基础设施
│   │   ├── config.py           # 配置管理（.env）
│   │   ├── database.py         # SQLAlchemy 引擎
│   │   ├── security.py         # JWT + 密码哈希
│   │   ├── redis_util.py       # Redis 任务状态
│   │   ├── ai_service.py       # 通用 AI 服务封装
│   │   ├── oss_service.py      # 阿里云 OSS
│   │   └── zhipu_media.py      # 智谱媒体生成
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── user.py             # 用户/教师模型
│   │   ├── lesson_model.py     # 教案模型
│   │   ├── lesson_template_model.py  # 模板模型
│   │   └── ...
│   ├── schema/                 # Pydantic 请求/响应模型
│   ├── service/                # 业务逻辑层
│   │   ├── lesson_context.py   # 教案上下文聚合
│   │   ├── learning_profile.py # 学情档案服务
│   │   └── exercise_service.py # 题库服务
│   └── ai/langchain/           # LangChain AI 逻辑
│       ├── orchestrator/      # 教案生成编排器
│       ├── agents/             # LangChain Agents
│       ├── prompts/            # Prompt 模板
│       ├── schema/             # AI Schema 定义
│       ├── templates.py        # 内置教案模板
│       └── tools/              # RAG / 知识图谱工具
├── docs/                      # 本文档目录
├── resources/                 # 资源文件（知识图谱 CSV 等）
└── requirements.txt
```

## ⚡ 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 初始化数据库
python init_db.py

# 启动服务
python main.py
# 或
uvicorn main:app --reload
```

访问 `http://localhost:8000/docs` 查看 Swagger UI 文档。
