# rag-python/app/schemas.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    system_prompt: str | None = None