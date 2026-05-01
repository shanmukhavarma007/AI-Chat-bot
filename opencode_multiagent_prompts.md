# OpenCode Multi-Agent Prompts
## GLM-4.7 NIM Chatbot — Full Project Implementation
> PRD: AI Chatbot with NVIDIA NIM API (GLM-4.7) + Webhook Integration
> Run these prompts sequentially in OpenCode. Each targets a specific sub-agent.

---

## PHASE 1 — Project Scaffold

### @planner — Project Architecture & Task Breakdown

```
@planner

You are planning the full implementation of a production-ready AI chatbot project. Study
this spec carefully and produce a concrete execution plan.

PROJECT: GLM-4.7 NIM Chatbot with Webhook Integration
TECH: Python 3.11+, FastAPI, httpx, Pydantic v2, python-dotenv

REQUIRED FILE STRUCTURE (do not deviate):
glm47-chatbot/
├── main.py
├── chatbot.py
├── models.py
├── config.py
├── utils/
│   ├── sanitize.py
│   └── retry.py
├── telegram_bot.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── README.md
└── tests/
    ├── test_webhook.py
    └── test_chatbot.py

KEY REQUIREMENTS:
- LLM: z-ai/glm-4.7 via NVIDIA NIM (https://integrate.api.nvidia.com/v1)
- Endpoint: POST /webhook (Pydantic-validated, per spec below)
- Endpoint: GET /health
- Session memory: in-memory dict, 10 message pairs per user, 30-min expiry
- GLM-4.7 Interleaved Thinking: enable/disable per-request via chat_template_kwargs
- Thinking traces: extracted from reasoning_content field, never leaked in public reply
- Preserved Thinking: thinking blocks retained in multi-turn history
- Retry: exponential backoff, max 3 retries
- Timeout: 45 seconds per request
- Input sanitization: strip HTML, enforce max lengths
- Error responses: never return 500 without safe fallback message

WEBHOOK PAYLOAD:
{
  "user_id": "string (required, max 64 chars)",
  "message": "string (required, max 4000 chars, strip HTML)",
  "system_prompt": "string (optional, max 500 chars)",
  "enable_thinking": "bool (optional, default true)"
}

WEBHOOK RESPONSE:
{
  "user_id": "string",
  "reply": "string",
  "thinking_trace": "string (only if enable_thinking=true)",
  "tokens_used": "int",
  "session_length": "int"
}

ERROR RESPONSES:
- 422: Pydantic validation error
- 503: NIM API unreachable
- 429: NIM rate limit hit
- 400: message too long or empty
- 504: NIM timeout

Produce:
1. Ordered task list by file (which file to write first, why)
2. Dependency graph (what imports what)
3. Risk flags (things likely to break or need care)
4. Environment variable checklist
5. Testing strategy per milestone
```

---

## PHASE 2 — Core Implementation

### @coder — config.py (Settings & Environment)

```
@coder

Implement config.py for the glm47-chatbot project.

REQUIREMENTS:
- Use pydantic-settings (BaseSettings) to load from .env
- Required field: NVIDIA_API_KEY (str)
- Optional fields with defaults:
    NIM_MODEL = "z-ai/glm-4.7"
    NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
    MAX_HISTORY_PAIRS = 10
    SESSION_TIMEOUT_MINUTES = 30
    DEFAULT_ENABLE_THINKING = True
    REQUEST_TIMEOUT_SECONDS = 45
    TELEGRAM_BOT_TOKEN = None (optional str)
- Export a single `settings` instance
- Do NOT hardcode any secrets

Also create .env.example with all variable names and placeholder values.
Add a comment above NVIDIA_API_KEY explaining where to get it (NVIDIA NIM portal).
```

---

### @coder — models.py (Pydantic Request/Response Models)

```
@coder

Implement models.py for the glm47-chatbot project using Pydantic v2.

WEBHOOK REQUEST MODEL (WebhookRequest):
- user_id: str, required, max_length=64, strip whitespace
- message: str, required, max_length=4000, strip whitespace, min_length=1
- system_prompt: Optional[str], max_length=500, default=None
- enable_thinking: bool, default=True

WEBHOOK RESPONSE MODEL (WebhookResponse):
- user_id: str
- reply: str
- thinking_trace: Optional[str] = None
- tokens_used: int
- session_length: int

HEALTH RESPONSE MODEL (HealthResponse):
- status: str = "ok"
- model: str
- context_window: int = 131072
- active_sessions: int

ERROR RESPONSE MODEL (ErrorResponse):
- error: str

Use Pydantic v2 syntax (model_config, field validators). 
Add Field descriptions so FastAPI auto-docs are meaningful.
```

---

### @coder — utils/sanitize.py (Input Cleaning)

```
@coder

Implement utils/sanitize.py for the glm47-chatbot project.

FUNCTIONS REQUIRED:

1. strip_html(text: str) -> str
   - Remove all HTML tags using regex or html.parser
   - Decode HTML entities (e.g. &amp; -> &)
   - Strip leading/trailing whitespace after cleaning
   - Return empty string if result is blank

2. sanitize_message(text: str, max_length: int = 4000) -> str
   - Call strip_html first
   - Truncate to max_length if needed
   - Raise ValueError("Message cannot be empty") if result is empty after cleaning

3. sanitize_system_prompt(text: str, max_length: int = 500) -> str
   - Same as sanitize_message but for system prompts, max 500 chars

Write unit-testable pure functions. No external dependencies beyond stdlib.
Add docstrings for each function.
```

---

### @coder — utils/retry.py (Exponential Backoff)

```
@coder

Implement utils/retry.py for the glm47-chatbot project.

REQUIREMENTS:
- Async exponential backoff decorator: @async_retry(max_attempts=3, base_delay=1.0)
- On each failure: wait base_delay * (2 ** attempt) seconds before retry
- Add jitter: ±20% random variation to avoid thundering herd
- Re-raise the last exception if all retries are exhausted
- Log each retry attempt with attempt number and wait time (use Python logging)
- Handle these specific exceptions for retry: httpx.TimeoutException, httpx.ConnectError
- Do NOT retry on: httpx.HTTPStatusError with status 400 or 422 (client errors)
- For 429 (rate limit): retry with longer delay (base_delay * 5 on first 429)
- For 503: retry normally

Use asyncio.sleep for async waits.
Export: async_retry decorator.
```

---

### @coder — chatbot.py (Core NIM API Logic + Session Management)

```
@coder

Implement chatbot.py for the glm47-chatbot project. This is the most critical file.

IMPORTS: httpx, asyncio, logging, time, from config import settings, from utils.retry import async_retry

SESSION MANAGEMENT:
- _sessions: dict[str, dict] — keys are user_id
- Each session: {"history": list[dict], "last_activity": float (unix timestamp)}
- Keep last MAX_HISTORY_PAIRS message pairs (trim oldest when over limit)
- Session expires after SESSION_TIMEOUT_MINUTES of inactivity
- Implement: get_session(user_id) -> list[dict]  (creates if not exists, cleans expired)
- Implement: update_session(user_id, user_msg: dict, assistant_msg: dict)
- Implement: cleanup_expired_sessions() — call at start of each request
- Implement: active_session_count() -> int

GLM-4.7 API CALL:
- Async function: call_glm47(messages: list[dict], enable_thinking: bool) -> dict
  Returns: {"reply": str, "thinking_trace": str | None, "tokens_used": int}
- Build payload:
    model: settings.NIM_MODEL
    messages: messages (full history including system prompt if any)
    temperature: 0.6
    max_tokens: 1024
    chat_template_kwargs: {"thinking": enable_thinking}
- POST to: {settings.NIM_BASE_URL}/chat/completions
- Headers: Authorization: Bearer {settings.NVIDIA_API_KEY}, Content-Type: application/json
- Timeout: settings.REQUEST_TIMEOUT_SECONDS
- Extract reply from: data["choices"][0]["message"]["content"]
- Extract thinking from: data["choices"][0]["message"].get("reasoning_content", None)
- Extract tokens from: data["usage"]["total_tokens"]
- Wrap with @async_retry(max_attempts=3)

PRESERVED THINKING:
- When enable_thinking=True, store the thinking block in history alongside the message
- History message format when thinking present:
  {"role": "assistant", "content": reply, "reasoning_content": thinking_trace}
- This is GLM-4.7's Preserved Thinking feature — do NOT strip thinking from history

MAIN ENTRY POINT:
- async def process_message(user_id, message, system_prompt=None, enable_thinking=True) -> dict
  Returns: {"reply": str, "thinking_trace": str|None, "tokens_used": int, "session_length": int}
  Steps:
  1. cleanup_expired_sessions()
  2. sanitize_message(message)
  3. get_session(user_id)
  4. Build messages array: [system_prompt if any] + history + [new user message]
  5. call_glm47()
  6. update_session()
  7. Return response dict (thinking_trace=None if enable_thinking=False)

ERROR HANDLING:
- httpx.TimeoutException -> raise custom NIMTimeoutError
- httpx.ConnectError -> raise custom NIMUnavailableError
- HTTPStatusError 429 -> raise custom NIMRateLimitError
- All others -> log and raise NIMUnavailableError with safe message

Define custom exceptions: NIMTimeoutError, NIMUnavailableError, NIMRateLimitError
```

---

### @coder — main.py (FastAPI Application)

```
@coder

Implement main.py for the glm47-chatbot project. This is the FastAPI entrypoint.

IMPORTS: FastAPI, from models import *, from chatbot import process_message, active_session_count, from chatbot import NIMTimeoutError, NIMUnavailableError, NIMRateLimitError, from config import settings

APP SETUP:
- app = FastAPI(title="GLM-4.7 NIM Chatbot", version="1.0.0", description="AI chatbot powered by z-ai/glm-4.7 via NVIDIA NIM")
- Add CORS middleware: allow all origins (for portfolio/demo use)
- Startup event: log that server is running and which model is loaded

POST /webhook:
- Input: WebhookRequest (Pydantic auto-validates)
- Call process_message() from chatbot.py
- On success: return WebhookResponse
- On NIMTimeoutError: return 504 with {"error": "Model response timed out, try a shorter message"}
- On NIMRateLimitError: return 429 with {"error": "Too many requests, try again shortly"}
- On NIMUnavailableError: return 503 with {"error": "AI service temporarily unavailable"}
- On ValueError (sanitization): return 400 with {"error": str(e)}
- Catch-all: log the error, return 503 with safe message (never expose internals)

GET /health:
- Return HealthResponse with:
    status="ok"
    model=settings.NIM_MODEL
    context_window=131072
    active_sessions=active_session_count()

GET / (root):
- Return simple JSON: {"message": "GLM-4.7 NIM Chatbot is running", "docs": "/docs", "health": "/health"}

IMPORTANT: Never expose NVIDIA_API_KEY or thinking_trace in error messages.
Use proper HTTP status codes as defined in the PRD error table.
```

---

## PHASE 3 — Optional Telegram Integration

### @coder — telegram_bot.py (Telegram Integration)

```
@coder

Implement telegram_bot.py for the glm47-chatbot project.

ONLY RUNS if settings.TELEGRAM_BOT_TOKEN is set (check at startup, skip if None).

REQUIREMENTS:
- Use python-telegram-bot library (async version, v20+)
- Message handler: on any text message, call chatbot.process_message()
  - user_id = str(update.effective_user.id)
  - message = update.message.text
  - enable_thinking = False (thinking too verbose for Telegram — always disabled)
  - system_prompt = "You are a helpful assistant. Be concise."
- Send reply["reply"] back to the user
- On error: send "Sorry, I couldn't process that right now. Please try again."
- Do NOT send thinking_trace to Telegram users (hidden by design)
- Add /start command handler: send welcome message explaining what the bot does
- Add /clear command handler: clear the user's session history (call chatbot session reset)

STARTUP INTEGRATION:
- Export: async def start_telegram_bot() -> None
- This is called from main.py's startup event if TELEGRAM_BOT_TOKEN is set
- Run the bot with: application.run_polling() in a separate asyncio task

Implement clean shutdown handling.
```

---

## PHASE 4 — Tests

### @tester — tests/test_webhook.py (Integration Tests)

```
@tester

Write integration tests in tests/test_webhook.py for the glm47-chatbot FastAPI app.

USE: pytest + httpx AsyncClient (for async FastAPI testing)

TESTS TO WRITE:

1. test_health_endpoint()
   - GET /health returns 200
   - Response has: status, model, context_window, active_sessions fields
   - model == "z-ai/glm-4.7"

2. test_webhook_invalid_payload_missing_user_id()
   - POST /webhook with no user_id -> 422

3. test_webhook_invalid_payload_empty_message()
   - POST /webhook with message="" -> 400

4. test_webhook_invalid_payload_message_too_long()
   - POST /webhook with message of 4001 chars -> 422 or 400

5. test_webhook_valid_payload_structure()
   - POST /webhook with valid payload, MOCK the NIM API response
   - Assert response has: user_id, reply, tokens_used, session_length
   - Assert thinking_trace is None when enable_thinking=False
   - Assert thinking_trace is present when enable_thinking=True (if mocked)

6. test_webhook_nim_timeout_returns_504()
   - Mock call_glm47 to raise NIMTimeoutError
   - Assert 504 response with correct error message

7. test_webhook_nim_unavailable_returns_503()
   - Mock call_glm47 to raise NIMUnavailableError
   - Assert 503 response

8. test_root_endpoint()
   - GET / returns 200 with docs link

MOCK STRATEGY:
- Use pytest monkeypatch or unittest.mock.patch to mock chatbot.process_message
- Do NOT make real NIM API calls in tests (no NVIDIA_API_KEY needed in test env)
- Mock return: {"reply": "test reply", "thinking_trace": None, "tokens_used": 10, "session_length": 1}
```

---

### @tester — tests/test_chatbot.py (Unit Tests)

```
@tester

Write unit tests in tests/test_chatbot.py for chatbot.py and utilities.

TESTS TO WRITE:

1. test_strip_html_removes_tags()
   - Input: "<p>Hello <b>world</b></p>" -> "Hello world"

2. test_strip_html_decodes_entities()
   - Input: "&amp;hello&nbsp;" -> "&hello "

3. test_sanitize_message_raises_on_empty()
   - Input: "   " or "<p></p>" -> ValueError

4. test_sanitize_message_truncates()
   - Input: string of 5000 chars -> output length == 4000

5. test_session_sliding_window()
   - Add 12 message pairs to a session
   - Assert history length == MAX_HISTORY_PAIRS * 2 (10 pairs = 20 messages)
   - Assert oldest messages are removed, newest retained

6. test_session_expiry()
   - Create session, manually set last_activity to (now - 31 minutes)
   - Call cleanup_expired_sessions()
   - Assert session no longer exists

7. test_thinking_preserved_in_history()
   - Call update_session with a message that has reasoning_content
   - Assert reasoning_content is stored in the assistant message in history

8. test_retry_decorator_retries_on_timeout()
   - Mock an async function that raises httpx.TimeoutException twice then succeeds
   - Assert it was called 3 times and returned the success value

9. test_retry_decorator_reraises_after_max_attempts()
   - Mock an async function that always raises httpx.TimeoutException
   - Assert NIMTimeoutError is raised after 3 attempts

Use pytest-asyncio for async tests. 
Use unittest.mock for all external calls.
```

---

## PHASE 5 — Infrastructure

### @coder — requirements.txt + Dockerfile

```
@coder

Create requirements.txt and Dockerfile for the glm47-chatbot project.

REQUIREMENTS.TXT — include exact packages:
- fastapi>=0.111.0
- uvicorn[standard]>=0.30.0
- httpx>=0.27.0
- pydantic>=2.7.0
- pydantic-settings>=2.3.0
- python-dotenv>=1.0.0
- python-telegram-bot>=21.0 (optional but include it)
- pytest>=8.0.0
- pytest-asyncio>=0.23.0

DOCKERFILE:
- Base: python:3.11-slim
- Working dir: /app
- Copy requirements.txt first (layer caching)
- Run pip install --no-cache-dir -r requirements.txt
- Copy all project files
- Expose port 8000
- CMD: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
- Add HEALTHCHECK: curl -f http://localhost:8000/health || exit 1
- Do NOT copy .env into the image (use runtime env vars)
- Add a .dockerignore: exclude .env, __pycache__, .git, tests/

The Dockerfile must work with Railway and Render free-tier deployment.
```

---

### @coder — README.md

```
@coder

Write README.md for the glm47-chatbot project. This is a portfolio piece.

SECTIONS TO INCLUDE:

1. Header: Project name, one-line description, badges (Python 3.11+, FastAPI, GLM-4.7)

2. About the Model: 
   - GLM-4.7 by Z.ai via NVIDIA NIM
   - 358B parameters, 131K context window
   - Interleaved Thinking — reasons before every response
   - Benchmark highlights: AIME 95.7%, GPQA-Diamond 85.7%, LiveCodeBench 84.9%

3. Architecture Diagram (ASCII):
   External Trigger -> POST /webhook -> FastAPI -> NVIDIA NIM (GLM-4.7) -> Response

4. Features:
   - Webhook endpoint for any external platform (n8n, Zapier, Telegram, curl)
   - Interleaved Thinking with per-request control
   - Preserved Thinking across multi-turn sessions
   - Session memory (10 pairs, 30-min expiry)
   - Exponential backoff retry
   - Input sanitization
   - Optional Telegram bot integration

5. Quick Start:
   - Clone, create .env from .env.example, pip install, uvicorn main:app
   - Example curl commands (copy from PRD testing section)

6. API Reference:
   - POST /webhook with request/response JSON examples
   - GET /health response example
   - Table of error codes and meanings

7. Deployment (Railway):
   - Step-by-step commands from the PRD deployment section

8. Environment Variables table

9. Running Tests: pytest command

Write in clear, professional markdown. No fluff. Aim for a developer reading this in 2 minutes.
```

---

## PHASE 6 — Review & Verification

### @reviewer — Full Code Review

```
@reviewer

Review the entire glm47-chatbot project for correctness, security, and PRD compliance.

CHECK THESE SPECIFIC THINGS:

SECURITY:
[ ] NVIDIA_API_KEY never appears in any response body or log output
[ ] Thinking traces are never returned when enable_thinking=False
[ ] HTML is stripped from all user inputs before processing
[ ] No secrets in Dockerfile or requirements.txt

PRD COMPLIANCE:
[ ] POST /webhook accepts exactly: user_id, message, system_prompt, enable_thinking
[ ] POST /webhook returns exactly: user_id, reply, thinking_trace, tokens_used, session_length
[ ] GET /health returns: status, model, context_window, active_sessions
[ ] model ID is exactly "z-ai/glm-4.7" (not any other model)
[ ] NIM base URL is exactly "https://integrate.api.nvidia.com/v1"
[ ] chat_template_kwargs: {"thinking": True/False} is passed correctly
[ ] thinking extracted from reasoning_content field (not content)
[ ] Session history limited to MAX_HISTORY_PAIRS pairs
[ ] Session expires after SESSION_TIMEOUT_MINUTES
[ ] Timeout is 45 seconds (not 30, not 60)
[ ] Max retries is 3

ERROR HANDLING:
[ ] 503 returned (not 500) on NIM unavailable
[ ] 504 returned on timeout
[ ] 429 returned on rate limit
[ ] 400 returned on empty/too-long message
[ ] 422 returned on missing required fields
[ ] Catch-all never exposes stack traces or internal errors

CODE QUALITY:
[ ] All async functions use await correctly (no blocking calls in async context)
[ ] httpx.AsyncClient used (not requests, not sync httpx)
[ ] Session cleanup runs on every request
[ ] Preserved Thinking blocks stored in history when enable_thinking=True

For each issue found: state the file, line (if visible), what's wrong, and the fix.
```

---

## PHASE 7 — Live Testing

### @general — Manual Test Run (after server is up)

```
@general

The glm47-chatbot FastAPI server should now be running at http://localhost:8000.
Run these test sequences and report what you observe.

TEST 1 — Health check:
curl http://localhost:8000/health

Expected: {"status":"ok","model":"z-ai/glm-4.7","context_window":131072,"active_sessions":0}

TEST 2 — Webhook with thinking enabled:
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user_1","message":"What is GLM-4.7 and why is it special?","enable_thinking":true}'

Expected: JSON with reply, thinking_trace (non-null), tokens_used, session_length=1

TEST 3 — Multi-turn (Preserved Thinking):
# Turn 1
curl -X POST http://localhost:8000/webhook \
  -d '{"user_id":"u1","message":"My name is Shanmukha. I am building a chatbot."}'

# Turn 2
curl -X POST http://localhost:8000/webhook \
  -d '{"user_id":"u1","message":"What project am I working on?"}'

Expected on Turn 2: bot remembers context, session_length=2

TEST 4 — Fast query with thinking disabled:
curl -X POST http://localhost:8000/webhook \
  -d '{"user_id":"u2","message":"What is 12 * 8?","enable_thinking":false}'

Expected: thinking_trace is null in response

TEST 5 — Error: empty message:
curl -X POST http://localhost:8000/webhook \
  -d '{"user_id":"u3","message":""}'

Expected: 400 or 422 with error message

TEST 6 — API docs accessible:
curl http://localhost:8000/docs

Expected: HTML page (Swagger UI)

For each test: show the actual response and whether it matches expectations.
If anything fails, identify which file/function needs to be fixed.
```

---

## EXECUTION ORDER

Run these prompts in this exact order:

| Step | Agent | Task |
|------|-------|------|
| 1 | `@planner` | Architecture plan |
| 2 | `@coder` | config.py + .env.example |
| 3 | `@coder` | models.py |
| 4 | `@coder` | utils/sanitize.py |
| 5 | `@coder` | utils/retry.py |
| 6 | `@coder` | chatbot.py |
| 7 | `@coder` | main.py |
| 8 | `@coder` | telegram_bot.py |
| 9 | `@coder` | requirements.txt + Dockerfile |
| 10 | `@coder` | README.md |
| 11 | `@tester` | tests/test_webhook.py |
| 12 | `@tester` | tests/test_chatbot.py |
| 13 | `@reviewer` | Full review |
| 14 | `@general` | Manual test run |

---

## TIPS FOR OPENCODE USAGE

- Use `@explore` before `@coder` on chatbot.py to let the agent first read the other files it depends on (config.py, models.py, utils/)
- If `@coder` writes a file but makes an error, use `@reviewer` on that single file before moving on
- After all files are written, run `pytest tests/` to catch issues before the `@reviewer` pass
- The `@planner` output can be saved and re-pasted into later prompts as context if needed
- Keep your NVIDIA_API_KEY in .env — never paste it directly into any OpenCode prompt
