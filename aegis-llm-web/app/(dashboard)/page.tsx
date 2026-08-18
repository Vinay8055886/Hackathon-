"use client";

import Link from "next/link";
import { Activity, Crosshair, Play, ShieldAlert, Target } from "lucide-react";
import { useFindings } from "@/lib/hooks/use-findings";
import { useRuns } from "@/lib/hooks/use-runs";
import { useTargets } from "@/lib/hooks/use-targets";
import { formatDate } from "@/lib/utils";
import { CoverageChart } from "@/components/coverage-chart";
import { SeverityTrendChart } from "@/components/severity-trend-chart";
import { SeverityBadge } from "@/components/severity-badge";
import { RunStatusIndicator } from "@/components/run-status-indicator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/empty-state";

export default function DashboardPage() {
  const runs = useRuns();
  const findings = useFindings();
  const targets = useTargets();

  const activeRuns = (runs.data ?? []).filter((r) => r.status === "scheduled" || r.status === "running");
  const allFindings = findings.data ?? [];
  const highCritical = allFindings.filter((f) => f.severity === "high" || f.severity === "critical");
  const allowlisted = (targets.data ?? []).filter((t) => t.allowlisted).length;
  const coveragePct =
    targets.data && targets.data.length > 0 ? Math.round((allowlisted / targets.data.length) * 100) : 0;

  const targetName = (id: string) => targets.data?.find((t) => t.id === id)?.name ?? id.slice(0, 8);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Attack posture across your LLM surface.</p>
        </div>
        <Button asChild>
          <Link href="/runs/new">
            <Play className="h-4 w-4" /> New run
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Active runs", value: activeRuns.length, icon: Activity, hint: `${(runs.data ?? []).length} total` },
          { label: "Open findings", value: allFindings.length, icon: Crosshair, hint: "all severities" },
          { label: "High / critical", value: highCritical.length, icon: ShieldAlert, hint: "needs triage", danger: true },
          { label: "Targets allow-listed", value: `${allowlisted}/${targets.data?.length ?? 0}`, icon: Target, hint: `${coveragePct}% of registered targets` },
        ].map(({ label, value, icon: Icon, hint, danger }) => (
          <Card key={label}>
            <CardContent className="flex items-start justify-between p-5">
              <div>
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className={`mt-1 text-2xl font-semibold ${danger && Number(value) > 0 ? "text-severity-critical" : ""}`}>{value}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>
              </div>
              <Icon className="h-5 w-5 text-muted-foreground" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">OWASP LLM coverage</CardTitle>
            <CardDescription>Findings per OWASP LLM Top 10 category</CardDescription>
          </CardHeader>
          <CardContent>
            {findings.isLoading ? <Skeleton className="h-56 w-full" /> : <CoverageChart findings={allFindings} />}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Severity trend</CardTitle>
            <CardDescription>Findings per day by severity</CardDescription>
          </CardHeader>
          <CardContent>
            {findings.isLoading ? <Skeleton className="h-56 w-full" /> : <SeverityTrendChart findings={allFindings} />}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">Recent runs</CardTitle>
            <CardDescription>Latest attack runs</CardDescription>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link href="/runs">All runs</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {runs.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : (runs.data ?? []).length === 0 ? (
            <EmptyState title="No runs yet" description="Launch your first attack run to start building evidence." action={<Button asChild><Link href="/runs/new">Launch run</Link></Button>} />
          ) : (
            <div className="divide-y">
              {(runs.data ?? []).slice(0, 6).map((run) => (
                <Link key={run.id} href={`/runs/${run.id}`} className="flex items-center justify-between gap-3 py-3 hover:bg-muted/40">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{targetName(run.target_id)}</p>
                    <p className="text-xs text-muted-foreground">
                      {run.dry_run ? "dry-run · " : ""}
                      {run.run_origin === "demo" ? "demo · " : ""}
                      started {formatDate(run.created_at)}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <span className="text-xs text-muted-foreground">{run.findings_count} findings</span>
                    <RunStatusIndicator status={run.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {highCritical.length > 0 ? (
        <Card className="border-severity-critical/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base text-severity-critical">
              <ShieldAlert className="h-4 w-4" /> Needs triage
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {highCritical.slice(0, 5).map((f) => (
              <Link key={f.id} href={`/findings/${f.id}`} className="flex items-center justify-between gap-3 py-1.5 hover:bg-muted/40">
                <span className="truncate text-sm">{f.title}</span>
                <SeverityBadge severity={f.severity} />
              </Link>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
