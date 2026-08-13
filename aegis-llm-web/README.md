# Aegis-LLM Web — Operator Console

The web frontend for the **Aegis-LLM** multi-agent LLM red-teaming platform: a
dark-mode-first, dense operator dashboard for registering targets, launching
attack runs, watching the Attacker → Judge → Refiner → Memory swarm in real
time, triaging findings, and exporting HTML/SARIF/JSON reports.

Built with **Next.js 14 (App Router) + TypeScript**, **shadcn/ui + Tailwind**,
**TanStack Query** (server state), **TanStack Table** (data grids), **Zustand**
(local UI state), **Recharts** (charts), **React Hook Form + Zod** (forms), and
**NextAuth.js** (sessions, credentials + OIDC).

## Getting started

```bash
npm install
cp .env.example .env.local      # then edit as needed
npm run dev                     # http://localhost:3000
```

Default local config: **mock mode** (`NEXT_PUBLIC_API_MOCK=true`) — the app
serves an in-memory dataset with a simulated live stream, so it runs with no
backend at all. Any credentials sign in (as `admin`).

## Mock mode vs live backend

| | Mock (`NEXT_PUBLIC_API_MOCK=true`) | Live |
|---|---|---|
| Data | In-memory seed (targets, packs, runs, findings) | FastAPI REST API |
| Stream | Simulated agent events | `GET /runs/{id}/stream` (SSE) |
| Auth | Any credentials → mock admin | `POST /auth/login` → JWT |
| Backend | none | `uvicorn app.main:app --port 8000` |

To point at a real backend, set `NEXT_PUBLIC_API_MOCK=false` and
`NEXT_PUBLIC_API_URL=http://localhost:8000`. The typed API client
(`lib/api/`) validates every response against Zod schemas mirroring the
backend contract (Section 3 of the build prompt), so drift surfaces loudly.

## Auth & RBAC

- **NextAuth.js** with a Credentials provider that authenticates against the
  backend's `POST /auth/login` and stores the returned JWT in the session; the
  API client attaches `Authorization: Bearer <token>` automatically.
- **OIDC/SSO**: set `OIDC_ISSUER`/`OIDC_CLIENT_ID`/`OIDC_CLIENT_SECRET` for
  Okta / Azure AD / Google Workspace.
- Roles (`viewer` / `operator` / `admin`) come from `GET /auth/me` and are
  gated client-side with `<RoleGate>` — **allow-listing a target, launching a
  live run, and stopping a run all require operator+**.
- `middleware.ts` redirects unauthenticated traffic to `/login`.

> Client-side gating is UX, not a security boundary — the backend enforces the
> same checks at the interaction layer.

## Pages

- `/login` — sign-in (credentials; SSO button when configured)
- `/` — dashboard: active runs, findings by severity, OWASP coverage +
  severity trend charts, recent runs, triage queue
- `/targets` · `/targets/new` · `/targets/[id]` — register, list, and manage
  targets; the allow-list flow is role-gated with an explicit confirmation
  dialog and audit note
- `/payload-packs` — versioned packs with OWASP LLM Top 10 / MITRE ATLAS
  chips and per-payload expansion
- `/runs` · `/runs/new` · `/runs/[id]` — run history with filters; run
  configuration (dry-run on by default); the **live run view** with the
  reconnecting SSE feed, agent status, token/cost budget meter, live findings,
  and a role-gated stop control
- `/findings` · `/findings/[id]` — filter/sort/paginate/CSV-export findings;
  detail with redacted evidence + remediation + linked run
- `/reports/[runId]` — inline HTML report preview + SARIF/JSON/HTML downloads
- `/settings` — current user + role, Slack alert toggle, CI gate status,
  RBAC user management, platform status (healthz, runner, vector store)

## Real-time layer

`useRunStream` (`lib/hooks/use-run-stream.ts`) opens the run's SSE stream via
`fetch` (the backend requires an `Authorization` header, which plain
`EventSource` cannot send), parses `data:` frames, **reconnects with
exponential backoff** (1s → 15s cap), exposes a connection status
(`open` / `reconnecting` / `closed`), and **merges events into the TanStack
Query cache** so run lists, detail views, and findings stay consistent.
In mock mode it streams a simulated event sequence.

## Tests

```bash
npm test        # vitest run
```

Coverage: `SeverityBadge` color/label mapping, `RoleGate` hide/disable
semantics, `FindingsTable` text + severity filtering.

## Notes on defaults chosen

- **Next.js 14** (stable App Router, sync route params) over 15.
- **Zustand** over Redux Toolkit — the only cross-cutting UI state is the
  session mirror + sidebar collapse.
- SSE over WebSocket — the backend exposes `GET /runs/{id}/stream` (SSE) and
  replay of history, which is the simpler contract for one-directional events.
- `GET /runs/{id}/report?format=` returns JSON metadata in real mode; the
  report body is fetched with the auth header and rendered via
  `iframe srcdoc` / blob download, since iframes cannot send bearer headers.
