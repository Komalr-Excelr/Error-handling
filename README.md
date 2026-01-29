

NAME: KOMAL RAVINDRA RAUT


# Error Recovery & Resilience System for AI Call Agent:

This repository demonstrates a resilient integration layer for an AI Call Agent that depends on third‑party services (e.g., ElevenLabs, LLM provider, CRM). It is designed to detect failures, recover intelligently, avoid cascading outages, alert humans when needed, and continue operating gracefully.

The code is configuration‑driven, cleanly separated by concern, testable, and avoids external resilience libraries.

## Architecture:

**Exceptions & Categorization**: A custom hierarchy differentiates transient vs. permanent errors. This enables precise retry and fail‑fast behavior.
**Retry**: A configurable exponential backoff mechanism applies only to transient errors.
**Circuit Breakers**: Each external service has its own breaker with `Closed`, `Open`, and `Half‑Open` states. **Health Checks**: Periodic checks update service health and reset breakers when recovery is detected.
**Monitoring & Alerts**: Structured logs to file and a Google Sheets mock CSV; alerts via Email, Telegram, and Webhook.
**Graceful Degradation**: On failures, the system skips the current call, marks it in CRM, alerts, and proceeds to the next item.

### Project Structure

error-recovery-system/
- src/
  - exceptions/ — Custom error types
  - core/ — Retry, circuit breaker, health checks, categorizer
  - monitoring/ — Logging and alerting
  - services/ — Mock integrations (ElevenLabs, LLM, CRM)
  - call_agent.py — Orchestrates the flow
- config/settings.yaml — Parameters for retries, breakers, health checks, logs, alerts
- tests/ — Unit + integration tests
- logs/ — App logs and mock Sheets CSV
- requirements.txt

##  1. Error Flow:

- **Transient errors** (timeouts, 503, network failures):
  - Categorized as `TransientError`
  - Retries with exponential backoff using configured `initial_delay`, `backoff_factor`, and `max_attempts`
  - Failures increment the service circuit breaker
  - If the breaker is `Open`, calls fail fast (no attempt)

- **Permanent errors** (401, invalid payloads, quota exceeded):
  - Categorized as `PermanentError`
  - No retry; the call is marked failed and the system proceeds

## 2. Retry Strategy:

- **Configurable** via `config/settings.yaml`:
  - `retry.initial_delay_seconds`: first delay (default 5s)
  - `retry.backoff_factor`: multiplier per attempt (default 2.0)
  - `retry.max_attempts`: total attempts (default 3)
- **Scope**: Applied only to `TransientError`.
- **Behavior**: `delay *= backoff_factor` per retry; aborts when `max_attempts` exhausted.

## 3. Circuit Breaker Behavior:

- **States**:
  - `Closed`: normal operation
  - `Open`: fail fast; no calls allowed
  - `Half‑Open`: probe state after timeout; success resets to `Closed`, failure re‑opens
- **Thresholds**: Controlled by `circuit_breaker.failure_threshold` and `reset_timeout_seconds`.
- **Per‑service**: Breakers are independent per integration to isolate faults.

## 4. Logging & Observability:

- **Local file**: Structured JSON lines at `logs/app.log` (timestamp, service, category, retry_count, circuit_breaker_state, message).
- **Google Sheets (mock)**: CSV appended at `logs/google_sheets.csv` for non‑technical visibility (works without external endpoints).
- **Visualization**: `src/visualize_logs.py` summarizes event categories, breaker states, and services.


## 5. Alerts:

- **Triggers**:
  - Circuit breaker opens (fail‑fast condition)
  - A call permanently fails
  - A dependency remains down beyond a threshold
- **Channels**: Email, Telegram, Webhook (implemented; demo prints to console for safety).


## 6. Health Checks:

- **Periodic** checks run in a background thread.
- **Recovery**: When a service reports healthy, its breaker is reset to `Closed`.
- **Deterministic**: `run_once()` allows manual invocation in tests and demos.


## 7. Graceful Degradation:

- **On failure**: Mark the current contact as failed, send alert, skip to the next contact, and prevent system‑wide blocking.

## Required Scenario: ElevenLabs 503

This scenario demonstrates detection, retries, failure handling, breaker open, continued health checks, recovery, and resumed processing.

1. Detect 503 as transient.
2. Retry with exponential backoff starting at 5 seconds, up to 3 attempts.
3. When retries fail: mark call failed, trigger alert, move to next contact.
4. Circuit breaker opens for ElevenLabs (fail fast).
5. Health checks continue.
6. When ElevenLabs is healthy again: circuit resets.
7. Call processing resumes.

## Output

### Console (Demo)
[Scenario] Starting processing with ElevenLabs unhealthy (expect retries and failure)
[Alert] Circuit breaker open for ElevenLabs: Fail-fast: ElevenLabs unhealthy
[Scenario] Circuit breaker state after failures: HALF_OPEN
[Scenario] Circuit breaker state after health check: CLOSED
[Scenario] Resuming processing with ElevenLabs healthy (expect success)
[Retry] backoff sleeping 5s (simulated)


### Logs (Structured JSON)
{"timestamp": "2026-01-29T13:28:27Z", "service": "elevenlabs", "category": "transient", "retry_count": 0, "circuit_breaker_state": "OPEN", "message": "Circuit open for elevenlabs"}
{"timestamp": "2026-01-29T13:28:28Z", "service": "elevenlabs", "category": "success", "retry_count": 0, "circuit_breaker_state": "CLOSED", "message": "TTS success"}


### Google Sheets (Mock CSV)
timestamp,service,category,retry_count,circuit_breaker_state,message
2026-01-29T13:28:27Z,elevenlabs,transient,0,OPEN,Circuit open for elevenlabs
2026-01-29T13:28:28Z,elevenlabs,success,0,CLOSED,TTS success


## Quick Start (Windows / PowerShell)

Create a virtual environment and install dependencies:

```powershell
Set-Location "D:\Error handling\error-recovery-system"
python -m venv ..\.venv
. "..\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

Run tests:

```powershell
& "..\.venv\Scripts\python.exe" -m pytest -q
```

Run the required scenario demo (failure → alerts → breaker open → recovery → resume):

```powershell
& "..\.venv\Scripts\python.exe" -m src.run_scenario
```

Visualize logs:

```powershell
& "..\.venv\Scripts\python.exe" -m src.visualize_logs
```

## Configuration

All behavior is controlled by `config/settings.yaml`:

- **retry**: `initial_delay_seconds`, `max_attempts`, `backoff_factor`
- **circuit_breaker**: `failure_threshold`, `reset_timeout_seconds`
- **health_check**: `interval_seconds`
- **logging**: `file_path`, `level`, `google_sheets.mock_file_path` for CSV
- **alerts**: email/telegram/webhook `enabled` and credentials (safe‑off by default)

## Tests & Simulations

- Unit tests cover retry backoff and circuit breaker transitions.
- Integration test exercises the ElevenLabs 503 scenario with deterministic health recovery.
- Scenario runner provides a no‑network, console‑visible demonstration.

## Notes

- No external retry/circuit breaker libraries.
- Clean separation of concerns and configuration‑driven behavior.
- Mocked services and CSV logging for safe local visualization.

