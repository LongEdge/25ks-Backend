# 09. 教案 CRUD 路由

**文件**: `app/api/v1/lesson.py` (386 行)

## 职责概述

提供教案的完整 CRUD 操作，包括：
- 列表查询（支持分页、筛选）
- 详情查看
- 创建、完整更新、局部更新
- 章节粒度更新（含锁定）
- 删除
- 包含正在生成的任务（从 Redis 读取）

## 核心接口

### GET /api/v1/lesson/all

返回结构：
```json
{
  "generating": [...],  // 从 Redis 读取，AI 生成中
  "completed": [...]    // 从 MySQL 读取，已完成
}
```

### PATCH /api/v1/lesson/{id}/section

章节粒度更新接口，支持嵌套 key：

```python
# section_key 支持格式
"objectives"                    # 顶层章节
"teaching_flow.introduction"    # 嵌套章节
```

实现方式：
```python
if "." in body.section_key:
    # 处理嵌套路径
    parts = body.section_key.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = body.content
else:
    content[body.section_key] = body.content
```

### 锁定机制

```python
if body.lock is not None:
    locked_sections = lesson.locked_sections or []
    if body.lock and body.section_key not in locked_sections:
        locked_sections.append(body.section_key)
    elif not body.lock and body.section_key in locked_sections:
        locked_sections.remove(body.section_key)
    lesson.locked_sections = locked_sections
```

锁定后，该章节在 AI 重新生成时会跳过。

## Schema 设计

```python
LessonCreateIn      # 创建
LessonUpdateIn      # 完整更新（PUT）
LessonPatchIn       # 局部更新（PATCH）
LessonSectionUpdateIn  # 章节更新
GeneratingTaskResponse # AI 生成任务响应
```

## 权限控制

所有接口通过 `current_user: User = Depends(get_current_user)` 注入当前用户，只返回/操作该用户的教案。

```python
LessonModel.teacher_id == current_user.id
```
