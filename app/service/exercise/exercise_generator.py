# app/services/exercise_generator.py

from zhipuai import ZhipuAI
import chromadb
from typing import List
import json
from app.schema.exercise import ExerciseRequest, ExamExample, ExerciseItem
# 配置（请替换为您的实际配置，推荐使用环境变量）
ZHIPU_API_KEY = "YOUR_ZHIPU_API_KEY"
CHROMA_PERSIST_DIR = "./chroma_db"
KNOWLEDGE_COLLECTION_NAME = "teaching_knowledge_base"


class ExerciseGeneratorService:
    def __init__(self):
        # 初始化智谱客户端
        self.zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)

        # 初始化 ChromaDB 客户端，使用持久化存储
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.collection = self.chroma_client.get_or_create_collection(
            name=KNOWLEDGE_COLLECTION_NAME
            # 假设您已设置了默认的 Embedding 模型，否则需要在此处指定
        )

    # --- 阶段一：检索 (Retrieval) ---
    async def _retrieve_context(self, subject: str, topic_keywords: str) -> str:
        """
        根据关键词和学科，从 ChromaDB 中检索相关的知识内容。
        """
        # 1. 使用智谱的 Embedding API 将查询转化为向量
        # 注意：实际生产中，检索和存储的 embedding 模型必须一致
        try:
            # 假设使用智谱提供的 Embedding 模型
            embedding_response = self.zhipu_client.embeddings.create(
                model="embedding-2",  # 智谱推荐的 Embedding 模型
                input=f"请检索 {subject} 中关于 {topic_keywords} 的教学知识点和习题范例。"
            )
            query_vector = embedding_response.data[0].embedding
        except Exception as e:
            print(f"Embedding 生成失败: {e}")
            return "未能检索到相关知识。"

        # 2. 在 ChromaDB 中进行向量相似度搜索，并使用学科进行元数据过滤
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=5,  # 检索最相关的 5 个知识块
            where={"subject": subject}  # 利用元数据过滤，提高准确性
        )

        # 3. 提取和拼接检索到的文本
        retrieved_texts = results.get('documents', [[]])[0]
        if retrieved_texts:
            context = "\n---\n".join(retrieved_texts)
            return f"检索到的相关教学资料:\n{context}"
        else:
            return "未在知识库中检索到相关资料，将依靠大模型原有知识生成。"

    # --- 阶段二 & 三：增强 (Augmentation) 与 生成 (Generation) ---
    async def generate_questions_with_rag(
            self, req: ExerciseRequest
    ) -> List[ExerciseItem]:
        """
        执行 RAG 流程，调用 GLM-4.5-flash 生成结构化习题。
        """
        # 1. 检索上下文
        context = await self._retrieve_context(req.subject, req.topic_keywords)

        # 2. 构建系统 Prompt 和用户 Prompt

        # 系统 Prompt：定义角色的专业性和输出的格式要求 (JSON Mode 的核心)
        system_prompt = (
            "你是一名专业的学科教师和出题专家。你的任务是根据提供的知识内容和教师要求，"
            f"生成 {req.num_of_questions} 道结构化的练习题。"
            "你必须严格遵循下面的 JSON Schema 格式进行输出。不要输出任何额外的解释性文字。"
        )

        # 用户 Prompt：结合检索到的上下文和具体的生成要求
        user_prompt = f"""
        请严格根据以下要求生成练习题：
        1. **学科和主题：** {req.subject}，主题关键词：{req.topic_keywords}。
        2. **题型：** {req.exercise_type}。
        3. **难度：** {req.knowledge_level}。
        4. **知识上下文 (Context)：**
        ---
        {context}
        ---

        请使用 Context 中的知识点和要求，生成 {req.num_of_questions} 道习题。
        """

        # 3. 调用 GLM-4.5-flash 并启用 JSON Mode
        try:
            response = self.zhipu_client.chat.completions.create(
                model="glm-4.5-flash",  # 使用高性能模型
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # 关键：启用 response_format 并传入 Pydantic 模型生成的 schema
                response_format={
                    "type": "json_object",
                    "schema": ExamExample.model_json_schema()
                }
            )

            # 4. 解析 JSON 输出
            json_text = response.choices[0].message.content.strip()
            # 使用 Pydantic 进行验证和解析
            exercise_list_model = ExamExample.model_validate_json(json_text)

            return exercise_list_model.exercises

        except Exception as e:
            print(f"调用 GLM-4.5-flash 失败或 JSON 解析错误: {e}")
            # 返回空列表或抛出 HTTP 错误
            return []