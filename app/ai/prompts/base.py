from dataclasses import Field

from pydantic import BaseModel


class BasePrompt(BaseModel):
    systemPrompt: str=Field(...)
    defaultPrompt: str=Field(...)