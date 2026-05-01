import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import chatbot
import telegram_bot
from config import settings
from models import (
    ErrorResponse,
    HealthResponse,
    WebhookRequest,
    WebhookResponse,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_bot.start_webhook_mode()
    yield
    await telegram_bot.stop_webhook_mode()


app = FastAPI(
    title="GLM-4.7 NIM Chatbot",
    version="1.0.0",
    description="AI chatbot powered by z-ai/glm-4.7 via NVIDIA NIM",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "GLM-4.7 NIM Chatbot is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"], response_model=HealthResponse)
async def health():
    return HealthResponse(
        model=settings.NIM_MODEL,
        active_sessions=chatbot.active_session_count(),
    )


@app.post("/webhook", tags=["Chatbot"], response_model=WebhookResponse)
async def webhook(request: WebhookRequest):
    try:
        result = await asyncio.wait_for(
            chatbot.process_message(
                user_id=request.user_id,
                message=request.message,
                system_prompt=request.system_prompt,
                enable_thinking=request.enable_thinking,
            ),
            timeout=40.0,
        )
        return WebhookResponse(
            user_id=request.user_id,
            reply=result["reply"],
            thinking_trace=result["thinking_trace"],
            tokens_used=result["tokens_used"],
            session_length=result["session_length"],
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"error": "Response took too long. Try a shorter question."},
        )
    except chatbot.NIMTimeoutError:
        return JSONResponse(
            status_code=504, content={"error": "Model response timed out, try a shorter message"}
        )
    except chatbot.NIMRateLimitError:
        return JSONResponse(status_code=429, content={"error": "Too many requests, try again shortly"})
    except chatbot.NIMUnavailableError:
        return JSONResponse(status_code=503, content={"error": "AI service temporarily unavailable"})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error in webhook: {e}", exc_info=True)
        return JSONResponse(status_code=503, content={"error": "Service temporarily unavailable"})


@app.post("/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    await telegram_bot.process_update(data)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)