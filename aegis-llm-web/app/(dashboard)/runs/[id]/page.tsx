"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, FileText, OctagonX, RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useCancelRun, useRun } from "@/lib/hooks/use-runs";
import { useFindings } from "@/lib/hooks/use-findings";
import { useRunStream } from "@/lib/hooks/use-run-stream";
import { useTarget } from "@/lib/hooks/use-targets";
import { api } from "@/lib/api";
import { qk } from "@/lib/hooks/query-keys";
import { formatDate } from "@/lib/utils";
import { LiveAgentFeed } from "@/components/live-agent-feed";
import { RunStatusIndicator } from "@/components/run-status-indicator";
import { TokenBudgetMeter } from "@/components/token-budget-meter";
import { SeverityBadge } from "@/components/severity-badge";
import { OwaspMitreTag } from "@/components/owasp-mitre-tag";
import { RoleGate } from "@/components/role-gate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";

export default function RunDetailPage({ params }: { params: { id: string } }) {
  const runId = params.id;
  const router = useRouter();
  const { data: run, isLoading } = useRun(runId);
  const { data: target } = useTarget(run?.target_id);
  const findings = useFindings({ runId });
  const { status: streamStatus, events, reconnectAttempt } = useRunStream(runId);
  const cancelRun = useCancelRun();
  const ci = useQuery({
    queryKey: qk.ciGate(runId),
    queryFn: () => api.ciGate(runId),
    enabled: !!run && (run.status === "completed" || run.status === "failed"),
  });

  if (isLoading || !run) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const running = run.status === "scheduled" || run.status === "running";
  const ciPassed = ci.data?.passed;

  return (
    <div className="space-y-4">
      <Link href="/runs" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Runs
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold">{target?.name ?? run.target_id.slice(0, 8)}</h1>
            <RunStatusIndicator status={run.status} />
            {run.dry_run ? <Badge variant="secondary">dry-run</Badge> : <Badge className="bg-severity-low/15 text-severity-low">live</Badge>}
            {ci.data ? (
              <Badge className={ciPassed ? "bg-emerald-500/15 text-emerald-500" : "bg-severity-critical/15 text-severity-critical"}>
                CI gate {ciPassed ? "passed" : "blocked"}
              </Badge>
            ) : null}
          </div>
          <p className="mt-0.5 font-mono text-xs text-muted-foreground">
            run {run.id} · started {formatDate(run.created_at)} by {run.started_by}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {running ? (
            <RoleGate required="operator" mode="disable">
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm" disabled={cancelRun.isPending}>
                    <OctagonX className="h-4 w-4" /> Stop run
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Stop this run?</AlertDialogTitle>
                    <AlertDialogDescription>
                      The run will be marked cancelled. Interactions already recorded stay in the audit log.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={async () => {
                        await cancelRun.mutateAsync(run.id);
                        router.refresh();
                      }}
                    >
                      Stop run
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </RoleGate>
          ) : null}
          <Button asChild variant="outline" size="sm">
            <Link href={`/reports/${run.id}`}>
              <FileText className="h-4 w-4" /> Report
            </Link>
          </Button>
        </div>
      </div>

      {run.error ? (
        <div className="rounded border border-severity-critical/40 bg-severity-critical/10 p-3 text-sm text-severity-critical">
          {run.error}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Live agent activity</CardTitle>
          </CardHeader>
          <CardContent>
            <LiveAgentFeed events={events} streamStatus={streamStatus} reconnectAttempt={reconnectAttempt} />
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Budgets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <TokenBudgetMeter tokensUsed={run.tokens_used} tokenBudget={run.token_budget} costUsd={run.cost_estimate_usd} />
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Max turns</span>
                <span className="font-mono text-xs">
                  {Math.min(run.max_turns, events.filter((e) => e.event_type === "payload_selected").length)}/{run.max_turns}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Findings</span>
                <span className="font-mono text-xs">{run.findings_count}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Run summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Packs</span>
                <span className="font-mono text-xs">{run.payload_pack_ids.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tokens</span>
                <span className="font-mono text-xs">{run.tokens_used.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cost</span>
                <span className="font-mono text-xs">${run.cost_estimate_usd.toFixed(4)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Finished</span>
                <span className="text-xs">{formatDate(run.finished_at)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">Findings ({findings.data?.length ?? 0})</CardTitle>
          </div>
          {findings.isFetching ? <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" /> : null}
        </CardHeader>
        <CardContent>
          {(findings.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {running ? "No findings yet — the swarm is still working." : "No findings. The target resisted every payload in this run."}
            </p>
          ) : (
            <div className="space-y-2">
              {(findings.data ?? []).map((f) => (
                <Link key={f.id} href={`/findings/${f.id}`} className="flex flex-wrap items-center justify-between gap-2 rounded border p-3 hover:bg-muted/40">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{f.title}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-1.5">
                      <OwaspMitreTag code={f.owasp_category} />
                      <OwaspMitreTag code={f.mitre_atlas_id} />
                      <span className="font-mono text-[11px] text-muted-foreground">{f.category}</span>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <span className="font-mono text-xs text-muted-foreground">{Math.round(f.confidence * 100)}% conf</span>
                    <SeverityBadge severity={f.severity} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
