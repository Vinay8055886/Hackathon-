"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Finding } from "@/lib/api/schemas";

/** Coverage of OWASP LLM categories — payload categories probed vs findings. */
export function CoverageChart({ findings }: { findings: Finding[] }) {
  const byOwasp = new Map<string, { category: string; findings: number }>();
  for (const f of findings) {
    const entry = byOwasp.get(f.owasp_category) ?? { category: f.owasp_category, findings: 0 };
    entry.findings += 1;
    byOwasp.set(f.owasp_category, entry);
  }
  const data = [...byOwasp.values()].sort((a, b) => b.findings - a.findings);

  return (
    <div className="h-56 w-full">
      {data.length === 0 ? (
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No findings yet — launch a run to build coverage.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -24 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
            <XAxis dataKey="category" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
            <Tooltip
              contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
              cursor={{ fill: "hsl(var(--muted))" }}
            />
            <Bar dataKey="findings" name="Findings" fill="hsl(var(--severity-low))" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
