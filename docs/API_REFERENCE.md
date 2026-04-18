# API 参考文档

> 所有接口均需要登录后访问（除 `/status/ping` 和认证接口）

**Base URL**: `http://host:8000`  
**认证方式**: `Authorization: Bearer <access_token>`

---

## 目录

1. [认证 Auth](#1-认证-auth-apiv1auth)
2. [教案 Lesson](#2-教案-lesson-apiv1lesson)
3. [教案模板 Template](#3-教案模板-template-apiv1template)
4. [AI 服务 AI](#4-ai-服务-ai-apiv1ai)
5. [学习档案 Learning Profile](#5-学习档案-learning-profile-apiv1learning_profile)
6. [媒体生成 Media](#6-媒体生成-media-apiv1media)

---

## 1. 认证 Auth `/api/v1/auth`

### 1.1 注册

```
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "username": "teacher_wang",
  "email": "wang@example.com",
  "password": "secure_password",
  "full_name": "王老师"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "teacher_wang",
  "email": "wang@example.com",
  "full_name": "王老师",
  "role": "teacher"
}
```

### 1.2 登录

```
POST /api/v1/auth/login
```

**Request Body (OAuth2PasswordRequestForm):**
```
username=teacher_wang&password=secure_password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 1.3 获取个人资料

```
GET /api/v1/auth/profile
```

**Response:**
```json
{
  "id": 1,
  "username": "teacher_wang",
  "email": "wang@example.com",
  "full_name": "王老师",
  "avatar_base64": "data:image/jpeg;base64,...",
  "subject": "数学",
  "teaching_style": ["启发式", "互动式"],
  "years_of_experience": 5
}
```

### 1.4 更新个人资料

```
PUT /api/v1/auth/profile
```

**Request Body:**
```json
{
  "full_name": "王建国",
  "subject": "物理",
  "years_of_experience": 10
}
```

### 1.5 修改密码

```
PUT /api/v1/auth/password
```

**Request Body:**
```json
{
  "old_password": "old_password",
  "new_password": "new_secure_password"
}
```

### 1.6 上传头像

```
POST /api/v1/auth/avatar
Content-Type: multipart/form-data

file: [图片文件 JPEG/PNG/GIF/WebP, 最大 5MB]
```

**Response:**
```json
{
  "avatar_base64": "data:image/jpeg;base64,..."
}
```

---

## 2. 教案 Lesson `/api/v1/lesson`

### 2.1 获取所有教案（含生成状态）

```
GET /api/v1/lesson/all
```

**Response:**
```json
{
  "generating": [
    {
      "task_id": "uuid-xxx",
      "status": "running",
      "current_stage": "teaching_flow.main",
      "progress": 0.55,
      "partial_lesson": {...},
      "locked_sections": ["objectives"],
      "lesson_id": null
    }
  ],
  "completed": [
    {
      "id": 1,
      "lesson_title": "二次函数图像与性质",
      "subject": "数学",
      "grade": "初三",
      "generation_status": "completed",
      "content": {...}
    }
  ]
}
```

### 2.2 教案列表（分页）

```
GET /api/v1/lesson/list?page=1&page_size=20&subject=数学&grade=初三
```

### 2.3 创建教案

```
POST /api/v1/lesson
```

**Request Body:**
```json
{
  "template_id": "default-v1",
  "subject": "数学",
  "grade": "初三",
  "lesson_title": "二次函数",
  "lesson_type": "新授课",
  "class_duration": 45,
  "lesson_count": 2
}
```

### 2.4 获取教案详情

```
GET /api/v1/lesson/{id}
```

### 2.5 完整更新教案

```
PUT /api/v1/lesson/{id}
```

### 2.6 局部更新教案

```
PATCH /api/v1/lesson/{id}
```

### 2.7 更新单个章节

```
PATCH /api/v1/lesson/{id}/section
```

**Request Body:**
```json
{
  "section_key": "teaching_flow.main",
  "content": "## 新授环节\n\n教师首先提问...\n\n## 例题精讲\n\n【例1】...",
  "lock": true
}
```

> `section_key` 支持嵌套格式，如 `"teaching_flow.introduction"`
> `lock=true` 时该章节被锁定，AI 生成时会跳过

### 2.8 删除教案

```
DELETE /api/v1/lesson/{id}
```

---

## 3. 教案模板 Template `/api/v1/template`

### 3.1 模板列表

```
GET /api/v1/template?include_system=true
```

**Response:**
```json
{
  "total": 3,
  "page": 1,
  "page_size": 20,
  "templates": [
    {
      "template_id": "default-v1",
      "name": "标准教案模板",
      "description": "适用于常规课堂教学的标准教案结构",
      "is_builtin": true,
      "teacher_id": null
    },
    {
      "template_id": "custom-abc123",
      "name": "我的自定义模板",
      "is_builtin": false,
      "teacher_id": 1
    }
  ]
}
```

### 3.2 获取模板详情

```
GET /api/v1/template/{template_id}
```

### 3.3 创建自定义模板

```
POST /api/v1/template
```

**Request Body:**
```json
{
  "name": "实验课模板",
  "description": "适用于实验类课程",
  "is_public": false,
  "sections": [
    {"key": "objectives", "title": "教学目标", "type": "markdown", "required": true},
    {"key": "experiment_flow", "title": "实验过程", "type": "structured_json", "required": true},
    {"key": "safety_notes", "title": "安全注意事项", "type": "text", "required": true}
  ]
}
```

### 3.4 更新模板

```
PUT /api/v1/template/{template_id}
```

### 3.5 删除模板

```
DELETE /api/v1/template/{template_id}
```

> 只能删除自己创建的模板，且模板不能被任何教案使用

---

## 4. AI 服务 AI `/api/v1/ai`

### 4.1 教案澄清对话

```
POST /api/v1/ai/lesson/clarify/chat
```

**Request Body:**
```json
{
  "session_id": "uuid-session-xxx",
  "message": "我想生成一个初三数学的二次函数教案"
}
```

**Response:**
```json
{
  "reply": "好的！请确认以下信息：\n- 学科：数学\n- 年级：初三\n还需要确认课题名称，请告诉我具体要上哪节二次函数的课？",
  "clarify": {
    "subject": "数学",
    "grade": "初三",
    "lesson_title": null,
    "lesson_type": null
  },
  "stage": "collecting_title",
  "is_complete": false
}
```

> 多轮对话后，`stage=confirmed` 且 `is_complete=true` 时进入生成阶段

### 4.2 查询澄清状态

```
GET /api/v1/ai/lesson/clarify/state?session_id=uuid-session-xxx
```

### 4.3 重置澄清会话

```
DELETE /api/v1/ai/lesson/clarify/session?session_id=uuid-session-xxx
```

### 4.4 触发教案生成

```
POST /api/v1/ai/lesson/generate
```

**Request Body (对话模式):**
```json
{
  "session_id": "uuid-session-xxx",
  "confirm_md_final": "我确认以上信息正确，请生成教案",
  "locked_sections": ["objectives"]
}
```

**Request Body (直接模式):**
```json
{
  "clarify": {
    "subject": "数学",
    "grade": "初三",
    "lesson_title": "二次函数",
    "lesson_type": "新授课",
    "class_duration": 45,
    "lesson_count": 2
  },
  "template_id": "default-v1"
}
```

**Response:**
```json
{
  "task_id": "uuid-task-xxx",
  "message": "教案生成任务已启动",
  "template_id": "default-v1"
}
```

### 4.5 查询生成进度

```
GET /api/v1/ai/lesson/generate/status?task_id=uuid-task-xxx
```

**Response:**
```json
{
  "task_id": "uuid-task-xxx",
  "status": "running",
  "current_stage": "teaching_flow.main",
  "progress": 0.66,
  "partial_lesson": {
    "objectives": "## 教学目标\n...",
    "key_points": "...",
    "teaching_flow": {"introduction": "...", "main": "生成中..."}
  },
  "locked_sections": ["objectives"],
  "error": null,
  "lesson_id": null
}
```

### 4.6 获取可用模板列表

```
GET /api/v1/ai/lesson/templates
```

### 4.7 题库澄清对话

```
POST /api/v1/ai/exercise/clarify/chat
```

**Request Body:**
```json
{
  "session_id": "uuid-exercise-session",
  "message": "生成5道二次函数的练习题"
}
```

### 4.8 确认题库需求

```
POST /api/v1/ai/exercise/clarify/confirm
```

**Request Body:**
```json
{
  "session_id": "uuid-exercise-session",
  "confirm_md_final": "确认生成5道中等难度的二次函数选择题"
}
```

### 4.9 触发题库生成

```
POST /api/v1/ai/exercise/generate
```

**Request Body:**
```json
{
  "session_id": "uuid-exercise-session"
}
```

**Response:**
```json
{
  "title": "二次函数练习题",
  "subject": "数学",
  "overall_difficulty": "中等",
  "exercises": [
    {
      "type": "choice",
      "question": "下列哪个函数是二次函数？",
      "options": ["A. y=x", "B. y=x^2", "C. y=1/x", "D. y=2x+1"],
      "answer": "B",
      "explanation": "二次函数的标准形式是 y=ax^2+bx+c (a≠0)",
      "difficulty": "easy",
      "knowledge_point": "二次函数定义"
    }
  ],
  "db_id": 1,
  "saved_to_database": true
}
```

### 4.10 题库列表

```
GET /api/v1/ai/exercise/list?page=1&page_size=10&subject=数学&difficulty=中等
```

### 4.11 题库详情

```
GET /api/v1/ai/exercise/{exercise_id}
```

### 4.12 更新题库

```
PUT /api/v1/ai/exercise/{exercise_id}
```

### 4.13 删除题库

```
DELETE /api/v1/ai/exercise/{exercise_id}
```

---

## 5. 学习档案 Learning Profile `/api/v1/learning_profile`

### 5.1 创建学习档案

```
POST /api/v1/learning_profile
```

**Request Body:**
```json
{
  "title": "初三(1)班数学学情档案",
  "subject": "数学",
  "grade": "初三",
  "related_chapter": "二次函数",
  "profile": {
    "scope": {"subject": "数学", "grade": "初三", "related_chapter": "二次函数"},
    "student_data": {...},
    "analysis": {
      "overall_level": "中等",
      "main_issues": ["对概念理解不深", "计算易出错"],
      "teaching_suggestions": "加强基础概念讲解，增加练习量"
    }
  }
}
```

### 5.2 学习档案列表

```
GET /api/v1/learning_profile
```

### 5.3 获取学习档案详情

```
GET /api/v1/learning_profile/{profile_id}
```

### 5.4 更新学习档案

```
PUT /api/v1/learning_profile/{profile_id}
```

### 5.5 删除学习档案

```
DELETE /api/v1/learning_profile/{profile_id}
```

---

## 6. 媒体生成 Media `/api/v1/media`

### 6.1 生成图像

```
POST /api/v1/media/image/generate
```

**Request Body:**
```json
{
  "prompt": "一个穿着校服的男孩在教室里解二次函数黑板题目",
  "optimize_prompt": true,
  "size": "1024x1024",
  "quality": "standard",
  "watermark_enabled": false
}
```

**Response:**
```json
{
  "original_prompt": "一个穿着校服的男孩在教室里解二次函数黑板题目",
  "optimized_prompt": "[high quality, 4K], a boy in school uniform solving quadratic function problems on blackboard, classroom setting, warm lighting, detailed illustration style",
  "image_url": "https://output.xxx/xxx.png",
  "created": 1713000000
}
```

### 6.2 发起视频生成

```
POST /api/v1/media/video/generate
```

**Request Body:**
```json
{
  "prompt": "老师用动画演示二次函数图像的开口方向变化",
  "optimize_prompt": true,
  "size": "1024x1024",
  "fps": 30,
  "quality": "speed",
  "with_audio": true,
  "watermark_enabled": false
}
```

**Response:**
```json
{
  "task_id": "video-task-xxx",
  "original_prompt": "老师用动画演示...",
  "optimized_prompt": "...",
  "task_status": "PROCESSING"
}
```

### 6.3 查询视频状态

```
GET /api/v1/media/video/status/{task_id}
```

**Response:**
```json
{
  "task_id": "video-task-xxx",
  "task_status": "SUCCESS",
  "video_url": "https://output.xxx/xxx.mp4",
  "cover_image_url": "https://output.xxx/cover.jpg",
  "error": null
}
```

> `task_status` 可能值: `PROCESSING` | `SUCCESS` | `FAIL`

---

## 附录：错误码

| HTTP Status | Detail 示例 | 说明 |
|------------|-------------|------|
| 400 | "用户名已存在" | 请求参数错误 |
| 401 | "Could not validate credentials" | Token 无效或过期 |
| 403 | "无权访问此模板" | 权限不足 |
| 404 | "教案不存在" | 资源不存在 |
| 500 | "AI服务调用异常" | 服务器内部错误 |
