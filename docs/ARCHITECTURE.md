# 系统架构设计文档

> AI 辅助教师备课系统 — 架构全景解析

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              客户端 (Client)                             │
│                    Web / App / 第三方集成 → FastAPI REST API             │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│                           API 网关层 (FastAPI)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  Auth   │ │ Lesson  │ │  AI     │ │Template │ │Profile  │ │ Media   │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
└───────┼───────────┼───────────┼───────────┼───────────┼───────────┼───────┘
        │           │           │           │           │           │
┌───────▼───────────▼───────────▼───────────▼───────────▼───────────▼───────┐
│                            业务逻辑层 (Service Layer)                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐   │
│  │LessonContext   │  │ExerciseService │  │ LearningProfileService      │   │
│  │Service         │  │                │  │                            │   │
│  └───────┬────────┘  └───────┬────────┘  └────────────────────────────┘   │
│          │                    │                                            │
│  ┌───────▼────────────────────▼──────────────────────────────────────┐    │
│  │                     LangChain AI 层                                │    │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │    │
│  │  │LessonOrchestrator│  │ExerciseAgent     │  │LearnAnalysis    │  │    │
│  │  │(教案生成流水线) │  │(题库生成Agent)   │  │Agent            │  │    │
│  │  └────────┬────────┘  └────────┬─────────┘  └─────────────────┘  │    │
│  │           │                    │                                  │    │
│  │  ┌────────▼────────────────────▼──────────────────────────────┐  │    │
│  │  │              Prompt 模板层 (prompts/)                      │  │    │
│  │  │   LESSON.py | CLARIFY.py | EXERCISE.py | LPS.py          │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐    │    │
│  │  │ RAG 工具    │  │ KG 工具     │  │ 智谱媒体工具           │    │    │
│  │  │(知识检索)   │  │(知识图谱)   │  │(图像/视频生成)         │    │    │
│  │  └────────────┘  └────────────┘  └────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
        │                    │
┌───────▼────────┐    ┌───────▼────────┐
│   MySQL        │    │   Redis         │
│  (教案/用户    │    │  (生成任务状态   │
│   模板/题库)   │    │   异步进度)      │
└───────────────┘    └────────────────┘
        │
┌───────▼────────┐    ┌───────▼────────┐
│   智谱 API     │    │ 阿里云 OSS     │
│  (GLM-4/LLM   │    │ (文件存储)      │
│  CogView/CogV)│    └────────────────┘
└───────────────┘
```

## 2. 核心模块依赖关系

```
main.py (入口)
  └─→ app.api.v1.* (路由注册)
          │
          ├─→ auth.py
          │       └─→ app.core.security (JWT / Argon2)
          │               └─→ app.models.user
          │
          ├─→ lesson.py
          │       ├─→ app.core.redis_util (任务状态)
          │       ├─→ app.models.lesson_model
          │       └─→ app.service.lesson_context
          │
          ├─→ ai.py
          │       ├─→ app.ai.langchain.orchestrator (教案生成)
          │       ├─→ app.ai.langchain.agents.ExerciseAgent (题库生成)
          │       ├─→ app.ai.langchain.agents.LearnAnalysisAgent (学情分析)
          │       ├─→ app.ai.langchain.templates (模板系统)
          │       └─→ app.service.exercise_service
          │
          ├─→ template.py
          │       ├─→ app.ai.langchain.templates (内置模板)
          │       └─→ app.models.lesson_template_model
          │
          ├─→ learning_profile.py
          │       └─→ app.service.learning_profile
          │
          └─→ media.py
                  └─→ app.core.zhipu_media (智谱媒体)
```

## 3. 教案生成核心流程

### 3.1 澄清对话流程（Clarify）

```
用户 → POST /api/v1/ai/lesson/clarify/chat
         │
         ├─→ lesson_clarify_chat(session_id, message)
         │       └─→ app.ai.langchain.utils.lesson_session
         │               ├─→ LESSON Clarify Prompt (prompts/CLARIFY.py)
         │               └─→ LLM (GLM-4)
         │
         ← 返回 {reply, clarify, stage, is_complete}
```

**澄清阶段**：通过多轮对话收集教案生成所需的 4 个核心字段：
- `subject`（学科）
- `grade`（年级）
- `lesson_title`（课题名称）
- `lesson_type`（课程类型）

### 3.2 异步教案生成流程

```
POST /api/v1/ai/lesson/generate
  │
  ├─→ 初始化 Redis 任务 (init_lesson_task)
  ├─→ 构建 LessonContext (build_lesson_context)
  │       └─→ 聚合学情档案 (LearningProfile)
  │
  └─→ 后台任务: orchestrator.run_pipeline_sync()
          │
          ├─→ 按 GENERATION_PIPELINE 逐章节生成:
          │       objectives → key_points →
          │       teaching_flow.introduction →
          │       teaching_flow.main →
          │       teaching_flow.practice →
          │       teaching_flow.summary →
          │       homework → board_design → remarks
          │
          ├─→ 每个章节:
          │       ├─→ get_section_prompt(stage) → LESSON Prompt
          │       ├─→ LLM.invoke(messages)
          │       └─→ update_partial_lesson(task_id, stage, content)
          │
          └─→ 全部完成后: _save_to_mysql() → LessonModel

状态查询: GET /api/v1/ai/lesson/generate/status?task_id=xxx
  └─→ get_lesson_task(task_id) → Redis
```

### 3.3 教案内容更新（章节锁机制）

```
PATCH /api/v1/lesson/{id}/section
Body: {section_key: "teaching_flow.main", content: "...", lock: true}
  │
  ├─→ 支持嵌套 key: "teaching_flow.main"
  ├─→ 锁定章节: AI 不会覆盖已锁定的章节
  └─→ 存储于 lesson.locked_sections (JSON 数组)
```

## 4. 数据模型关系

```
┌─────────────┐
│    User     │  (teacher_id)
└──────┬──────┘
       │ 1:N
       ├──────────────────────────┐
       │                          │
┌──────▼──────┐           ┌───────▼────────┐
│ LessonModel │           │LessonTemplate  │
│ (教案)      │           │Model (模板)     │
└──────┬──────┘           └────────────────┘
       │
       │ 1:N (可选, 一个教案可含多个题库)
       │
┌──────▼──────┐
│ExerciseModel│  (题库)
└─────────────┘

┌─────────────────────┐
│ LearningProfileModel │
│ (学习档案)            │
│ teacher_id + subject  │
│ + grade              │
└─────────────────────┘
```

## 5. AI 服务架构

### 5.1 LLM 调用链路

```
AIService (通用 AI 封装)
  └─→ httpx.AsyncClient → AI_BASE_URL (智谱 API 代理)

LangChain Agents:
  ├─ LessonOrchestrator
  │       └─→ ChatZhipuAI(model="glm-4-flashx-250414")
  │
  ├─ ExerciseAgent
  │       └─→ ChatZhipuAI
  │
  └─ LearnAnalysisAgent
          └─→ ChatZhipuAI
```

### 5.2 Prompt 模板体系

| 文件 | 职责 |
|------|------|
| `prompts/CLARIFY.py` | 教案澄清对话的 System/User Prompt |
| `prompts/LESSON.py` | 各章节生成的 Prompt 模板 |
| `prompts/EXERCISE.py` | 题库生成的 Prompt |
| `prompts/LPS.py` | 学习档案分析 Prompt |
| `templates.py` | 内置教案模板结构定义 |

### 5.3 内置教案模板 (default-v1)

```
LessonTemplate:
  sections:
    1. objectives           (教学目标)         [必填]
    2. key_points          (教学重难点)        [必填]
    3. teaching_flow        (教学过程)          [必填]
       ├─ introduction     (导入新课)
       ├─ main             (新授环节)
       ├─ practice         (课堂练习)
       └─ summary          (课堂小结)
    4. homework            (作业布置)
    5. board_design        (板书设计)
    6. remarks             (教学反思)
```

## 6. 媒体生成架构

```
POST /api/v1/media/image/generate
  │
  ├─→ zhipu_media_service.optimize_prompt()  (LLM 优化提示词)
  │       └─→ ChatGLM-4 (glm-4-flash)
  │
  └─→ zhipu_media_service.generate_image()
          └─→ 智谱 CogView-3 Flash API

POST /api/v1/media/video/generate
  │
  ├─→ 提示词优化 (同上)
  └─→ zhipu_media_service.generate_video()
          └─→ 智谱 CogVideoX Flash API (异步)

GET /api/v1/media/video/status/{task_id}
  └─→ zhipu_media_service.query_video_task()
```

## 7. 安全认证架构

```
JWT 认证流程:
  1. 注册/登录 → verify_password(argon2) → create_access_token(JWT)
  2. 后续请求 → Authorization: Bearer <token>
  3. FastAPI Depends(get_current_user) → oauth2_scheme → decode JWT
  4. 验证通过后注入 current_user: User

密码存储: Argon2 (非 bcrypt)
Token 算法: HS256
Token 过期: 30 分钟 (可配置)
```

## 8. 配置管理

```python
Settings (from pydantic_settings.BaseSettings):
  ├── 数据库:     DATABASE_URL (sqlite/mysql)
  ├── JWT:        SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
  ├── AI:         AI_API_KEY, AI_BASE_URL
  ├── 智谱媒体:   ZHIPU_API_KEY, ZHIPU_BASE_URL
  ├── Redis:      REDIS_URL, REDIS_KEY
  ├── 阿里云OSS:  ALIYUN_OSS_*
  └── 知识图谱:   KG_CSV_PATH, KG_DB_PATH
```

## 9. 扩展点设计

| 扩展点 | 当前实现 | 可扩展方向 |
|--------|----------|------------|
| **LLM Provider** | 智谱 GLM-4 | OpenAI GPT / Claude / 本地模型 |
| **教案 Pipeline** | 9 阶段固定 | 增加/调整章节顺序 |
| **模板系统** | 内置 + 自定义 | 可视化模板编辑器 |
| **RAG** | ChromaDB (预留) | 接入手册/教材知识库 |
| **知识图谱** | DuckDB CSV (预留) | Neo4j / NebulaGraph |
| **媒体生成** | 智谱 CogView/Video | Stable Diffusion / Pika |

## 10. 关键设计决策

1. **异步生成 + Redis 状态**：教案生成是耗时操作，通过 Redis 存储中间状态，前端轮询查询进度
2. **章节锁机制**：用户编辑过的章节被锁定，AI 不会覆盖，保证教师主导权
3. **学情上下文注入**：生成教案时可携带班级学情档案，使教案更具针对性
4. **模板 + Pipeline 分离**：模板定义章节结构，Pipeline 定义生成顺序，灵活可配
5. **Base64 头像存储**：简化存储，不依赖外部文件服务
