# Aegis-LLM — Complete Run Guide

> Step-by-step instructions for running the full Aegis-LLM platform, including
> local development, Docker, dry-run mode, live scans, the web frontend, API
> usage, CI/CD integration, and testing.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup (No Docker)](#2-local-development-setup-no-docker)
3. [Docker Setup (Full Stack)](#3-docker-setup-full-stack)
4. [Database Initialization](#4-database-initialization)
5. [Running the Mock Target (Demo)](#5-running-the-mock-target-demo)
6. [Registering a Target](#6-registering-a-target)
7. [Running Scans — Dry Run Mode](#7-running-scans--dry-run-mode)
8. [Running Scans — Live Mode](#8-running-scans--live-mode)
9. [Scanning a Real AI/LLM Target](#9-scanning-a-real-aillm-target)
10. [Viewing Findings & Generating Reports](#10-viewing-findings--generating-reports)
11. [Running the Web Frontend](#11-running-the-web-frontend)
12. [Using the REST API](#12-using-the-rest-api)
13. [CI/CD Integration](#13-cicd-integration)
14. [Running Tests](#14-running-tests)
15. [Environment Variables Reference](#15-environment-variables-reference)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Python | 3.11+ | Required by the backend |
| Node.js | 18+ | Only for the web frontend |
| Docker & Docker Compose | 24+ / v2 | For the full-stack Docker setup |
| PostgreSQL (optional) | 16 | Only if not using SQLite for dev |
| Redis (optional) | 7 | Only needed for ARQ worker (`AEGIS_RUNNER=arq`) |

---

## 2. Local Development Setup (No Docker)

This is the fastest way to get started. It uses **SQLite** by default so no
external services are required.

### Step 1 — Clone & create virtual environment

```bash
git clone <repo-url> aegis-llm
cd aegis-llm

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### Step 2 — Install the backend

```bash
pip install -e ".[dev]"
```

This installs the core package plus dev dependencies (pytest, httpx, etc.).

### Step 3 — Copy & edit the environment file

```bash
cp .env.example .env
```

Edit `.env` as needed. For local dev with SQLite (the defaults work as-is):

```
AEGIS_DATABASE_URL=sqlite+aiosqlite:///./aegis.db
AEGIS_RUNNER=inproc
AEGIS_DRY_RUN_DEFAULT=true
```

### Step 4 — Verify the installation

```bash
python -m app.cli --help
```

You should see a list of available commands: `init-db`, `register-target`, `run`,
`findings`, `report`, `demo`, `scan-real`, etc.

---

## 3. Docker Setup (Full Stack)

One command brings up **PostgreSQL + pgvector**, **Redis**, the **API server**,
and the **ARQ worker**.

### Step 1 — Build & start all services

```bash
docker compose up --build
```

Services started:

| Service | Port | Description |
|---|---|---|
| `db` | 5432 | PostgreSQL 16 + pgvector |
| `redis` | 6379 | Redis 7 (queues, rate limits, pub/sub) |
| `api` | 8000 | FastAPI backend (uvicorn) |
| `worker` | — | ARQ background worker |

### Step 2 — Verify

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

### Step 3 — Open API docs

Navigate to **http://localhost:8000/docs** in your browser for the interactive
Swagger UI.

### Stop all services

```bash
docker compose down            # keeps volumes
docker compose down -v         # also removes data volumes
```

---

## 4. Database Initialization

Before running any commands (locally or with Docker), you must initialize the
database.

### Local (SQLite)

```bash
python -m app.cli init-db
```

This will:
1. Create all database tables.
2. Seed default roles (`viewer`, `operator`, `admin`).
3. Create the admin user (default: `admin` / `admin`).
4. Load bundled payload packs (5 packs: prompt-injection, jailbreak,
   data-exfiltration, tool-abuse, multi-turn).

### Docker (PostgreSQL)

When using `docker compose up`, the API container runs the migration on startup.
To run it manually inside the container:

```bash
docker compose exec api python -m app.cli init-db
```

### Using Alembic (canonical schema path)

```bash
alembic upgrade head
```

---

## 5. Running the Mock Target (Demo)

The **end-to-end demo** is the fastest way to see the full platform in action.
It spins up a deliberately vulnerable mock LLM chat app, registers it, runs
both a dry-run and a live scan, and generates reports.

### One command demo

```bash
python -m app.cli demo
```

What happens:

1. Starts a mock vulnerable target (Acme Chat) on port 8100 in a background
   thread.
2. Initializes the database and seeds data.
3. Registers the mock target and allow-lists it.
4. **[1/3] DRY-RUN** — executes the full pipeline without touching the real
   target (uses `DryRunConnector`).
5. **[2/3] LIVE run** — sends payloads to the mock target, exercises the full
   Attacker → Judge → Refiner → Memory agent loop, records findings.
6. **[3/3] Report generation** — produces HTML, SARIF, and JSON reports in
   `reports/`.

### Running the mock target independently

```bash
python -m mock_target.main
# Available at http://127.0.0.1:8100/chat
# Health check: http://127.0.0.1:8100/healthz
```

---

## 6. Registering a Target

### CLI registration

```bash
python -m app.cli register-target \
  --name acme-chat \
  --connector-type rest \
  --endpoint http://127.0.0.1:8100/chat \
  --config '{"response_path": "reply"}'
```

Options:

| Flag | Required | Description |
|---|---|---|
| `--name` | Yes | Human-readable target name |
| `--connector-type` | Yes | `rest`, `browser`, or `websocket` |
| `--endpoint` | Yes | Target URL |
| `--config` | No | JSON config (e.g., `response_path`, `headers`, `body_template`) |
| `--description` | No | Free-text description |
| `--approved-by` | No | Approver username (defaults to admin) |
| `--approval-note` | No | Audit note for the approval |

> **Note:** Targets registered via CLI are **automatically allow-listed**.
> Targets created via the API start as `CLOSED` and must be explicitly
> allow-listed before any run can target them.

### List registered targets

```bash
python -m app.cli list-targets
```

### Allow-list / de-list an existing target

```bash
python -m app.cli allowlist-target --id <target-id> --allow
python -m app.cli allowlist-target --id <target-id> --no-allow
```

---

## 7. Running Scans — Dry Run Mode

**Dry-run mode** executes the full attack pipeline (payload selection,
orchestration, judge evaluation, finding generation) but uses a simulated
`DryRunConnector` instead of making real HTTP requests to the target. **Nothing
touches the real target.**

Dry-run is the **default mode** (`AEGIS_DRY_RUN_DEFAULT=true` in `.env`).

### Step 1 — List available payload packs

```bash
python -m app.cli list-packs
```

Sample output:

```
data-exfiltration  v1.0.0     5 payloads  OWASP LLM06
jailbreak          v1.0.0     5 payloads  OWASP LLM01
multi-turn         v1.0.0     5 payloads  OWASP LLM01,LLM05
prompt-injection   v1.0.0     5 payloads  OWASP LLM01
tool-abuse         v1.0.0     5 payloads  OWASP LLM05,LLM07
```

### Step 2 — Run a dry run

```bash
python -m app.cli run \
  --target <target-id> \
  --packs prompt-injection,jailbreak,data-exfiltration \
  --dry-run
```

What happens:

1. Validates the target is registered and allow-listed.
2. Loads payloads from the specified packs.
3. Runs the full orchestrator loop in dry-run mode:
   - Attacker selects payloads (no real HTTP sent).
   - Judge evaluates simulated responses.
   - Refiner generates mutations (if applicable).
   - Memory records the (simulated) interaction.
4. Prints a summary: status, events, findings (if any).

### Step 3 — Explicit dry-run via environment variable

You can also control this globally in `.env`:

```
AEGIS_DRY_RUN_DEFAULT=true     # all runs are dry-run unless overridden
AEGIS_DRY_RUN_DEFAULT=false    # all runs are live unless overridden
```

### Override per-run

```bash
# Force dry-run even if AEGIS_DRY_RUN_DEFAULT=false
python -m app.cli run --target <id> --packs prompt-injection --dry-run

# Force live even if AEGIS_DRY_RUN_DEFAULT=true
python -m app.cli run --target <id> --packs prompt-injection --no-dry-run
```

---

## 8. Running Scans — Live Mode

**Live mode** sends real requests to the target endpoint. Use only against
targets you **own or are explicitly authorized to test**.

### Step 1 — Ensure the target is allow-listed

```bash
python -m app.cli list-targets
# Look for "ALLOW-LISTED" in the output
```

### Step 2 — Run a live scan

```bash
python -m app.cli run \
  --target <target-id> \
  --packs prompt-injection,jailbreak,data-exfiltration \
  --no-dry-run
```

### Step 3 — Set max turns (optional)

```bash
python -m app.cli run \
  --target <target-id> \
  --packs prompt-injection,jailbreak \
  --no-dry-run \
  --max-turns 5
```

### What happens in a live run

1. **Payload selection** — attacker agent picks payloads from the packs.
2. **Interaction** — each payload is sent to the target via the configured
   connector (REST via httpx, browser via Playwright, or WebSocket).
3. **Judgment** — the judge evaluates the target's response (heuristic
   detector ensemble; optional LLM judge if `AEGIS_JUDGE_API_KEY` is set).
4. **Refinement** — if the judge indicates partial success, the refiner
   mutates the payload and retries.
5. **Memory** — interactions are recorded in the vector store + knowledge graph.
6. **Safety enforcement** — rate limits, token budgets, circuit breakers, and
   audit logging are enforced at every step.
7. **Findings** — successful attacks are recorded as findings with severity,
   confidence, OWASP category, and MITRE ATLAS mapping.

### Safety guardrails during live runs

- **Rate limiting**: max 60 requests/minute per target (configurable).
- **Token budget**: 200,000 tokens per run (configurable).
- **Circuit breaker**: opens after 5 consecutive failures; cooldown 60s.
- **Audit log**: every request/response pair is redacted and persisted before
  returning to the caller.
- **Max concurrent runs**: 4 (configurable via `AEGIS_MAX_CONCURRENT_RUNS`).

---

## 9. Scanning a Real AI/LLM Target

The `scan-real` command provides a one-step workflow: test connection → register
target → run scan.

### Basic usage

```bash
python -m app.cli scan-real \
  --url https://api.openai.com/v1/chat/completions \
  --name "my-openai-chat" \
  --model gpt-4o-mini \
  --response-path choices.0.message.content
```

### With custom headers and API key

```bash
python -m app.cli scan-real \
  --url https://api.openai.com/v1/chat/completions \
  --name "my-gpt" \
  --model gpt-4o-mini \
  --response-path choices.0.message.content \
  --headers '{"Authorization": "Bearer sk-..."}'
```

### Dry run against a real target

```bash
python -m app.cli scan-real \
  --url https://your-app.com/api/chat \
  --name "prod-chat" \
  --response-path reply \
  --dry-run
```

### With custom body template

```bash
python -m app.cli scan-real \
  --url https://your-app.com/api/chat \
  --name "custom-body" \
  --body-template '{"model":"gpt-4o","messages":{messages},"stream":false}' \
  --response-path choices.0.message.content
```

### Full options

| Flag | Description | Default |
|---|---|---|
| `--url` | Target endpoint (required) | — |
| `--name` | Target name | auto-generated from URL |
| `--description` | Description | — |
| `--connector-type` | `rest`, `browser`, `websocket` | `rest` |
| `--model` | Model name for the request body | — |
| `--response-path` | Dotted path to extract reply | — |
| `--headers` | Extra headers as JSON | — |
| `--body-template` | Body JSON with `{messages}` placeholder | — |
| `--method` | HTTP method | `POST` |
| `--timeout` | Connection timeout (seconds) | `30` |
| `--insecure` | Disable TLS verification | `false` |
| `--packs` | Comma-separated pack names | `prompt-injection,jailbreak,data-exfiltration` |
| `--dry-run` / `--no-dry-run` | Dry-run mode toggle | from `AEGIS_DRY_RUN_DEFAULT` |
| `--max-turns` | Max agent turns | from config |

---

## 10. Viewing Findings & Generating Reports

### List findings

```bash
# All findings
python -m app.cli findings

# Filter by run
python -m app.cli findings --run <run-id>

# Filter by severity
python -m app.cli findings --severity high

# Filter by category
python -m app.cli findings --category prompt-leak
```

### Generate reports

```bash
# HTML report
python -m app.cli report --run <run-id> --format html

# SARIF report (for code scanning integration)
python -m app.cli report --run <run-id> --format sarif

# JSON report
python -m app.cli report --run <run-id> --format json
```

Reports are saved to the `reports/` directory (configurable via
`AEGIS_REPORT_DIR`).

---

## 11. Running the Web Frontend

The web frontend is a **Next.js 14** app in the `aegis-llm-web/` directory.

### Step 1 — Install dependencies

```bash
cd aegis-llm-web
npm install
```

### Step 2 — Configure environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```
# Mock mode (no backend needed)
NEXT_PUBLIC_API_MOCK=true

# Or point to a live backend
# NEXT_PUBLIC_API_MOCK=false
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3 — Start the dev server

```bash
npm run dev
```

Open **http://localhost:3000** in your browser.

### Mock mode vs live mode

| | Mock Mode | Live Mode |
|---|---|---|
| Backend required | No | Yes (`uvicorn app.main:app`) |
| Data source | In-memory seed data | FastAPI REST API |
| Auth | Any credentials → mock admin | `POST /auth/login` → JWT |
| SSE stream | Simulated agent events | Real-time `GET /runs/{id}/stream` |

### Running frontend tests

```bash
cd aegis-llm-web
npm test
```

---

## 12. Using the REST API

### Start the API server

```bash
# Local (no Docker)
uvicorn app.main:app --reload --port 8000

# Docker
docker compose up api
```

### Login & get a JWT token

```bash
TOKEN=$(curl -s localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"admin","password":"admin"}' \
  | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
```

### Register a target via API

```bash
curl -s localhost:8000/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{
    "name": "acme-chat",
    "connector_type": "rest",
    "endpoint": "http://127.0.0.1:8100/chat",
    "config": {"response_path": "reply"}
  }'
```

### Allow-list the target (required before any run)

```bash
curl -s -X PATCH localhost:8000/targets/<target-id>/allowlist \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"allowlisted":true,"approved_by":"admin","approval_note":"own demo target"}'
```

### Dry-run via API

```bash
curl -s localhost:8000/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{
    "target_id": "<target-id>",
    "payload_pack_ids": ["<pack-id>"],
    "dry_run": true
  }'
```

### Live run via API

```bash
curl -s localhost:8000/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{
    "target_id": "<target-id>",
    "payload_pack_ids": ["<pack-id>"],
    "dry_run": false
  }'
```

### Stream live events (SSE)

```bash
curl -N localhost:8000/runs/<run-id>/stream \
  -H "Authorization: Bearer $TOKEN"
```

### Generate a report via API

```bash
curl -s "localhost:8000/runs/<run-id>/report?format=sarif" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 13. CI/CD Integration

### GitHub Actions workflow

A reusable workflow is at `.github/workflows/ci.yml`. It runs on PRs and pushes
to `main`.

**Required secrets:**

| Secret | Description |
|---|---|
| `AEGIS_API` | Base URL of the Aegis-LLM API |
| `AEGIS_TOKEN` | Bearer token with `viewer+` role |
| `AEGIS_TARGET_ID` | Allow-listed staging target to scan |

**Optional variables:**

| Variable | Default | Description |
|---|---|---|
| `AEGIS_PACKS` | `prompt-injection,jailbreak,data-exfiltration` | Comma-separated pack names |
| `AEGIS_THRESHOLD` | `high` | Severity threshold for the policy gate |
| `AEGIS_MIN_CONF` | `0.6` | Minimum confidence for blocking findings |

### Standalone policy gate script

```bash
AEGIS_API=http://localhost:8000 \
AEGIS_TOKEN=<token> \
ci/policy_gate.sh <run-id> high 0.6
```

Exits `0` if the gate passes, `1` if blocking findings are present. Writes a
SARIF file on failure.

### Policy gate via REST API

```bash
curl -s localhost:8000/ci/gate \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{
    "run_id": "<run-id>",
    "severity_threshold": "high",
    "min_confidence": 0.6
  }'
```

---

## 14. Running Tests

### Backend tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_agents.py

# Run tests matching a keyword
pytest -k "sarif"
```

Test coverage includes:
- Allow-list enforcement
- Redaction of sensitive data
- Agent loop (Attacker → Judge → Refiner)
- SARIF report shape
- API smoke tests

### Frontend tests

```bash
cd aegis-llm-web
npm test
```

---

## 15. Environment Variables Reference

All variables are prefixed with `AEGIS_` and validated by `app/core/config.py`.

### Runtime

| Variable | Default | Description |
|---|---|---|
| `AEGIS_ENV` | `dev` | `dev` or `prod` |
| `AEGIS_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `AEGIS_DATABASE_URL` | `sqlite+aiosqlite:///./aegis.db` | Database connection string |
| `AEGIS_REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `AEGIS_RUNNER` | `inproc` | `inproc` (demo/tests) or `arq` (production) |
| `AEGIS_DRY_RUN_DEFAULT` | `true` | Default dry-run mode for new runs |
| `AEGIS_MAX_CONCURRENT_RUNS` | `4` | Max concurrent attack runs |

### Authentication

| Variable | Default | Description |
|---|---|---|
| `AEGIS_JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `AEGIS_JWT_ALG` | `HS256` | JWT algorithm |
| `AEGIS_JWT_EXPIRES_MINUTES` | `480` | Token expiry (minutes) |
| `AEGIS_ADMIN_USERNAME` | `admin` | Default admin username |
| `AEGIS_ADMIN_PASSWORD` | `admin` | Default admin password |

### Safety Limits

| Variable | Default | Description |
|---|---|---|
| `AEGIS_DEFAULT_MAX_TOKENS_PER_RUN` | `200000` | Token budget per run |
| `AEGIS_DEFAULT_MAX_TURNS` | `10` | Max agent turns per run |
| `AEGIS_RATE_LIMIT_PER_MINUTE` | `60` | Requests per minute per target |
| `AEGIS_CIRCUIT_BREAKER_FAILURE_THRESHOLD` | `5` | Failures before circuit opens |
| `AEGIS_CIRCUIT_BREAKER_COOLDOWN_SECONDS` | `60` | Circuit breaker cooldown |

### Judge & Embeddings (Optional)

| Variable | Default | Description |
|---|---|---|
| `AEGIS_JUDGE_API_KEY` | (empty) | Set to enable LLM-as-judge |
| `AEGIS_JUDGE_API_BASE` | `https://api.openai.com/v1` | Judge API base URL |
| `AEGIS_JUDGE_MODEL` | `gpt-4o-mini` | Judge model |
| `AEGIS_VECTOR_STORE` | `numpy` | `numpy` or `pgvector` |
| `AEGIS_EMBEDDING_API_BASE` | (empty) | Embedding API base URL |
| `AEGIS_EMBEDDING_API_KEY` | (empty) | Embedding API key |

### Reporting & Mock

| Variable | Default | Description |
|---|---|---|
| `AEGIS_REPORT_DIR` | `./reports` | Report output directory |
| `AEGIS_MOCK_TARGET_PORT` | `8100` | Mock target server port |

---

## 16. Troubleshooting

### "Admin user not found"
Run `python -m app.cli init-db` to create the database and seed the admin user.

### "target is NOT allow-listed — refusing to run"
Use `python -m app.cli allowlist-target --id <target-id> --allow` to approve
the target before running a scan.

### "Payload pack not found"
Run `python -m app.cli list-packs` to see available packs. Make sure you
ran `init-db` to load the bundled packs.

### Docker: "relation 'targets' does not exist"
The database hasn't been initialized. Run:
```bash
docker compose exec api python -m app.cli init-db
```

### Mock target won't start (port in use)
Change the port in `.env`:
```
AEGIS_MOCK_TARGET_PORT=8101
```

### Connection refused to Redis
Redis is only required when `AEGIS_RUNNER=arq`. For local dev, use
`AEGIS_RUNNER=inproc`.

### Frontend shows "API error" in live mode
Ensure the backend is running on port 8000 and `NEXT_PUBLIC_API_URL` in
`aegis-llm-web/.env.local` matches.

---

## Quick Reference — Common Workflows

### Minimal local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m app.cli init-db
python -m app.cli demo
```

### Dry run only (safe, no real requests)

```bash
python -m app.cli init-db
python -m app.cli register-target \
  --name my-target --connector-type rest \
  --endpoint http://localhost:8100/chat \
  --config '{"response_path":"reply"}'
python -m app.cli run \
  --target $(python -m app.cli list-targets | awk '{print $1}' | head -1) \
  --packs prompt-injection,jailbreak \
  --dry-run
```

### Full live scan

```bash
python -m app.cli scan-real \
  --url https://your-llm-api.com/chat \
  --name my-llm \
  --response-path data.reply \
  --no-dry-run
```

### Docker full stack + web frontend

```bash
docker compose up --build          # backend on :8000
cd aegis-llm-web && npm install && npm run dev  # frontend on :3000
```
