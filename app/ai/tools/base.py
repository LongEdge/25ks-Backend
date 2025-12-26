"""
Tool 抽象 & 注册器
"""

KG_TOOLS_META = [
    {
        "name": "kg_get_entity",
        "description": "查询某个实体的属性信息。用于知识图谱增强检索。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "实体名，例如：世界波"},
                "top_k": {"type": "integer", "description": "返回最多多少条属性", "default": 30},
                "core_only": {"type": "boolean", "description": "是否只返回核心属性", "default": False},
            },
            "required": ["name"],
        },
    },
    {
        "name": "kg_search",
        "description": "通过属性+值反查实体列表，例如：适用领域=足球。",
        "parameters": {
            "type": "object",
            "properties": {
                "attr": {"type": "string", "description": "属性名，例如：适用领域"},
                "value": {"type": "string", "description": "属性值，例如：足球"},
                "limit": {"type": "integer", "description": "返回条数", "default": 50},
            },
            "required": ["attr", "value"],
        },
    },
]
