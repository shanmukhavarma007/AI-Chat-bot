import pytest
import time
from unittest.mock import patch, AsyncMock

import chatbot
from utils import sanitize
from utils.retry import async_retry
from config import settings


class TestSanitize:
    def test_strip_html_removes_tags(self):
        text = "<p>Hello <b>World</b></p>"
        result = sanitize.strip_html(text)
        assert result == "Hello World"

    def test_strip_html_decodes_entities(self):
        text = "&lt;script&gt;alert('xss')&lt;/script&gt;"
        result = sanitize.strip_html(text)
        assert result == "<script>alert('xss')</script>"

    def test_sanitize_message_raises_on_empty_string(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize.sanitize_message("   ")

    def test_sanitize_message_truncates_to_max_length(self):
        text = "a" * 5000
        result = sanitize.sanitize_message(text, max_length=4000)
        assert len(result) == 4000


class TestSession:
    def test_session_sliding_window_keeps_last_10_pairs(self):
        chatbot._sessions.clear()
        for i in range(15):
            chatbot.update_session(
                "test_user",
                {"content": f"user message {i}"},
                {"content": f"assistant reply {i}"},
            )

        history = chatbot.get_session("test_user")
        assert len(history) == settings.MAX_HISTORY_PAIRS

    def test_session_expires_after_timeout(self):
        chatbot._sessions.clear()
        chatbot._sessions["test_user"] = {
            "history": [{"user": {"content": "test"}, "assistant": {"content": "reply"}}],
            "last_activity": time.time() - (settings.SESSION_TIMEOUT_MINUTES * 60 + 10),
        }

        chatbot.cleanup_expired_sessions()

        assert "test_user" not in chatbot._sessions

    def test_thinking_stored_in_history_when_enabled(self):
        chatbot._sessions.clear()
        user_msg = {"content": "test message"}
        assistant_msg = {"content": "reply", "thinking_trace": "thinking..."}

        chatbot.update_session("user1", user_msg, assistant_msg)

        history = chatbot.get_session("user1")
        assert history[0]["assistant"].get("thinking_trace") == "thinking..."


class TestRetry:
    @pytest.mark.asyncio
    async def test_retry_retries_on_timeout_exception(self):
        import httpx

        call_count = 0

        @async_retry(max_attempts=3, base_delay=0.1)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("timeout")
            return {"reply": "success", "thinking_trace": None, "tokens_used": 10}

        result = await failing_function()

        assert call_count == 3
        assert result["reply"] == "success"

    @pytest.mark.asyncio
    async def test_retry_reraises_after_max_attempts(self):
        import httpx

        @async_retry(max_attempts=3, base_delay=0.1)
        async def always_fails():
            raise httpx.TimeoutException("always times out")

        with pytest.raises(httpx.TimeoutException):
            await always_fails()