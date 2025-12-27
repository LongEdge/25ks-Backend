from langchain_core.tools import Tool


#===============纯KG层===================

from app.core.database import get_duckdb
class KnowledgeGraph:
    @staticmethod
    def get_entity(entity_name: str):
        con = get_duckdb()
        return con.execute("""
            SELECT 属性, 值, match_score, is_core
            FROM kg
            WHERE 实体 LIKE ?
            ORDER BY is_core DESC, match_score DESC
        """, [f"{entity_name}%"]).fetchdf()

    @staticmethod
    def search(attr: str, value: str):
        con = get_duckdb()
        return con.execute("""
            SELECT 实体, 属性, 值
            FROM kg
            WHERE 属性 = ? AND 值 = ?
            LIMIT 50
        """, [attr, value]).fetchdf()

    @staticmethod
    def delete_entity(entity_name: str):
        con = get_duckdb()
        con.execute("""
            DELETE FROM kg
            WHERE 实体 LIKE ?
        """, [f"{entity_name}%"])
#
# @router.get("/entity")
# def get_entity(name: str = Query(..., description="实体名")):
#     df = KnowledgeGraph.get_entity(name)
#     return df.to_dict(orient="records")
#
# @router.get("/search")
# def search(attr: str, value: str):
#     df = KnowledgeGraph.search(attr, value)
#     return df.to_dict(orient="records")

from typing import Any, Dict, List, Optional

def kg_get_entity(name: str, top_k: int = 30, core_only: bool = False) -> List[Dict[str, Any]]:
    """
    查询实体的属性列表。
    返回：[{attr,value,match_score,is_core}, ...]
    """
    df = KnowledgeGraph.get_entity(name)

    if core_only and "is_core" in df.columns:
        df = df[df["is_core"] == 1]

    if top_k is not None:
        df = df.head(int(top_k))

    # 统一字段名，给 LLM 友好一点
    cols = [c for c in ["属性", "值", "match_score", "is_core"] if c in df.columns]
    df = df[cols].rename(columns={"属性": "attr", "值": "value"})

    return df.to_dict(orient="records")


def kg_search(attr: str, value: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    通过属性+值反查实体。
    返回：[{entity, attr, value}, ...]
    """
    df = KnowledgeGraph.search(attr, value)

    if limit is not None:
        df = df.head(int(limit))

    # 统一字段名
    df = df.rename(columns={"实体": "entity", "属性": "attr", "值": "value"})
    return df.to_dict(orient="records")

#===========REGISTER=======================
kg_get_entity_tool = Tool(
    name="kg_get_entity",
    description="查询知识图谱中某个实体的属性信息",
    func=kg_get_entity,
)

kg_search_tool = Tool(
    name="kg_search",
    description="通过属性和值反向查找实体",
    func=kg_search,
)

KG_TOOLS = [kg_get_entity_tool, kg_search_tool]

"""
知识图谱相关工具
"""
