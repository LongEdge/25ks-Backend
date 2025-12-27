from typing import List, Any

from langchain_classic import requests
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.core.config import settings


class ZhipuKnowledgeRetriever(BaseRetriever):
    def __init__(self, api_key: str, knowledge_ids: list[str], top_k: int = 8, recall_method: str = "mixed",
                 rerank: bool = False, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.api_key = api_key
        self.knowledge_ids = knowledge_ids
        self.top_k = top_k
        self.recall_method = recall_method
        self.rerank = rerank

    def _get_relevant_documents(self, query: str) -> List[Document]:
        payload = {
            "query": query,
            "knowledge_ids": self.knowledge_ids,
            "top_k": self.top_k,
            "recall_method": self.recall_method,
            "rerank_status": 1 if self.rerank else 0,
        }

        resp = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/knowledge/retrieve",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        docs = []
        for item in data.get("data", []):
            docs.append(
                Document(
                    page_content=item["content"],
                    metadata={
                        "score": item.get("score"),
                        "document_id": item.get("document_id"),
                        "knowledge_id": item.get("knowledge_id"),
                    },
                )
            )
        return docs


retriever = ZhipuKnowledgeRetriever(
    api_key=settings.AI_API_KEY,
    knowledge_ids=["1999002185098272768"],
    top_k=8,
    recall_method="mixed",
    rerank=True,
)

docs = retriever.get_relevant_documents("赤壁赋的写作背景")
