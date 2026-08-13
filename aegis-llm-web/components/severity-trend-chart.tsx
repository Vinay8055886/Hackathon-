"use client";

import { useMemo } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Finding } from "@/lib/api/schemas";

const SEVERITIES = ["critical", "high", "medium", "low"] as const;
const COLORS: Record<string, string> = {
  critical: "hsl(var(--severity-critical))",
  high: "hsl(var(--severity-high))",
  medium: "hsl(var(--severity-medium))",
  low: "hsl(var(--severity-low))",
};

/** Findings per severity bucketed by day (mock/real runs). */
export function SeverityTrendChart({ findings }: { findings: Finding[] }) {
  const data = useMemo(() => {
    type Bucket = { day: string; critical: number; high: number; medium: number; low: number };
    const buckets = new Map<string, Bucket>();
    for (const f of findings) {
      if (!f.created_at) continue;
      const day = f.created_at.slice(0, 10);
      const b = buckets.get(day) ?? { day, critical: 0, high: 0, medium: 0, low: 0 };
      b[f.severity] += 1;
      buckets.set(day, b);
    }
    return [...buckets.values()].sort((a, b) => a.day.localeCompare(b.day));
  }, [findings]);

  return (
    <div className="h-56 w-full">
      {data.length === 0 ? (
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No finding history to chart yet.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
            <Tooltip
              contentStyle={{ background: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {SEVERITIES.map((s) => (
              <Line key={s} type="monotone" dataKey={s} name={s} stroke={COLORS[s]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
