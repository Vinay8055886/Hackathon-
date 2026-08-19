import {
  AllowlistRequest,
  AgentEvent,
  CiGate,
  Finding,
  Healthz,
  Me,
  Payload,
  PayloadPack,
  Report,
  Run,
  RunCreate,
  Target,
  TargetCreate,
} from "@/lib/api/schemas";
import { IS_MOCK, apiFetch } from "@/lib/api/client";
import * as mock from "@/lib/api/mock";

/**
 * Typed API facade. Every call goes through `mock.*` when
 * NEXT_PUBLIC_API_MOCK=true (local dev / preview without a live backend),
 * otherwise against the real FastAPI backend.
 */
export const api = {
  // ── health ────────────────────────────────────────────────────────────────
  healthz(): Promise<Healthz> {
    return IS_MOCK ? mock.healthz() : apiFetch<Healthz>("/healthz");
  },

  // ── targets ───────────────────────────────────────────────────────────────
  listTargets(allowlisted?: boolean): Promise<Target[]> {
    if (IS_MOCK) return mock.listTargets(allowlisted);
    const q = allowlisted === undefined ? "" : `?allowlisted=${allowlisted}`;
    return apiFetch<Target[]>(`/targets${q}`);
  },
  getTarget(id: string): Promise<Target> {
    return IS_MOCK ? mock.getTarget(id) : apiFetch<Target>(`/targets/${id}`);
  },
  createTarget(body: TargetCreate): Promise<Target> {
    return IS_MOCK ? mock.createTarget(body) : apiFetch<Target>("/targets", { method: "POST", body });
  },
  setAllowlist(id: string, body: AllowlistRequest): Promise<Target> {
    return IS_MOCK
      ? mock.setAllowlist(id, body)
      : apiFetch<Target>(`/targets/${id}/allowlist`, { method: "PATCH", body });
  },

  // ── payload packs ─────────────────────────────────────────────────────────
  listPayloadPacks(): Promise<PayloadPack[]> {
    return IS_MOCK ? mock.listPayloadPacks() : apiFetch<PayloadPack[]>("/payload-packs");
  },
  listPayloads(packId: string): Promise<Payload[]> {
    return IS_MOCK
      ? mock.listPayloads(packId)
      : apiFetch<Payload[]>(`/payload-packs/${packId}/payloads`);
  },

  // ── runs ──────────────────────────────────────────────────────────────────
  listRuns(status?: string, targetId?: string, runOrigin?: string): Promise<Run[]> {
    if (IS_MOCK) return mock.listRuns(status, targetId);
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (targetId) params.set("target_id", targetId);
    if (runOrigin) params.set("run_origin", runOrigin);
    const qs = params.toString();
    return apiFetch<Run[]>(`/runs${qs ? `?${qs}` : ""}`);
  },
  getRun(id: string): Promise<Run> {
    return IS_MOCK ? mock.getRun(id) : apiFetch<Run>(`/runs/${id}`);
  },
  createRun(body: RunCreate): Promise<Run> {
    return IS_MOCK ? mock.createRun(body) : apiFetch<Run>("/runs", { method: "POST", body });
  },
  cancelRun(id: string): Promise<Run> {
    return IS_MOCK ? mock.cancelRun(id) : apiFetch<Run>(`/runs/${id}/cancel`, { method: "PATCH" });
  },
  runEvents(id: string): Promise<AgentEvent[]> {
    return IS_MOCK ? mock.listRunEvents(id) : apiFetch<AgentEvent[]>(`/runs/${id}/events`);
  },

  // ── findings ──────────────────────────────────────────────────────────────
  listFindings(filters?: {
    severity?: string;
    runId?: string;
    category?: string;
    owaspCategory?: string;
  }): Promise<Finding[]> {
    if (IS_MOCK) return mock.listFindings(filters);
    const params = new URLSearchParams();
    if (filters?.severity) params.set("severity", filters.severity);
    if (filters?.runId) params.set("run_id", filters.runId);
    if (filters?.category) params.set("category", filters.category);
    if (filters?.owaspCategory) params.set("owasp_category", filters.owaspCategory);
    const qs = params.toString();
    return apiFetch<Finding[]>(`/findings${qs ? `?${qs}` : ""}`);
  },
  getFinding(id: string): Promise<Finding> {
    return IS_MOCK ? mock.getFinding(id) : apiFetch<Finding>(`/findings/${id}`);
  },

  // ── reports ───────────────────────────────────────────────────────────────
  getReportMeta(runId: string, format: "html" | "sarif" | "json"): Promise<Report> {
    return IS_MOCK
      ? mock.getReportMeta(runId, format)
      : apiFetch<Report>(`/runs/${runId}/report?format=${format}`);
  },
  async getReportText(runId: string, format: "html" | "sarif" | "json"): Promise<string> {
    if (IS_MOCK) return mock.getReportText(runId, format);
    return apiFetch<string>(`/runs/${runId}/report?format=${format}`, { raw: true });
  },

  // ── ci ────────────────────────────────────────────────────────────────────
  ciGate(runId: string, severityThreshold = "high", minConfidence = 0.6): Promise<CiGate> {
    return IS_MOCK
      ? mock.ciGate(runId, severityThreshold, minConfidence)
      : apiFetch<CiGate>("/ci/gate", {
          method: "POST",
          body: { run_id: runId, severity_threshold: severityThreshold, min_confidence: minConfidence, sarif: true },
        });
  },

  // ── auth ──────────────────────────────────────────────────────────────────
  me(): Promise<Me> {
    return IS_MOCK ? mock.me() : apiFetch<Me>("/auth/me");
  },
};

export * from "@/lib/api/client";
