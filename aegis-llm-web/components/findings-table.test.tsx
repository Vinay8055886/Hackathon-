import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Finding } from "@/lib/api/schemas";
import { FindingsTable } from "@/components/findings-table";

const MOCK_FINDINGS: Finding[] = [
  {
    id: "f-1",
    run_id: "r-1",
    target_id: "t-1",
    title: "System prompt leakage suspected in model output",
    category: "system_prompt_leak",
    owasp_category: "LLM07",
    mitre_atlas_id: "AML.T0040",
    severity: "medium",
    confidence: 0.8,
    redacted_evidence: {},
    remediation_guidance: "Treat the system prompt as confidential.",
    status: "open",
    detector: "prompt_leak",
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "f-2",
    run_id: "r-1",
    target_id: "t-1",
    title: "Secret/credential disclosure: api key, password, db url",
    category: "secret_leak",
    owasp_category: "LLM02",
    mitre_atlas_id: "AML.T0040",
    severity: "critical",
    confidence: 0.85,
    redacted_evidence: {},
    remediation_guidance: "Rotate leaked credentials immediately.",
    status: "triaged",
    detector: "secrets",
    created_at: "2026-01-01T00:00:01Z",
  },
  {
    id: "f-3",
    run_id: "r-2",
    target_id: "t-2",
    title: "PII disclosure: email detected in model output",
    category: "pii_leak",
    owasp_category: "LLM02",
    mitre_atlas_id: "AML.T0040",
    severity: "high",
    confidence: 0.95,
    redacted_evidence: {},
    remediation_guidance: "Apply output filtering for PII.",
    status: "open",
    detector: "pii",
    created_at: "2026-01-02T00:00:00Z",
  },
];

describe("FindingsTable", () => {
  it("renders all findings initially", () => {
    render(<FindingsTable findings={MOCK_FINDINGS} showRunLink={false} />);
    expect(screen.getByText("System prompt leakage suspected in model output")).toBeInTheDocument();
    expect(screen.getByText("Secret/credential disclosure: api key, password, db url")).toBeInTheDocument();
  });

  it("filters rows by the text search", async () => {
    const user = userEvent.setup();
    render(<FindingsTable findings={MOCK_FINDINGS} showRunLink={false} />);
    await user.type(screen.getByLabelText("Filter findings"), "credential");
    expect(screen.getByText("Secret/credential disclosure: api key, password, db url")).toBeInTheDocument();
    expect(screen.queryByText("System prompt leakage suspected in model output")).not.toBeInTheDocument();
  });

  it("filters rows by severity", async () => {
    const user = userEvent.setup();
    render(<FindingsTable findings={MOCK_FINDINGS} showRunLink={false} />);
    await user.click(screen.getByLabelText("Filter by severity"));
    await user.click(await screen.findByText("Critical"));
    expect(screen.getByText("Secret/credential disclosure: api key, password, db url")).toBeInTheDocument();
    expect(screen.queryByText("PII disclosure: email detected in model output")).not.toBeInTheDocument();
  });
});
