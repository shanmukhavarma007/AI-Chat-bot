import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import chatbot
from config import settings
from models import (
    ErrorResponse,
    HealthResponse,
    WebhookRequest,
    WebhookResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="GLM-4.7 NIM Chatbot", version="1.0.0")

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
        result = await chatbot.process_message(
            user_id=request.user_id,
            message=request.message,
            system_prompt=request.system_prompt,
            enable_thinking=request.enable_thinking,
        )
        return WebhookResponse(
            user_id=request.user_id,
            reply=result["reply"],
            thinking_trace=result["thinking_trace"],
            tokens_used=result["tokens_used"],
            session_length=result["session_length"],
        )
    except chatbot.NIMTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Model response timed out, try a shorter message",
        )
    except chatbot.NIMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Too many requests, try again shortly",
        )
    except chatbot.NIMUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in webhook: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)