from typing import List

from pydantic import BaseModel

from app.core.config import settings

test_headers={
    "Authorization": f"Bearer REMOVED_ZHIPU_API_KEY",
    "Content-Type": "application/json"
}

headers = {
    "Authorization": f"Bearer {settings.AI_API_KEY}",
    "Content-Type": "application/json"
}

class Message(BaseModel):
    role:str
    content:str

def get_chat_model_list() -> List[str]:
    return ["glm-4-flashx-250414"]

def get_chat_url()->str:
    return "https://open.bigmodel.cn/api/paas/v4/chat/completions"

def get_pic_model_list() -> List[str]:
    return ["cogview-3-flash"]

