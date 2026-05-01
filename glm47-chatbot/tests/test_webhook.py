import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock

from httpx import AsyncClient, ASGITransport

import main


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=main.app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_returns_200(client):
    with patch("chatbot.active_session_count", return_value=0):
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "z-ai/glm-4.7"


@pytest.mark.asyncio
async def test_webhook_missing_user_id_returns_422(client):
    response = await client.post("/webhook", json={"message": "hello"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_webhook_empty_message_returns_400_or_422(client):
    response = await client.post(
        "/webhook",
        json={"user_id": "user123", "message": ""}
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_webhook_valid_payload_returns_correct_structure(client):
    mock_result = {
        "reply": "Hello!",
        "thinking_trace": "Thinking...",
        "tokens_used": 10,
        "session_length": 1,
    }
    with patch("chatbot.process_message", new_callable=AsyncMock, return_value=mock_result):
        response = await client.post(
            "/webhook",
            json={
                "user_id": "user123",
                "message": "Hello",
                "enable_thinking": True,
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "reply" in data
    assert "tokens_used" in data
    assert "session_length" in data


@pytest.mark.asyncio
async def test_webhook_thinking_trace_none_when_disabled(client):
    mock_result = {
        "reply": "Hello!",
        "thinking_trace": None,
        "tokens_used": 10,
        "session_length": 1,
    }
    with patch("chatbot.process_message", new_callable=AsyncMock, return_value=mock_result):
        response = await client.post(
            "/webhook",
            json={
                "user_id": "user123",
                "message": "Hello",
                "enable_thinking": False,
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert data["thinking_trace"] is None


@pytest.mark.asyncio
async def test_webhook_nim_timeout_returns_504(client):
    from chatbot import NIMTimeoutError

    with patch(
        "chatbot.process_message",
        new_callable=AsyncMock,
        side_effect=NIMTimeoutError("timeout")
    ):
        response = await client.post(
            "/webhook",
            json={"user_id": "user123", "message": "Hello"}
        )
    assert response.status_code == 504


@pytest.mark.asyncio
async def test_webhook_nim_unavailable_returns_503(client):
    from chatbot import NIMUnavailableError

    with patch(
        "chatbot.process_message",
        new_callable=AsyncMock,
        side_effect=NIMUnavailableError("unavailable")
    ):
        response = await client.post(
            "/webhook",
            json={"user_id": "user123", "message": "Hello"}
        )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_root_returns_200(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data