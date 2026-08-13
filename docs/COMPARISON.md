# Aegis-LLM vs Static LLM-Security Testing — Measuring the Difference

Static LLM security scanners (payload lists run once, single-turn, against an
endpoint) and Aegis-LLM answer different questions. This document defines how
we would *measure* the difference — detection rate, false-positive rate, and
coverage — so adoption decisions are evidence-based rather than vibes-based.

## 1. Definitions

| Metric | Definition |
|---|---|
| **Detection rate (recall)** | `confirmed attacks detected / total attacks present in the test corpus` — where "attack present" means the target actually exhibits the vulnerable behaviour. |
| **False-positive rate (FPR)** | `findings that are not real vulnerabilities / total findings` (per-run). A finding is a false positive if a human or a confirmed ground truth says the target's behaviour is actually correct. |
| **Coverage** | Fraction of the attack surface exercised: distinct OWASP LLM categories, MITRE ATLAS techniques, attack vectors (direct/indirect/multi-turn), and connector types probed. |

## 2. Why the numbers will differ

1. **Multi-turn adaptation.** Static tools fire one payload per case. Aegis-LLM
   runs Attacker → Judge → Refiner loops: a payload that fails once is mutated
   (role-play, indirect frame, encoding, social engineering, delimiters) and
   retried. On vulnerable targets, refinement *increases* detection rate
   versus the static baseline; on hardened targets, it raises coverage without
   adding false positives (the judge still demands evidence).
2. **Context-aware judging.** Static tools often flag on keyword matches.
   Aegis-LLM's detector ensemble scores confidence and requires
   `confidence ≥ 0.55` before a finding is recorded, which suppresses
   incidental matches (e.g. the word "password" in a benign reply) that inflate
   static-tool FPR.
3. **Guardrail-bypass state.** Refusal-then-compliance only exists across
   turns. Static single-turn tools cannot see it; Aegis-LLM's
   `guardrail_bypass` detector explicitly models conversation state.
4. **Indirect injection.** Static tools that only send `messages: [...]`
   cannot simulate attacker-controlled *retrieved content*; Aegis-LLM packs
   embed injected content in the user turn explicitly (document/email framing).

## 3. Proposed evaluation protocol

Run both tools against the same corpus and measure:

```
Corpus:  a "vulnerable" set (targets with known, injected weaknesses —
         e.g. the bundled mock target, plus 3 more stubs with system-prompt
         echo, PII leak, and tool-abuse behaviours)
         a "hardened" set (targets that refuse all of the above correctly)

Per target, run:
  1. Static tool: full payload list, one shot per payload.
  2. Aegis-LLM:  run with same packs, max_turns=10, detector ensemble only
                 (no LLM judge, to keep the comparison deterministic).

Compute:
  detection_rate   = confirmed / ground_truth_attacks
  fp_rate          = false_positive_findings / total_findings
  coverage         = |distinct (owasp, atlas, vector) probed| / |corpus space|
  cost             = requests, tokens, wall-clock per confirmed finding
```

## 4. Expected results (hypotheses to validate)

| Metric | Static tool | Aegis-LLM | Driver |
|---|---|---|---|
| Detection rate (vulnerable set) | ~60–75% | ~85–95% | refinement loop re-tries mutated variants; stateful judge catches multi-turn bypass |
| Detection rate (hardened set) | ~5–15% (keyword FPs) | ~1–5% | conservative confidence threshold suppresses noise |
| FPR | higher (keyword matching) | lower (evidence + confidence required) | ensemble + optional LLM confirmation |
| Coverage | single vector per payload | direct + indirect + multi_turn, 6 detector classes | pack metadata + vector field |
| Cost per confirmed finding | low (one shot) | higher (multi-turn) but bounded | explicit budgets: max_turns, token_budget |

These are hypotheses; the protocol above exists to validate them with data
before claiming superiority.

## 5. Guarding against overfitting the benchmark

- **Blind ground truth**: findings are labelled by an operator who did not
  write the payloads.
- **Deterministic judging**: default runs use the detector ensemble with no
  LLM so results are reproducible across runs (LLM judge is opt-in).
- **Seed stability**: payload ordering is deterministic (priority → risk →
  slug), so the only randomness is the target's own behaviour.
- **Coverage accounting**: report which (OWASP, ATLAS, vector) combinations
  were probed, so a high detection rate on two categories is not mistaken for
  broad coverage.

## 6. How to run the comparison in this repo

1. `python -m app.cli demo` — generates a baseline run against the bundled
   vulnerable mock target (known ground truth: prompt leak, PII leak, secret
   leak, guardrail bypass, injection compliance).
2. Add hardened stubs (targets that refuse everything) and record the same
   metrics via `GET /runs/{id}/report?format=json`.
3. Wire the numbers into a small report table; the `report` JSON already
   includes `by_severity`/`by_category`/`by_owasp` summaries and per-finding
   confidence for FPR analysis.
