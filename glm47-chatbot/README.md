# GLM-4.7 NIM Chatbot with Webhook Integration

A FastAPI-based chatbot service powered by NVIDIA's GLM-4.7 model via NIM (NVIDIA Inference Microservices), with Telegram bot integration and webhook endpoints.

## Project Summary

This project provides a scalable chatbot API that integrates with NVIDIA's GLM-4.7 model through their NIM platform. It supports:
- RESTful webhook API for chatbot interactions
- Session management with conversation history
- Thinking trace support for model reasoning
- Optional Telegram bot integration
- Automatic retry with exponential backoff

## GLM-4.7 Model Information

GLM-4.7 is NVIDIA's latest large language model featuring:
- 131,072 token context window
- Advanced reasoning capabilities
- Thinking mode for complex problem-solving
- High-quality conversational responses
- Tool use capabilities

## Architecture

```
┌─────────────────┐
│   Telegram Bot   │
│  (Optional)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│  Session Mgmt   │
│    (main.py)    │     │ (In-Memory)    │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│   GLM-4.7 NIM   │
│    (chatbot.py)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ NVIDIA NIM API  │
│integrate.api.   │
│nvidia.com/v1   │
└─────────────────┘
```

## Features

- **Webhook API**: POST /webhook endpoint for chatbot interactions
- **Session Management**: Maintains conversation history per user (configurable)
- **Thinking Mode**: Enable/disable model reasoning traces
- **System Prompts**: Custom instructions per request
- **Error Handling**: Proper HTTP status codes for different failure scenarios
- **Telegram Integration**: Optional bot for telegram messaging
- **Auto-Retry**: Exponential backoff for transient failures
- **Input Sanitization**: HTML stripping and length limits
- **CORS Support**: Enabled for all origins

## Quick Start

### Prerequisites

- Python 3.11+
- NVIDIA API Key (get from https://build.nvidia.com/)

### Installation

```bash
# Clone or navigate to project directory
cd glm47-chatbot

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment file
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY
```

### Running the Server

```bash
# Development
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000

# Docker
docker build -t glm47-chatbot .
docker run -p 8000:8000 --env-file .env glm47-chatbot
```

## API Reference

### POST /webhook

Send a message to the chatbot.

**Request:**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Hello, how are you?",
    "enable_thinking": true
  }'
```

**Response:**
```json
{
  "user_id": "user123",
  "reply": "Hello! I'm doing well, thank you for asking. How can I help you today?",
  "thinking_trace": "The user is greeting me...",
  "tokens_used": 25,
  "session_length": 1
}
```

### GET /health

Check service health.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "model": "z-ai/glm-4.7",
  "context_window": 131072,
  "active_sessions": 5
}
```

### GET /

Service information.

```bash
curl http://localhost:8000/
```

## Deployment on Railway

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add environment variables:
   - `NVIDIA_API_KEY`: Your NVIDIA API key
4. Deploy: railway deploy

The service will be available at your Railway domain.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NVIDIA_API_KEY` | Yes | - | NVIDIA API key from build.nvidia.com |
| `NIM_MODEL` | No | z-ai/glm-4.7 | Model identifier |
| `NIM_BASE_URL` | No | https://integrate.api.nvidia.com/v1 | API base URL |
| `MAX_HISTORY_PAIRS` | No | 10 | Message pairs to keep in history |
| `SESSION_TIMEOUT_MINUTES` | No | 30 | Session expiration time |
| `DEFAULT_ENABLE_THINKING` | No | true | Enable thinking by default |
| `REQUEST_TIMEOUT_SECONDS` | No | 45 | API request timeout |
| `TELEGRAM_BOT_TOKEN` | No | - | Telegram bot token (optional) |

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_webhook.py -v
pytest tests/test_chatbot.py -v

# With coverage
pytest tests/ --cov
```

## Docker

Build and run with Docker:

```bash
docker build -t glm47-chatbot .
docker run -p 8000:8000 --env-file .env glm47-chatbot
```

Or using Docker Compose:

```yaml
version: '3.8'
services:
  bot:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## License

MIT License