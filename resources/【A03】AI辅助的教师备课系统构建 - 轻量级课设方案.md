# 【A03】AI 辅助教师备课系统 — 完整增强版 MVP 方案

## 1. 方案综述：低成本，高完成度

**定位：** 这是一个基于 **FastAPI + Vue3 + 云端大模型 API** 构建的“全流程智能备课助手”。 **核心差异化：** 相比于简单的“一键生成”，本系统提供**向导式生成**、**版本管理**、**多模态资源库**以及**一键 PPT 导出**等核心竞争力功能，能够真实模拟教师的备课工作流。

**技术约束：**

- **0 本地算力：** 所有 AI 均调用智谱/百度 API。
- **0 复杂中间件：** 仅依赖 MySQL (数据) + ChromaDB (轻量向量) + 本地文件系统 (PPT/图片缓存)。
- **100% 可演示：** 重点优化前端交互和生成结果的结构化展示。

## 2. 系统架构增强 (System Architecture)

在原有基础上，增加了 **PPT 引擎**、**缓存层** 和 **版本控制逻辑**。

### 2.1 逻辑分层架构

- **前端交互层 (Vue 3 + Element Plus + ECharts):**
  - **编辑器：** 类似 Notion 的块级编辑器，支持拖拽排序。
  - **可视化：** ECharts 渲染学情雷达图、错题分布。
  - **对比视图：** 左右分栏展示教案版本差异 (Diff View)。
- **业务逻辑层 (FastAPI):**
  - **Workflow Engine:** 管理“向导式”备课状态流。
  - **PPT Generator:** 基于 `python-pptx` 将 JSON 教案转为幻灯片。
  - **Prompt Manager:** 管理不同风格（幽默、严谨、PBL）的提示词模板。
- **数据持久层 (MySQL 8.0):**
  - 存储教案、版本历史、题库、用户日志。
- **资源缓存层 (Local FS + SQL):**
  - 缓存已生成的图片、PPT 文件，避免重复调用 API 烧钱。

## 3. 核心功能模块深度设计 (Enhanced Modules)

### 3.1 模块一：智能教案工作台 (Smart Lesson Workbench)

**增强点：** 多模板、版本控制、摘要生成。

- **功能流程：**

  1. **向导配置 (Wizard):** 教师选择“人教版三年级”、“古诗”、“PBL 项目式教学模板”。
  2. **维度开关:** 前端勾选 `[x] 生成板书设计` `[x] 包含分层作业`。
  3. **流式生成:** 后端根据模板组装 System Prompt，流式返回 Markdown。
  4. **版本快照:** 每次保存时，后端自动存储快照。
  5. **智能摘要:** 备课完成后，触发后台任务生成 100 字摘要：“本课重点讲解了...，设计了3个互动环节...”。

- **Prompt 策略 (Template Switcher):**

  ```
  TEMPLATES = {
      "standard": "你是一位严谨的教研员，请严格按照新课标格式生成...",
      "humorous": "你是一位幽默风趣的特级教师，请用生动的语言、类比手法生成...",
      "pbl": "你是一位项目式学习专家，请围绕‘驱动性问题’设计教学环节..."
  }
  system_prompt = TEMPLATES.get(user_style, TEMPLATES["standard"])
  if need_blackboard:
      user_prompt += "请在末尾单独附上【板书设计】..."
  ```

### 3.2 模块二：多媒体资源工厂 (Multimedia Factory)

**增强点：** 板书生成、PPT 导出、素材复用。

- **功能 A：AI 板书生成**
  - **逻辑：** 提取教案中的“板书设计”文本 -> 拼接 Prompt “黑板粉笔手绘风格，结构清晰，文字：{text}” -> 调用 CogView-3 生成图片。
- **功能 B：一键 PPT 生成 (核心亮点)**
  - **实现：** 不用 AI 生成 PPT 文件（太不可控），而是用 **Python 代码组装**。
  - **逻辑：**
    1. 解析教案 JSON 结构。
    2. 使用 `python-pptx` 加载预设底图模板。
    3. Page 1: 填入 `topic` 和 `teacher_name`。
    4. Page 2~N: 循环遍历 `sections`，左侧填文字，右侧插入生成的配图。
    5. Page End: 插入作业布置。
- **功能 C：素材库 (Asset Library)**
  - 所有生成的图片、板书图都会存入 `resource_library` 表。教师在编辑器右侧可以看到“我的素材”，直接拖拽复用，无需重新生成。

### 3.3 模块三：分层题库与智能解析 (Adaptive Assessment)

**增强点：** 难度分级、完整解析。

- **数据结构优化：** AI 输出必须严格遵循 Schema：

  ```
  {
    "difficulty": "advance", // 进阶
    "type": "multiple_choice",
    "question": "...",
    "options": ["A...", "B..."],
    "analysis": "本题考查...易错点在于...", 
    "tags": ["重点", "易错"]
  }
  ```

- **应用场景：** 生成完教案后，教师点击“生成配套测验”，选择“难度：拔高”，系统自动产出 5 道题，教师可一键加入 PPT 最后一页。

### 3.4 模块四：学情分析看板 (Visual Analytics)

**增强点：** ECharts 可视化、班级画像。

- **实现逻辑 (Mock Data 驱动):**
  - **班级画像：** 数据库预置一些虚拟学生的近期成绩。
  - **图表生成：** 后端计算统计数据，前端 ECharts 渲染：
    - *雷达图：* 识记、理解、应用、分析、综合（布鲁姆五维）。
    - *知识图谱热力图：* 红色代表该知识点全班错误率高。
  - **个性化推荐：** 基于热力图红色区域，自动触发 RAG 检索：“请推荐 3 个关于‘通分’的教学视频链接”。

## 4. 数据库设计 (MySQL Schema - Enhanced)

为了支持上述功能，我们需要扩展数据库表结构。

```
-- 1. 教案主表
CREATE TABLE lesson_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    topic VARCHAR(100),
    template_type VARCHAR(20) DEFAULT 'standard', -- 模板类型
    current_content JSON, -- 当前最新内容
    summary VARCHAR(500), -- 智能摘要
    created_at DATETIME,
    updated_at DATETIME
);

-- 2. 教案版本历史表 (用于 Diff 对比)
CREATE TABLE lesson_plan_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id INT,
    version_num INT, -- 版本号 v1, v2...
    content_snapshot JSON, -- 当时的完整内容
    change_reason VARCHAR(200), -- 修改原因(可选)
    created_at DATETIME
);

-- 3. 资源素材库 (实现复用与缓存)
CREATE TABLE resource_library (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    plan_id INT, -- 关联的教案
    resource_type ENUM('image', 'blackboard', 'exercise'),
    keyword_md5 VARCHAR(32), -- 用于去重检查
    content_url TEXT, -- 图片URL 或 题目JSON
    created_at DATETIME
);

-- 4. 学生学情表 (Mock数据)
CREATE TABLE student_stats (
    id INT PRIMARY KEY,
    class_id INT,
    student_name VARCHAR(50),
    knowledge_map JSON -- {"分数": 0.8, "小数": 0.4} 掌握度
);
```