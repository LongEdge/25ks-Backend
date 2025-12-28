def escape_curly_braces(text: str) -> str:
    """
    将字符串中的所有花括号转义：
    { -> {{
    } -> }}

    适用于 LangChain / Jinja / format 场景中，
    需要把 JSON / 示例文本当作字面量的情况。
    """
    if not text:
        return text
    return text.replace("{", "{{").replace("}", "}}")
