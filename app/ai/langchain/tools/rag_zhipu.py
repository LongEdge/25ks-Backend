from typing import List, Any

import requests
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.tools import tool
from pydantic import Field

TEST_KEY="REMOVED_ZHIPU_API_KEY"

class ZhipuKnowledgeRetriever(BaseRetriever):
    api_key: str = Field(...)
    knowledge_ids: List[str] = Field(...)
    top_k: int = Field(default=12)
    recall_method: str = Field(default="mixed")
    rerank: bool = Field(default=False)

    def _get_relevant_documents(self, query: str) -> List[Document]:
        payload = {
            "query": query,
            "knowledge_ids": self.knowledge_ids,
            "top_k": self.top_k,
            "recall_method": self.recall_method,
            "rerank_status": 1 if self.rerank else 0,
        }

        resp = requests.post(
            "https://open.bigmodel.cn/api/llm-application/open/knowledge/retrieve",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()

        data = resp.json()

        return [
            Document(
                page_content=item["text"],
                metadata=item,
            )
            for item in data.get("data", [])
        ]

retriever = ZhipuKnowledgeRetriever(
    api_key=TEST_KEY,
    knowledge_ids=["1999002185098272768"],
    top_k=5,
    recall_method="mixed",
    rerank=True,
)

# docs = retriever.invoke("赤壁赋的写作背景")
# print(docs)

@tool
def zhipu_rag_search(query: str) -> str:
    """
    使用智谱知识库检索问题背景知识，返回与问题相关的文本内容
    """
    docs = retriever.invoke(query)

    if not docs:
        return "未检索到相关知识"

    # 只返回文本，LLM 才能用
    return "\n\n".join(
        f"【文档 {i+1}】{doc.page_content}"
        for i, doc in enumerate(docs)
    )