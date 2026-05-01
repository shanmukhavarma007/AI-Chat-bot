# Product Requirements Document
## AI Chatbot with NVIDIA NIM API (GLM-4.7) + Webhook Integration

---

**Document Version:** 2.0  
**Author:** Shanmukha Varma  
**Date:** May 2026  
**Status:** Draft  
**Project Type:** Portfolio Project — AI Automation Specialist Role  
**Model:** `z-ai/glm-4.7` via NVIDIA NIM

---

## 1. Overview

### 1.1 Project Summary

This project is a production-ready AI chatbot built in Python that uses **GLM-4.7 by Z.ai** (hosted on NVIDIA NIM) as its LLM backbone and exposes a **webhook endpoint** for real-world integration. The bot can be connected to any external platform (Telegram, Slack, web forms, n8n, Zapier) via HTTP POST webhooks, making it a genuine end-to-end automation artifact.

GLM-4.7 is a 358B-parameter multilingual reasoning model with built-in **Interleaved Thinking** — it reasons before every response, making it significantly stronger than standard chat models for agentic and coding tasks.

### 1.2 Why GLM-4.7

| Feature | GLM-4.7 Advantage |
|---|---|
| Reasoning | Interleaved Thinking — reasons before every response |
| Context window | 131,072 tokens (input + output) |
| Tool use | Native tool/function calling support |
| Coding | Strong multilingual coding and agentic workflow performance |
| Portfolio edge | Uncommon model choice — differentiates from typical OpenAI projects |
| Benchmarks | AIME 2025: 95.7%, GPQA-Diamond: 85.7%, LiveCodeBench: 84.9% |

### 1.3 Why This Project

This project directly demonstrates the three core requirements of the **AI Automation Specialist** job description:

| Job Requirement | What This Project Proves |
|---|---|
| Python | Entire backend written in Python |
| AI/ML | Real LLM integration via NVIDIA NIM (GLM-4.7) |
| API Integration | Webhook server + external NIM API calls |
| Automation Tools | Webhook connects to n8n, Zapier, or Telegram |

### 1.4 Goals

- Build a working AI chatbot powered by GLM-4.7 via NVIDIA NIM
- Expose a webhook so external tools can trigger the chatbot programmatically
- Leverage GLM-4.7's Interleaved Thinking for higher-quality responses
- Maintain conversation history per user session
- Deploy it publicly (Railway / Render / Fly.io) so it can be live-demoed in interviews

---

## 2. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Language | Python 3.11+ | Job requirement |
| LLM API | NVIDIA NIM — `z-ai/glm-4.7` | 358B reasoning model, Interleaved Thinking |
| Web Framework | FastAPI | Async, production-grade, auto-docs at `/docs` |
| HTTP Client | `httpx` | Async HTTP calls to NIM API |
| Data Validation | Pydantic v2 | Input validation on webhook payloads |
| Deployment | Railway or Render (free tier) | Live public URL for portfolio |
| Environment Secrets | `python-dotenv` | Secure API key management |
| Optional Frontend | Telegram Bot (via `python-telegram-bot`) | Real-world integration demo |

---

## 3. About the Model — GLM-4.7

**Model ID (NVIDIA NIM):** `z-ai/glm-4.7`  
**API Base URL:** `https://integrate.api.nvidia.com/v1`  
**Developer:** Z.ai (formerly THUDM / Zhipu AI)  
**Parameters:** 358B  
**Context Length:** 131,072 tokens (input + output)  
**License:** NVIDIA Open Model License (commercial use permitted)

### 3.1 Key Capabilities

**Interleaved Thinking** — The model thinks step-by-step before every response and every tool call. This improves instruction following and generation quality automatically.

**Preserved Thinking** — In multi-turn conversations, thinking blocks are retained across turns, reducing information loss in agentic coding sessions.

**Turn-level Thinking Control** — Thinking can be enabled/disabled per-turn via `chat_template_kwargs`. Disable for lightweight requests, enable for complex reasoning tasks.

**Tool Calling** — Native support for function/tool calling, making it ideal for agentic automation workflows.

### 3.2 Benchmark Highlights

| Benchmark | GLM-4.7 Score |
|---|---|
| AIME 2025 | 95.7% |
| HMMT Feb 2025 | 97.1% |
| GPQA-Diamond | 85.7% |
| LiveCodeBench-v6 | 84.9% |
| τ²-Bench (Agentic) | 87.4% |

---

## 4. System Architecture

```
External Trigger (Telegram / n8n / Zapier / curl)
        │
        ▼
  POST /webhook
  { "user_id": "...", "message": "...", "enable_thinking": true }
        │
        ▼
  FastAPI Webhook Server (Python)
        │
        ├── Validates payload (Pydantic)
        ├── Loads session history for user_id
        ├── Appends user message to history
        │
        ▼
  NVIDIA NIM API
  Model: z-ai/glm-4.7
  Endpoint: https://integrate.api.nvidia.com/v1/chat/completions
        │
        ▼
  GLM-4.7 Response
  (with optional reasoning/thinking trace)
        │
        ├── Appends assistant reply to history
        ├── Strips thinking block from public reply
        ├── Returns JSON response
        │
        ▼
  {
    "reply": "...",
    "user_id": "...",
    "tokens_used": ...,
    "thinking_trace": "..." (if requested)
  }
```

---

## 5. Functional Requirements

### 5.1 Webhook Endpoint

**Endpoint:** `POST /webhook`

**Request Body:**
```json
{
  "user_id": "user_123",
  "message": "Write a Python function to reverse a linked list.",
  "system_prompt": "You are a helpful coding assistant.",
  "enable_thinking": true
}
```

**Response:**
```json
{
  "user_id": "user_123",
  "reply": "Here's a Python function to reverse a linked list...",
  "thinking_trace": "Let me think through the node traversal logic...",
  "tokens_used": 312,
  "session_length": 3
}
```

**Validation Rules:**
- `user_id` — required, string, max 64 chars
- `message` — required, string, max 4000 chars, strip HTML
- `system_prompt` — optional, string, max 500 chars
- `enable_thinking` — optional, boolean, default `true`

### 5.2 GLM-4.7 NIM Integration

- Call NVIDIA NIM API using the OpenAI-compatible `/v1/chat/completions` endpoint
- Model ID: `z-ai/glm-4.7`
- Pass full conversation history in `messages[]` array for multi-turn context
- Control thinking per-turn via `chat_template_kwargs` parameter
- Handle rate limits with exponential backoff retry (max 3 retries)
- Timeout: 45 seconds per request (358B model — allow more time than smaller models)

**Thinking control in payload:**
```python
# Enable thinking (default — for complex tasks)
"chat_template_kwargs": {"thinking": True}

# Disable thinking (for simple/fast queries)
"chat_template_kwargs": {"thinking": False}
```

### 5.3 Session / Conversation Memory

- Store conversation history in-memory (Python dict keyed by `user_id`)
- Keep last **10 message pairs** per user (GLM-4.7's 131K context makes this very generous)
- Session expires after **30 minutes** of inactivity
- Preserve thinking blocks in history when `enable_thinking=True` (GLM-4.7's Preserved Thinking feature)
- Each session stores: `[{"role": "user/assistant", "content": "..."}]`

### 5.4 Health Check Endpoint

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok",
  "model": "z-ai/glm-4.7",
  "context_window": 131072,
  "active_sessions": 3
}
```

### 5.5 Optional: Telegram Integration

- If `TELEGRAM_BOT_TOKEN` is set, the bot also listens to Telegram messages
- Telegram message handler calls the same internal chatbot logic
- Thinking traces are hidden from Telegram replies by default (too verbose for chat)
- Allows live demo via Telegram bot during interviews

---

## 6. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Response time | < 10 seconds for typical messages (358B model — larger latency expected) |
| Uptime | 99%+ on Railway/Render free tier |
| Security | API key never exposed in code or responses |
| Input safety | Strip HTML, enforce max length, reject empty messages |
| Error handling | Never return a 500 without a safe fallback message |
| Thinking traces | Never leak internal reasoning to end users unless explicitly requested |

---

## 7. Project File Structure

```
glm47-chatbot/
├── main.py                   # FastAPI app entrypoint
├── chatbot.py                # GLM-4.7 NIM API call logic + session management
├── models.py                 # Pydantic request/response models
├── config.py                 # Settings loaded from .env
├── utils/
│   ├── sanitize.py           # Input cleaning utilities
│   └── retry.py              # Exponential backoff wrapper
├── telegram_bot.py           # Optional Telegram integration
├── requirements.txt
├── .env.example
├── Dockerfile                # For Railway/Render deployment
├── README.md
└── tests/
    ├── test_webhook.py
    └── test_chatbot.py
```

---

## 8. Environment Variables

```env
# Required
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxx

# Model config
NIM_MODEL=z-ai/glm-4.7
NIM_BASE_URL=https://integrate.api.nvidia.com/v1

# Optional — Telegram integration
TELEGRAM_BOT_TOKEN=xxxxxxxxxx

# Optional — tuning
MAX_HISTORY_PAIRS=10
SESSION_TIMEOUT_MINUTES=30
DEFAULT_ENABLE_THINKING=true
REQUEST_TIMEOUT_SECONDS=45
```

---

## 9. Error Handling

| Scenario | HTTP Status | Response |
|---|---|---|
| Missing required field | 422 | Pydantic validation error detail |
| NIM API unreachable | 503 | `{"error": "AI service temporarily unavailable"}` |
| NIM API rate limit | 429 | `{"error": "Too many requests, try again shortly"}` |
| Message too long | 400 | `{"error": "Message exceeds 4000 character limit"}` |
| Empty message | 400 | `{"error": "Message cannot be empty"}` |
| NIM timeout (>45s) | 504 | `{"error": "Model response timed out, try a shorter message"}` |

---

## 10. API Reference — GLM-4.7 via NVIDIA NIM

```python
import httpx

NVIDIA_API_KEY = "nvapi-xxxx"

headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "z-ai/glm-4.7",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain how recursion works in Python."}
    ],
    "temperature": 0.6,
    "max_tokens": 1024,
    "chat_template_kwargs": {
        "thinking": True   # Enable Interleaved Thinking
    }
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=45.0
    )
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    # Thinking trace is returned in reasoning_content field
    thinking = data["choices"][0]["message"].get("reasoning_content", "")
```

### 10.1 Turn-Level Thinking Control

```python
# Complex task — enable thinking for better quality
payload["chat_template_kwargs"] = {"thinking": True}

# Simple/fast query — disable thinking to reduce latency
payload["chat_template_kwargs"] = {"thinking": False}
```

### 10.2 Tool Calling Example

GLM-4.7 supports native tool calling for future agentic workflows:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

payload["tools"] = tools
payload["tool_choice"] = "auto"
```

---

## 11. Development Milestones

| Milestone | Tasks | Est. Time |
|---|---|---|
| **M1 — Core Chatbot** | GLM-4.7 NIM API call, basic Python script, test with curl | 1 day |
| **M2 — Webhook Server** | FastAPI app, `/webhook` endpoint, Pydantic validation, `/health` | 1 day |
| **M3 — Session Memory** | In-memory history, sliding window, Preserved Thinking support | 0.5 day |
| **M4 — Thinking Control** | Per-request `enable_thinking` flag, strip thinking from public replies | 0.5 day |
| **M5 — Error Handling** | Retries, timeouts, safe error responses, input sanitization | 0.5 day |
| **M6 — Deployment** | Dockerfile, deploy to Railway, public URL working | 1 day |
| **M7 — Telegram (optional)** | Telegram bot handler, live demo setup | 1 day |
| **M8 — README + Tests** | README with usage examples, basic unit tests | 0.5 day |

**Total estimated time: 6–7 days**

---

## 12. Testing Plan

### Manual Testing

Test the webhook with thinking enabled:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_1",
    "message": "What is GLM-4.7 and why is it special?",
    "enable_thinking": true
  }'
```

Test multi-turn conversation with Preserved Thinking:

```bash
# Turn 1
curl -X POST http://localhost:8000/webhook \
  -d '{"user_id": "u1", "message": "My name is Shanmukha. I am building a chatbot."}'

# Turn 2 — bot should remember context across turns
curl -X POST http://localhost:8000/webhook \
  -d '{"user_id": "u1", "message": "What project am I working on?"}'
```

Test fast query with thinking disabled:

```bash
curl -X POST http://localhost:8000/webhook \
  -d '{"user_id": "u2", "message": "What is 12 * 8?", "enable_thinking": false}'
```

### Automated Tests

- Unit test: input sanitization functions
- Unit test: session history sliding window logic
- Unit test: thinking trace extraction from NIM response
- Integration test: mock NIM API response, assert correct output format
- Integration test: 422 on invalid payload

---

## 13. Deployment Guide (Railway)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and init
railway login
railway init

# 3. Set environment variables
railway variables set NVIDIA_API_KEY=nvapi-xxxx
railway variables set NIM_MODEL=z-ai/glm-4.7

# 4. Deploy
railway up

# Public URL:  https://your-app.railway.app/webhook
# API Docs:    https://your-app.railway.app/docs
```

---

## 14. Portfolio Presentation Notes

When showcasing this project to interviewers, highlight:

- **GLM-4.7 model choice** — 358B model with Interleaved Thinking; uncommon and technically impressive compared to typical OpenAI demos
- **Interleaved Thinking** — the model reasons before every response; show the `thinking_trace` field in responses to demonstrate this live
- **Turn-level thinking control** — shows understanding of LLM inference optimization (disable thinking for speed on simple queries)
- **Python + FastAPI** — not just no-code tools; real production-grade server code
- **Webhook design** — makes the bot pluggable into any automation platform (n8n, Zapier, Make)
- **Session memory + Preserved Thinking** — demonstrates understanding of stateful, multi-turn AI conversations
- **Security** — API key in env vars, input sanitization, thinking traces never exposed to end users by default
- **Live deployment** — shareable URL that works in real time during an interview

---

## 15. Future Enhancements

- Persistent session storage with Redis or SQLite (vs in-memory)
- Webhook authentication via HMAC signature verification
- Agentic tool calling — expose tools (web search, calculator) to GLM-4.7 for autonomous task completion
- Streaming responses via Server-Sent Events (SSE)
- Admin dashboard to view active sessions and usage stats
- Rate limiting per `user_id` to prevent abuse
- Slack integration alongside Telegram
- Upgrade path to `z-ai/glm-5` when needed (744B MoE, same API format, same endpoint structure)

---

*Built as a portfolio project targeting AI Automation Specialist roles — demonstrating Python, GLM-4.7 LLM integration via NVIDIA NIM, webhook design, Interleaved Thinking, and production deployment.*
