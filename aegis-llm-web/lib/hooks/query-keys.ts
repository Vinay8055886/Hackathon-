export const qk = {
  healthz: ["healthz"] as const,
  me: ["me"] as const,
  targets: (allowlisted?: boolean) => ["targets", allowlisted ?? "all"] as const,
  target: (id: string) => ["target", id] as const,
  packs: ["packs"] as const,
  payloads: (packId: string) => ["payloads", packId] as const,
  runs: (status?: string) => ["runs", status ?? "all"] as const,
  run: (id: string) => ["run", id] as const,
  findings: (filters?: Record<string, string | undefined>) =>
    ["findings", filters ?? {}] as const,
  finding: (id: string) => ["finding", id] as const,
  report: (runId: string, format: string) => ["report", runId, format] as const,
  ciGate: (runId: string) => ["ciGate", runId] as const,
};
