"use client";

import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";
import { useRun } from "@/lib/hooks/use-runs";
import { useTarget } from "@/lib/hooks/use-targets";
import { formatDate } from "@/lib/utils";
import { ReportViewer } from "@/components/report-viewer";
import { RunStatusIndicator } from "@/components/run-status-indicator";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function ReportDetailPage({ params }: { params: { id: string } }) {
  const runId = params.id;
  const { data: run, isLoading: runLoading } = useRun(runId);
  const { data: target } = useTarget(run?.target_id);

  if (runLoading || !run) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-[600px] w-full" />
      </div>
    );
  }

  const targetName = target?.name ?? run.target_id.slice(0, 8);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Link
            href={`/runs/${runId}`}
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Run
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <FileText className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-semibold">Security Audit Report: {targetName}</h1>
            <RunStatusIndicator status={run.status} />
            {run.dry_run ? (
              <Badge variant="secondary">dry-run</Badge>
            ) : (
              <Badge className="bg-severity-low/15 text-severity-low">live</Badge>
            )}
          </div>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            Run ID: {run.id} · Generated {formatDate(run.finished_at || run.created_at)} · Findings: {run.findings_count}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Audit Findings & Remediation Report</CardTitle>
          <CardDescription>
            Download full audit artifacts in HTML, SARIF 2.1.0 (for CI/CD and GitHub Security), or raw JSON.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ReportViewer runId={runId} />
        </CardContent>
      </Card>
    </div>
  );
}
