# Graph Report - .  (2026-05-01)

## Corpus Check
- Corpus is ~4,498 words - fits in a single context window. You may not need a graph.

## Summary
- 86 nodes · 105 edges · 9 communities detected
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]

## God Nodes (most connected - your core abstractions)
1. `Chatbot Processing Service` - 8 edges
2. `process_message()` - 7 edges
3. `call_glm47()` - 5 edges
4. `TestSanitize` - 5 edges
5. `FastAPI Application` - 5 edges
6. `Telegram Bot Integration` - 5 edges
7. `NIMTimeoutError` - 4 edges
8. `NIMUnavailableError` - 4 edges
9. `sanitize_message()` - 4 edges
10. `TestSession` - 4 edges

## Surprising Connections (you probably didn't know these)
- `test_webhook_nim_timeout_returns_504()` --calls--> `NIMTimeoutError`  [INFERRED]
  tests/test_webhook.py → chatbot.py
- `test_webhook_nim_unavailable_returns_503()` --calls--> `NIMUnavailableError`  [INFERRED]
  tests/test_webhook.py → chatbot.py
- `process_message()` --calls--> `sanitize_message()`  [INFERRED]
  chatbot.py → utils/sanitize.py
- `process_message()` --calls--> `sanitize_system_prompt()`  [INFERRED]
  chatbot.py → utils/sanitize.py
- `health()` --calls--> `HealthResponse`  [INFERRED]
  main.py → models.py

## Hyperedges (group relationships)
- **Webhook Request-Response Flow** — wh_req, pydantic_models, wh_resp, webhook_ep [EXTRACTED 0.95]
- **Telegram Bot Integration Flow** — telegram_bot, tel_webhook, chatbot_service, session_mgmt [EXTRACTED 0.95]
- **NIM Error Handling Flow** — nim_timeout, nim_unavail, nim_ratelimit, chatbot_service, webhook_ep [EXTRACTED 0.95]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (6): test_retry_reraises_after_max_attempts(), test_retry_retries_on_timeout_exception(), TestRetry, TestSanitize, TestSession, async_retry()

### Community 1 - "Community 1"
Cohesion: 0.23
Nodes (7): BaseModel, health(), webhook(), ErrorResponse, HealthResponse, WebhookRequest, WebhookResponse

### Community 2 - "Community 2"
Cohesion: 0.35
Nodes (9): Exception, call_glm47(), cleanup_expired_sessions(), get_session(), NIMRateLimitError, NIMTimeoutError, NIMUnavailableError, process_message() (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.2
Nodes (2): test_webhook_nim_timeout_returns_504(), test_webhook_nim_unavailable_returns_503()

### Community 4 - "Community 4"
Cohesion: 0.29
Nodes (10): Chatbot Processing Service, GLM-4.7 LLM Model, NIM API Integration, NIM Rate Limit Error, NIM Timeout Error, NIM Unavailable Error, Async Retry Decorator, Input Sanitization (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.22
Nodes (10): Configuration Settings, FastAPI Application, Health Check Endpoint, Pydantic Models, In-Memory Session Management, Telegram Polling Mode, Telegram Webhook Mode, Telegram Bot Integration (+2 more)

### Community 6 - "Community 6"
Cohesion: 0.28
Nodes (3): _build_application(), start_polling_mode(), start_webhook_mode()

### Community 7 - "Community 7"
Cohesion: 0.83
Nodes (3): sanitize_message(), sanitize_system_prompt(), strip_html()

### Community 8 - "Community 8"
Cohesion: 0.67
Nodes (2): BaseSettings, Settings

## Knowledge Gaps
- **7 isolated node(s):** `TestRetry`, `GLM-4.7 LLM Model`, `Thinking Mode`, `Health Check Endpoint`, `Webhook Request Model` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 3`** (10 nodes): `client()`, `test_webhook.py`, `test_health_returns_200()`, `test_root_returns_200()`, `test_webhook_empty_message_returns_400_or_422()`, `test_webhook_missing_user_id_returns_422()`, `test_webhook_nim_timeout_returns_504()`, `test_webhook_nim_unavailable_returns_503()`, `test_webhook_thinking_trace_none_when_disabled()`, `test_webhook_valid_payload_returns_correct_structure()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 8`** (3 nodes): `BaseSettings`, `config.py`, `Settings`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Telegram Bot Integration` connect `Community 5` to `Community 1`, `Community 4`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `Chatbot Processing Service` connect `Community 4` to `Community 5`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `process_message()` (e.g. with `sanitize_message()` and `sanitize_system_prompt()`) actually correct?**
  _`process_message()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `TestRetry`, `GLM-4.7 LLM Model`, `Thinking Mode` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._