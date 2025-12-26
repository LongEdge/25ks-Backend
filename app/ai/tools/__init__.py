"""
AI 可调用的能力集合
"""
from app.ai.tools.knowledgeGraph import kg_get_entity, kg_search

TOOLS_REGISTRY = {
    "kg_get_entity": kg_get_entity,
    "kg_search": kg_search,
}
