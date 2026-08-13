import { z } from "zod";

// ── Target ──────────────────────────────────────────────────────────────────
export const connectorTypeSchema = z.enum(["rest", "browser", "websocket"]);

export const targetSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().default(""),
  connector_type: connectorTypeSchema,
  endpoint: z.string(),
  config: z.record(z.string(), z.unknown()).default({}),
  allowlisted: z.boolean().default(false),
  approved_by: z.string().nullable().default(null),
  approval_note: z.string().default(""),
  owner_id: z.string(),
  auth_ref: z.string().nullable().default(null),
  rate_limit_per_minute: z.number().nullable().default(null),
  max_tokens_per_run: z.number().nullable().default(null),
  created_at: z.string().nullable().default(null),
  updated_at: z.string().nullable().default(null),
});

export const targetCreateSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().default(""),
  connector_type: connectorTypeSchema,
  endpoint: z.string().url(),
  config: z.record(z.string(), z.unknown()).default({}),
  auth_ref: z.string().nullable().optional(),
  rate_limit_per_minute: z.number().int().positive().nullable().optional(),
  max_tokens_per_run: z.number().int().positive().nullable().optional(),
});

export const allowlistRequestSchema = z.object({
  allowlisted: z.boolean().default(true),
  approved_by: z.string().min(1),
  approval_note: z.string().default(""),
});

// ── Payload packs ───────────────────────────────────────────────────────────
export const payloadPackSchema = z.object({
  id: z.string(),
  name: z.string(),
  version: z.string(),
  description: z.string().default(""),
  owasp_categories: z.array(z.string()).default([]),
  mitre_atlas_ids: z.array(z.string()).default([]),
  tags: z.array(z.string()).default([]),
  source: z.string().default("bundled"),
  payload_count: z.number().default(0),
  created_at: z.string().nullable().default(null),
});

export const payloadSchema = z.object({
  id: z.string(),
  pack_id: z.string(),
  slug: z.string(),
  name: z.string(),
  risk: z.string(),
  attack_vector: z.string(),
  owasp_category: z.string(),
  mitre_atlas_id: z.string(),
  priority: z.number().default(1),
  tags: z.array(z.string()).default([]),
  messages: z.array(z.record(z.string(), z.unknown())).default([]),
  created_at: z.string().nullable().default(null),
});

// ── Runs ────────────────────────────────────────────────────────────────────
export const runStatusSchema = z.enum([
  "scheduled",
  "running",
  "completed",
  "failed",
  "cancelled",
]);

export const runSchema = z.object({
  id: z.string(),
  target_id: z.string(),
  payload_pack_ids: z.array(z.string()).default([]),
  status: runStatusSchema,
  dry_run: z.boolean(),
  started_by: z.string(),
  max_turns: z.number(),
  token_budget: z.number(),
  tokens_used: z.number().default(0),
  cost_estimate_usd: z.number().default(0),
  findings_count: z.number().default(0),
  error: z.string().nullable().default(null),
  created_at: z.string().nullable().default(null),
  started_at: z.string().nullable().default(null),
  finished_at: z.string().nullable().default(null),
});

export const runCreateSchema = z.object({
  target_id: z.string().min(1, "Target is required"),
  payload_pack_ids: z.array(z.string()).min(1, "Pick at least one payload pack"),
  dry_run: z.boolean().optional(),
  max_turns: z.coerce.number().int().min(1).max(200).optional(),
  token_budget: z.coerce.number().int().positive().optional(),
});

// ── Findings ────────────────────────────────────────────────────────────────
export const severitySchema = z.enum(["low", "medium", "high", "critical"]);

export const findingSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  target_id: z.string(),
  title: z.string(),
  category: z.string(),
  owasp_category: z.string(),
  mitre_atlas_id: z.string(),
  severity: severitySchema,
  confidence: z.number(),
  redacted_evidence: z.record(z.string(), z.unknown()).default({}),
  remediation_guidance: z.string().default(""),
  status: z.string().default("open"),
  detector: z.string().default(""),
  created_at: z.string().nullable().default(null),
});

// ── Agent events (SSE payload) ──────────────────────────────────────────────
export const agentEventSchema = z.object({
  sequence: z.number(),
  run_id: z.string(),
  agent: z.string(),
  event_type: z.string(),
  payload: z.record(z.string(), z.unknown()).default({}),
});

// ── Auth / me ───────────────────────────────────────────────────────────────
export const loginResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().default("bearer"),
  expires_in: z.number(),
});

export const meSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string(),
  role: z.enum(["viewer", "operator", "admin"]),
  is_active: z.boolean().default(true),
  created_at: z.string().nullable().default(null),
});

export const userCreateSchema = z.object({
  username: z.string().min(3).max(128),
  email: z.string().email(),
  password: z.string().min(8),
  role: z.enum(["viewer", "operator", "admin"]),
});

// ── Reports / CI / health ───────────────────────────────────────────────────
export const reportSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  format: z.enum(["html", "sarif", "json"]),
  storage_path: z.string(),
  size_bytes: z.number(),
  generated_by: z.string().default("system"),
  created_at: z.string().nullable().default(null),
});

export const ciGateSchema = z.object({
  passed: z.boolean(),
  blocking_findings: z.array(z.record(z.string(), z.unknown())).default([]),
  total_findings: z.number(),
  threshold: z.string(),
  message: z.string(),
  sarif: z.record(z.string(), z.unknown()).nullable().default(null),
});

export const healthzSchema = z.object({
  status: z.string(),
  env: z.string().optional(),
  runner: z.string().optional(),
  database: z.string().optional(),
  redis: z.string().optional(),
  vector_store: z.string().optional(),
});

export type Target = z.infer<typeof targetSchema>;
export type TargetCreate = z.infer<typeof targetCreateSchema>;
export type AllowlistRequest = z.infer<typeof allowlistRequestSchema>;
export type PayloadPack = z.infer<typeof payloadPackSchema>;
export type Payload = z.infer<typeof payloadSchema>;
export type Run = z.infer<typeof runSchema>;
export type RunCreate = z.infer<typeof runCreateSchema>;
export type RunStatus = z.infer<typeof runStatusSchema>;
export type Finding = z.infer<typeof findingSchema>;
export type Severity = z.infer<typeof severitySchema>;
export type AgentEvent = z.infer<typeof agentEventSchema>;
export type LoginResponse = z.infer<typeof loginResponseSchema>;
export type Me = z.infer<typeof meSchema>;
export type Report = z.infer<typeof reportSchema>;
export type CiGate = z.infer<typeof ciGateSchema>;
export type Healthz = z.infer<typeof healthzSchema>;
