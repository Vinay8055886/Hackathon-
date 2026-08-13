# Aegis-LLM Methodology

## 1. Objectives

An Aegis-LLM run answers one question with evidence: *"does this LLM-powered
product resist the attack patterns we know about (and variants of them)?"*

Three properties make the answer trustworthy:

- **Reproducible** — every run is a sequence of persisted `agent_events`; the
  same packs + target config + budgets replay the same behaviour.
- **Auditable** — every request/response pair is in `audit_log`, redacted
  before storage, and every finding links to the evidence that produced it.
- **Bounded** — runs carry explicit turn/token ceilings and targets carry rate
  limits, so testing never becomes a DoS against the system under test.

## 2. The attack lifecycle

```
1. REGISTER   Target is created CLOSED. Nothing can touch it.
2. ALLOW-LIST An operator approves it (identity + note). Required once.
3. PLAN       Operator picks payload packs; dry-run validates the pipeline.
4. RUN        Attacker → Interaction (guarded) → Judge → Refiner → repeat.
5. LEARN      Successful patterns boost payload priority, write KG edges,
              and join the vector store for similarity search.
6. REPORT     HTML (humans), SARIF (CI/code scanning), JSON (tooling).
7. GATE       CI policy gate blocks a PR when findings exceed thresholds.
```

## 3. The agent loop

At each turn, up to `max_turns`:

| Agent | Responsibility | Output |
|---|---|---|
| **Attacker** | Selects the next candidate payload. Feedback-loop priority first, then risk, then deterministic tie-break. Skips slugs already exhausted this run. | a `messages` list |
| **Interaction** | Guarded connector: allow-list → rate limit → token budget → circuit breaker → request → redacted audit log. | `{status, body, tokens, duration}` |
| **Judge** | Detector ensemble (+ optional LLM judge for borderline calls). A detection is accepted at confidence ≥ 0.55; severity = worst accepted detection. | `{success, confidence, severity, detections}` |
| **Refiner** | On failure, mutates the payload with a deterministic strategy (role-play frame, indirect frame, case obfuscation, base64 encoding, social engineering, delimiter injection), tracked in the event log. | mutated `messages` or `None` (exhausted) |
| **Memory** | Persists the turn transcript, writes findings (redacted evidence), and feeds the feedback loop. | persisted rows |

The loop terminates when: an attack is confirmed, all payloads are exhausted
(including refinements), `max_turns` is reached, the token budget is spent, or
the safety layer blocks (allow-list, rate limit, circuit breaker).

## 4. Detection classes

| Detector | What it flags | OWASP | MITRE ATLAS |
|---|---|---|---|
| `prompt_leak` | System-prompt echo (known fragments, structural markers, persona self-description) | LLM07 | AML.T0040 |
| `pii` | Emails, phones, SSNs, credit cards in output | LLM02 | AML.T0040 |
| `secrets` | API keys, AWS keys, JWTs, private keys, DB URLs, `password=` | LLM02 | AML.T0040 |
| `guardrail_bypass` | Refusal-then-compliance across turns; compliance with dangerous requests | LLM01 | AML.T0026 |
| `hallucination` | Citations/claims not present in the provided context | LLM09 | AML.T0051 |
| `resource_exhaustion` | Extreme output length or latency (unbounded consumption) | LLM10 | AML.T0034 |
| `LLM judge (optional)` | Confirms/refutes borderline detector calls via an OpenAI-compatible model | — | — |

Detector guidance: **conservative**. A false negative (missed attack) is
recorded in the audit trail; a false positive costs an operator's time. The
LLM judge, when enabled, is instructed to be conservative and only agrees on
clear evidence.

## 5. Evidence and redaction

- Raw request/response pairs are **never** persisted: `AuditLogger` runs the
  `Redactor` (16 secret/PII classes) before writing to `audit_log`.
- Findings store both `evidence` (internal, raw) and `redacted_evidence`;
  every API schema and every report renders only `redacted_evidence`.
- The SSE stream redacts response snippets before they leave the server.

## 6. Intelligence loop

After a confirmed finding, `FeedbackLoop`:

1. **Boosts** the winning payload's `priority` (×1.2, capped) so similar
   targets are probed with it first;
2. **Embeds** the transcript (hash embedding by default, or a configured
   embeddings API) into the vector store for similarity search;
3. **Writes graph edges** `technique:AML.T0051 -[compromises]-> target:X` and
   `target:X -[exhibits]-> weakness:prompt_injection` (SQL-backed by default,
   Neo4j adapter available).

## 7. CI/CD integration

- **SARIF 2.1.0** output maps severities to levels (critical/high → `error`,
  medium → `warning`, low → `note`) for native code-scanning ingestion.
- **Policy gate** (`POST /ci/gate`, `ci/policy_gate.sh`) evaluates findings
  against `{severity_threshold, min_confidence, block_categories}` and fails
  the build when any finding meets all criteria.
- **Chat alerts / ticketing** are integration points: consume
  `GET /findings?severity=critical` or the `finding_recorded` SSE events.
