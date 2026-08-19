# Aegis-LLM Web Dashboard — UI Feature & Screen Documentation

This document provides a detailed breakdown of all pages, features, and visual components of the **Aegis-LLM Red-Teaming Platform** user interface (`http://localhost:3000`).

---

## 1. Executive Dashboard (`/`)

The **Main Dashboard** serves as the central command center for security operators and engineers to assess the security posture of their LLM deployments.

### Key Sections:

#### A. Metric Overview Cards
* **Active Runs**: Displays the number of attack simulations currently running in real-time versus total historical runs.
* **Open Findings**: Aggregates all un-remediated vulnerabilities across all registered targets.
* **High / Critical Needs Triage**: Highlights severe vulnerabilities (PII leaks, credential exposure, prompt injections) requiring immediate review.
* **Targets Allow-Listed**: Tracks the safety posture by displaying the ratio of approved/allow-listed targets versus total registered systems.

#### B. Security Analytics & Coverage Charts
* **OWASP LLM Coverage Bar Chart**: Maps detected vulnerabilities to standard security framework categories:
  * **LLM01**: Prompt Injection
  * **LLM02**: Insecure Output Handling
  * **LLM06**: Excessive Agency / Tool Abuse
  * **LLM07**: System Prompt Leakage
* **Severity Trend Graph**: Historical timeline plotting daily vulnerability occurrences broken down by severity level (Critical, High, Medium, Low).

#### C. Live Activity & Triage Panels
* **Recent Runs**: Quick-access feed showing the latest execution statuses (`Completed`, `Running`, `Failed`) for target applications (e.g., `acme-chat`, `sales-agent-api`).
* **Needs Triage**: Priority queue displaying unresolved security findings with risk level badges (e.g., *PII disclosure*, *Secret/credential disclosure*, *Guardrail bypass*, *Direct prompt injection*).

---

## 2. Target Management (`/targets`)

The **Targets** page enforces Aegis-LLM's core safety directive: **No system can be tested unless explicitly authorized**.

### Features:
* **Register Target**: Allows operators to define new LLM endpoints (REST endpoints or Playwright browser automation targets).
* **Allow-listing Enforcement**: Targets start in a `CLOSED` / `Blocked` state. Admins must explicitly review and allow-list a target before any red-teaming payload can be sent.
* **Target Table**: Lists target names, connector types (`REST`, `Browser`), endpoint URLs (e.g., `http://127.0.0.1:8100/chat`), approval statuses, and administrator sign-offs.

---

## 3. Payload Packs Library (`/payload-packs`)

The **Payload Packs** page hosts versioned adversarial test suites used during red-teaming runs.

### Bundled Attack Packs:
1. **`prompt-injection` (v1.0.0)**: Direct and indirect prompt injection attack vectors (mapped to `LLM01`, `MITRE ATLAS AML.T0051`, `AML.T0050`).
2. **`jailbreak` (v1.0.0)**: Persona override, refusal bypass, and guardrail circumventing payloads (mapped to `LLM01`, `AML.T0026`).
3. **`data-exfiltration` (v1.0.0)**: System prompt extraction and PII/credential scraping probes (mapped to `LLM02`, `LLM07`, `AML.T0040`).
4. **`tool-abuse` (v1.0.0)**: Function/tool-calling abuse and excessive agency exploits (mapped to `LLM06`, `AML.T0051`).

---

## 4. Attack Runs History (`/runs`)

The **Runs** page provides a complete, auditable record of all automated red-teaming evaluations.

### Table Columns:
* **Target**: Name of the tested model/application.
* **Status**: Execution state (`Completed`, `Running`, `Failed`).
* **Findings**: Total vulnerabilities uncovered during the run.
* **Mode**: Distinguishes between `live` runs (sent to target) and `dry-run` sessions (pipeline dry-run without network calls).
* **Tokens & Cost**: Tracks LLM token usage and estimated monetary execution cost.
* **Operator & Timestamp**: Audit log of who initiated the scan and when.
* **New Run Trigger**: Top-right action button to dispatch new custom attack runs.

---

## 5. Vulnerabilities & Findings Database (`/findings`)

The **Findings** page offers granular vulnerability management for security analysts and developers.

### Features:
* **Filtering & Search**: Search findings by keyword or filter by severity level (Critical, High, Medium, Low).
* **Export Capabilities**: `Export CSV` button for offline audit reporting and ticket creation.
* **Vulnerability Table Details**:
  * **Severity**: Color-coded risk rating.
  * **Confidence**: Model detector certainty percentage (e.g., 95% confidence on PII leak detection).
  * **Category & Standards**: Mapped OWASP LLM Top 10 ID and MITRE ATLAS Technique ID.
  * **Description**: Detailed description of the exploited flaw (e.g., *System prompt leakage suspected in model output*).
  * **Status**: Open, acknowledged, or resolved states.

---

## 6. Settings & CI/CD Governance (`/settings`)

The **Settings** page manages platform credentials, role-based access control, and integration policies.

### Settings Sections:
* **Current User Identity**: Shows user authentication details, email, and active role (`ADMIN`).
* **User Management (RBAC)**: Supports 3 permission tiers:
  * **Viewer**: Read-only access to reports and metrics.
  * **Operator**: Can execute runs and manage targets.
  * **Admin**: Full access including user management and system settings.
* **Integrations & Build Gates**:
  * **Slack Notifications**: Toggle for instant critical finding alerts.
  * **CI/CD Policy Gate**: Enables automated PR blocking (`POST /ci/gate`) when security scan results exceed configured severity thresholds.
