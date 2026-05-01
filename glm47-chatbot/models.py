from typing import Optional

from pydantic import BaseModel, Field


class WebhookRequest(BaseModel):
    user_id: str = Field(..., max_length=64)
    message: str = Field(..., min_length=1, max_length=4000)
    system_prompt: Optional[str] = Field(default=None, max_length=500)
    enable_thinking: bool = Field(default=True)


class WebhookResponse(BaseModel):
    user_id: str
    reply: str
    thinking_trace: Optional[str] = None
    tokens_used: int
    session_length: int


class HealthResponse(BaseModel):
    status: str = "ok"
    model: str
    context_window: int = 131072
    active_sessions: int


class ErrorResponse(BaseModel):
    error: str