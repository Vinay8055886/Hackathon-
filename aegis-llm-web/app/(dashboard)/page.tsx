"use client";

import { useState } from "react";
import Link from "next/link";
import { Activity, Crosshair, Play, ShieldAlert, Target } from "lucide-react";
import { useFindings } from "@/lib/hooks/use-findings";
import { useRuns } from "@/lib/hooks/use-runs";
import { useTargets } from "@/lib/hooks/use-targets";
import { useRunStream } from "@/lib/hooks/use-run-stream";
import { formatDate } from "@/lib/utils";
import { CoverageChart } from "@/components/coverage-chart";
import { SeverityTrendChart } from "@/components/severity-trend-chart";
import { SeverityBadge } from "@/components/severity-badge";
import { RunStatusIndicator } from "@/components/run-status-indicator";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/empty-state";

export default function DashboardPage() {
  const [selectedCard, setSelectedCard] = useState<string | null>(null);

  const runs = useRuns();
  const findings = useFindings();
  const targets = useTargets();

  const activeRuns = (runs.data ?? []).filter(
    (r) => r.status === "scheduled" || r.status === "running",
  );

  // Connect to the currently active Aegis run.
  const liveRunId = activeRuns[0]?.id;
  const runStream = useRunStream(liveRunId);

  const allFindings = findings.data ?? [];

  const highCritical = allFindings.filter(
    (f) => f.severity === "high" || f.severity === "critical",
  );

  const allowlisted = (targets.data ?? []).filter(
    (t) => t.allowlisted,
  ).length;

  const coveragePct =
    targets.data && targets.data.length > 0
      ? Math.round((allowlisted / targets.data.length) * 100)
      : 0;

  const targetName = (id: string) =>
    targets.data?.find((t) => t.id === id)?.name ?? id.slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Dashboard header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Attack posture across your LLM surface.
          </p>
        </div>

        <Button asChild>
          <Link href="/runs/new">
            <Play className="h-4 w-4" />
            New run
          </Link>
        </Button>
      </div>

      {/* Interactive dashboard cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Active runs",
            value: activeRuns.length,
            icon: Activity,
            hint: `${(runs.data ?? []).length} total`,
            details: `There are ${activeRuns.length} attack runs currently active.`,
          },
          {
            label: "Open findings",
            value: allFindings.length,
            icon: Crosshair,
            hint: "all severities",
            details: `${allFindings.length} security findings require review.`,
          },
          {
            label: "High / critical",
            value: highCritical.length,
            icon: ShieldAlert,
            hint: "needs triage",
            danger: true,
            details: `${highCritical.length} high or critical findings need immediate triage.`,
          },
          {
            label: "Targets allow-listed",
            value: `${allowlisted}/${targets.data?.length ?? 0}`,
            icon: Target,
            hint: `${coveragePct}% of registered targets`,
            details: `${coveragePct}% of registered targets are currently allow-listed.`,
          },
        ].map(
          ({
            label,
            value,
            icon: Icon,
            hint,
            danger,
            details,
          }) => (
            <div key={label} className="relative">
              <Card
                className="cursor-pointer transition-all hover:border-primary/50 hover:shadow-md"
                onClick={() =>
                  setSelectedCard(
                    selectedCard === label ? null : label,
                  )
                }
              >
                <CardContent className="flex items-start justify-between p-5">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {label}
                    </p>

                    <p
                      className={`mt-1 text-2xl font-semibold ${
                        danger && Number(value) > 0
                          ? "text-severity-critical"
                          : ""
                      }`}
                    >
                      {value}
                    </p>

                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {hint}
                    </p>
                  </div>

                  <Icon className="h-5 w-5 text-muted-foreground" />
                </CardContent>
              </Card>

              {selectedCard === label && (
                <div className="absolute left-0 top-full z-20 mt-2 w-full rounded-lg border bg-card p-4 shadow-xl">
                  <p className="text-sm font-semibold">{label}</p>

                  <p className="mt-1 text-xs text-muted-foreground">
                    {details}
                  </p>

                  <button
                    type="button"
                    className="mt-3 text-xs font-medium text-primary hover:underline"
                    onClick={(event) => {
                      event.stopPropagation();
                      setSelectedCard(null);
                    }}
                  >
                    Close
                  </button>
                </div>
              )}
            </div>
          ),
        )}
      </div>

      {/* Live Attack Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4 text-severity-low" />

            Live Attack Activity

            <span
              className={`ml-auto flex items-center gap-1 text-xs font-normal ${
                runStream.status === "open"
                  ? "text-severity-low"
                  : runStream.status === "connecting" ||
                      runStream.status === "reconnecting"
                    ? "text-yellow-500"
                    : "text-muted-foreground"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  runStream.status === "open"
                    ? "animate-pulse bg-severity-low"
                    : runStream.status === "connecting" ||
                        runStream.status === "reconnecting"
                      ? "animate-pulse bg-yellow-500"
                      : "bg-muted-foreground"
                }`}
              />

              {runStream.status === "open"
                ? "LIVE"
                : runStream.status === "connecting"
                  ? "CONNECTING"
                  : runStream.status === "reconnecting"
                    ? "RECONNECTING"
                    : "IDLE"}
            </span>
          </CardTitle>

          <CardDescription>
            Real-time Aegis agent workflow and security events
          </CardDescription>
        </CardHeader>

        <CardContent>
          {runStream.events.length === 0 ? (
            <div className="rounded-lg border border-dashed p-6 text-center">
              <Activity className="mx-auto mb-2 h-6 w-6 text-muted-foreground" />

              <p className="text-sm font-medium">
                {liveRunId
                  ? "Waiting for agent activity..."
                  : "No active attack run"}
              </p>

              <p className="mt-1 text-xs text-muted-foreground">
                {liveRunId
                  ? "Aegis is connected and waiting for the next agent event."
                  : "Start a new run to see live attacker, target, judge and memory events here."}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {runStream.events
                .slice(-8)
                .reverse()
                .map((event) => {
                  const isFinding =
                    event.event_type === "finding_recorded";

                  const isFinished =
                    event.event_type === "run_finished" ||
                    event.event_type === "run_failed";

                  const payloadEntries = Object.entries(
                    event.payload ?? {},
                  ).slice(0, 5);

                  return (
                    <div
                      key={event.sequence}
                      className="rounded-lg border p-3 transition-colors hover:bg-muted/40"
                    >
                      <div className="flex items-start gap-3">
                        {/* Event status indicator */}
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-background">
                          <span
                            className={`h-2.5 w-2.5 rounded-full ${
                              isFinding
                                ? "bg-severity-critical"
                                : isFinished
                                  ? "bg-severity-low"
                                  : "bg-primary"
                            }`}
                          />
                        </div>

                        {/* Event information */}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-semibold capitalize">
                              {event.agent}
                            </p>

                            {isFinding && (
                              <span className="rounded-full bg-severity-critical/10 px-2 py-0.5 text-[10px] font-medium text-severity-critical">
                                FINDING
                              </span>
                            )}

                            {isFinished && (
                              <span className="rounded-full bg-severity-low/10 px-2 py-0.5 text-[10px] font-medium text-severity-low">
                                COMPLETE
                              </span>
                            )}
                          </div>

                          <p className="text-xs capitalize text-muted-foreground">
                            {event.event_type.replaceAll("_", " ")}
                          </p>

                          {/* Real backend payload */}
                          {payloadEntries.length > 0 && (
                            <div className="mt-2 rounded-md border bg-muted/20 px-3 py-2">
                              <div className="space-y-1">
                                {payloadEntries.map(([key, value]) => (
                                  <div
                                    key={key}
                                    className="flex items-start gap-2 text-[11px]"
                                  >
                                    <span className="shrink-0 text-muted-foreground">
                                      {key.replaceAll("_", " ")}:
                                    </span>

                                    <span className="min-w-0 truncate font-medium">
                                      {typeof value === "object" &&
                                      value !== null
                                        ? JSON.stringify(value)
                                        : String(value)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Event sequence */}
                        <span className="shrink-0 text-[11px] text-muted-foreground">
                          #{event.sequence}
                        </span>
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* OWASP and Severity charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              OWASP LLM coverage
            </CardTitle>

            <CardDescription>
              Findings per OWASP LLM Top 10 category
            </CardDescription>
          </CardHeader>

          <CardContent>
            {findings.isLoading ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <CoverageChart findings={allFindings} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Severity trend
            </CardTitle>

            <CardDescription>
              Findings per day by severity
            </CardDescription>
          </CardHeader>

          <CardContent>
            {findings.isLoading ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <SeverityTrendChart findings={allFindings} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent runs */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">
              Recent runs
            </CardTitle>

            <CardDescription>
              Latest attack runs
            </CardDescription>
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
            <EmptyState
              title="No runs yet"
              description="Launch your first attack run to start building evidence."
              action={
                <Button asChild>
                  <Link href="/runs/new">Launch run</Link>
                </Button>
              }
            />
          ) : (
            <div className="divide-y">
              {(runs.data ?? []).slice(0, 6).map((run) => (
                <Link
                  key={run.id}
                  href={`/runs/${run.id}`}
                  className="flex items-center justify-between gap-3 py-3 hover:bg-muted/40"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {targetName(run.target_id)}
                    </p>

                    <p className="text-xs text-muted-foreground">
                      {run.dry_run ? "dry-run · " : ""}
                      {run.run_origin === "demo" ? "demo · " : ""}
                      started {formatDate(run.created_at)}
                    </p>
                  </div>

                  <div className="flex shrink-0 items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      {run.findings_count} findings
                    </span>

                    <RunStatusIndicator status={run.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* High/Critical findings */}
      {highCritical.length > 0 ? (
        <Card className="border-severity-critical/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base text-severity-critical">
              <ShieldAlert className="h-4 w-4" />
              Needs triage
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-2">
            {highCritical.slice(0, 5).map((f) => (
              <Link
                key={f.id}
                href={`/findings/${f.id}`}
                className="flex items-center justify-between gap-3 py-1.5 hover:bg-muted/40"
              >
                <span className="truncate text-sm">
                  {f.title}
                </span>

                <SeverityBadge severity={f.severity} />
              </Link>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}