import logging
import time
from typing import Optional

import httpx

from config import settings
from utils.retry import async_retry
from utils.sanitize import sanitize_message, sanitize_system_prompt

logger = logging.getLogger(__name__)


class NIMTimeoutError(Exception):
    pass


class NIMUnavailableError(Exception):
    pass


class NIMRateLimitError(Exception):
    pass


_sessions: dict = {}


def get_session(user_id: str) -> list[dict]:
    if user_id not in _sessions:
        _sessions[user_id] = {"history": [], "last_activity": time.time()}
    _sessions[user_id]["last_activity"] = time.time()
    return _sessions[user_id]["history"]


def update_session(user_id: str, user_msg: dict, assistant_msg: dict):
    if user_id not in _sessions:
        _sessions[user_id] = {"history": [], "last_activity": time.time()}
    session = _sessions[user_id]
    session["history"].append({"user": user_msg, "assistant": assistant_msg})
    if len(session["history"]) > settings.MAX_HISTORY_PAIRS:
        session["history"] = session["history"][-settings.MAX_HISTORY_PAIRS :]
    session["last_activity"] = time.time()


def cleanup_expired_sessions():
    current_time = time.time()
    timeout_seconds = settings.SESSION_TIMEOUT_MINUTES * 60
    expired_users = [
        user_id
        for user_id, session in _sessions.items()
        if current_time - session["last_activity"] > timeout_seconds
    ]
    for user_id in expired_users:
        del _sessions[user_id]


def active_session_count() -> int:
    return len(_sessions)


@async_retry(max_attempts=3)
async def call_glm47(messages: list[dict], enable_thinking: bool) -> dict:
    url = f"{settings.NIM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.NIM_MODEL,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 1024,
        "chat_template_kwargs": {"thinking": enable_thinking},
    }

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            raise NIMTimeoutError("NIM API request timed out")
        except httpx.ConnectError:
            raise NIMUnavailableError("NIM API is unavailable")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise NIMRateLimitError("NIM API rate limit exceeded")
            raise

    reply = data["choices"][0]["message"]["content"]
    thinking_trace = data["choices"][0]["message"].get("reasoning_content", None)
    tokens_used = data["usage"]["total_tokens"]

    return {"reply": reply, "thinking_trace": thinking_trace, "tokens_used": tokens_used}


async def process_message(
    user_id: str,
    message: str,
    system_prompt: Optional[str] = None,
    enable_thinking: bool = True,
) -> dict:
    cleanup_expired_sessions()

    message = sanitize_message(message)

    if system_prompt:
        system_prompt = sanitize_system_prompt(system_prompt)

    session_history = get_session(user_id)

    messages_to_send = []
    if system_prompt:
        messages_to_send.append({"role": "system", "content": system_prompt})
    for pair in session_history:
        messages_to_send.append({"role": "user", "content": pair["user"]["content"]})
        messages_to_send.append({"role": "assistant", "content": pair["assistant"]["content"]})
    messages_to_send.append({"role": "user", "content": message})

    result = await call_glm47(messages_to_send, enable_thinking)

    reply = result["reply"]
    thinking_trace = result["thinking_trace"] if enable_thinking else None
    tokens_used = result["tokens_used"]

    user_msg = {"content": message}
    assistant_msg = {"content": reply}
    if enable_thinking and thinking_trace:
        assistant_msg["thinking_trace"] = thinking_trace

    update_session(user_id, user_msg, assistant_msg)

    new_session_length = len(get_session(user_id))

    return {
        "reply": reply,
        "thinking_trace": thinking_trace,
        "tokens_used": tokens_used,
        "session_length": new_session_length,
    }