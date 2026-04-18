# 12. 数据库与 Redis 工具

## 数据库层

**文件**: `app/core/database.py`

### SQLAlchemy 引擎

```python
# SQLite（开发）
engine = create_engine(
    "sqlite:///./app.db",
    connect_args={"check_same_thread": False}
)

# MySQL/PostgreSQL（生产）
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 连接前检测
    pool_recycle=300     # 5分钟回收连接
)
```

### SessionLocal

```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### 依赖注入

```python
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Base 模型

```python
Base = declarative_base()

class BaseModel(Base, TimestampMixin):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

## Redis 工具层

**文件**: `app/core/redis_util.py`

### 任务状态存储

```python
LESSON_TASK_PREFIX = "lesson:gen:"
TASK_TTL = 3600  # 1 小时
```

### 核心操作

| 函数 | 作用 |
|------|------|
| `init_lesson_task()` | 初始化生成任务 |
| `get_lesson_task()` | 获取任务状态和 partial_lesson |
| `update_lesson_task()` | 更新任务状态 |
| `update_partial_lesson()` | 更新某个章节的内容 |
| `mark_task_completed()` | 标记完成，记录 lesson_id |
| `mark_task_failed()` | 标记失败，记录错误信息 |
| `extend_task_ttl()` | 延长 TTL |

### 嵌套内容更新

```python
# 支持 "teaching_flow.main" 格式的嵌套 key
if "." in stage:
    parts = stage.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = content
```

### 单例 Redis 客户端

```python
@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=host, port=port, password=password,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
```

## 数据库模型一览

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | `users` | 教师用户 |
| `LessonModel` | `lessons` | 教案 |
| `LessonTemplateModel` | `lesson_templates` | 教案模板 |
| `ExerciseModel` | `exercise_sets` | 题库 |
| `LearningProfileModel` | `learning_profiles` | 学习档案 |

## 初始化数据库

```bash
python init_db.py
```

> 建议生产环境使用 Alembic 进行数据库迁移管理。
