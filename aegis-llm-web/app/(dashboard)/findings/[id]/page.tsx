"use client";

import Link from "next/link";
import { ArrowLeft, TicketPlus } from "lucide-react";
import { useFinding } from "@/lib/hooks/use-findings";
import { useRun } from "@/lib/hooks/use-runs";
import { useTarget } from "@/lib/hooks/use-targets";
import { formatDate } from "@/lib/utils";
import { SeverityBadge } from "@/components/severity-badge";
import { OwaspMitreTag } from "@/components/owasp-mitre-tag";
import { RunStatusIndicator } from "@/components/run-status-indicator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

export default function FindingDetailPage({ params }: { params: { id: string } }) {
  const { data: finding, isLoading, isError } = useFinding(params.id);
  const { data: run } = useRun(finding?.run_id);
  const { data: target } = useTarget(finding?.target_id);

  if (isLoading || !finding) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (isError) return <p className="text-severity-critical">Finding not found.</p>;

  return (
    <div className="space-y-4">
      <Link href="/findings" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Findings
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold">{finding.title}</h1>
            <SeverityBadge severity={finding.severity} />
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
            <OwaspMitreTag code={finding.owasp_category} />
            <OwaspMitreTag code={finding.mitre_atlas_id} />
            <span className="font-mono text-xs">{finding.category}</span>
            <span>·</span>
            <span className="font-mono text-xs">detector: {finding.detector || "ensemble"}</span>
          </div>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <TicketPlus className="h-4 w-4" /> Create ticket
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create tracking ticket</DialogTitle>
              <DialogDescription>
                Ticketing integration stub — wire this to Jira/Linear via the backend alert integration.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2 text-sm">
              <p><b>Title:</b> {finding.title}</p>
              <p><b>Severity:</b> {finding.severity} · <b>Confidence:</b> {Math.round(finding.confidence * 100)}%</p>
              <p className="text-muted-foreground">A ticket would be created with the redacted evidence and remediation guidance attached.</p>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Evidence (redacted)</CardTitle>
              <CardDescription>Backend redaction is applied before storage or display — raw payloads and responses are never shown here.</CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="max-h-80 overflow-auto rounded border bg-muted/40 p-3 font-mono text-xs">
                {JSON.stringify(finding.redacted_evidence, null, 2)}
              </pre>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Remediation guidance</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{finding.remediation_guidance || "No guidance recorded."}</p>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Confidence</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Progress value={Math.round(finding.confidence * 100)} className={finding.confidence >= 0.8 ? "" : "bg-severity-medium/40"} />
              <p className="font-mono text-xs text-muted-foreground">{Math.round(finding.confidence * 100)}% — detector ensemble agreement</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Context</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <span>{finding.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Run</span>
                <Link href={`/runs/${finding.run_id}`} className="font-mono text-xs underline-offset-2 hover:underline">
                  {finding.run_id.slice(0, 8)}
                  {run ? ` · ${run.dry_run ? "dry-run" : "live"}` : ""}
                </Link>
              </div>
              {run ? (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Run status</span>
                  <RunStatusIndicator status={run.status} />
                </div>
              ) : null}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Target</span>
                {target ? (
                  <Link href={`/targets/${target.id}`} className="hover:underline">
                    {target.name}
                  </Link>
                ) : (
                  <span className="font-mono text-xs">{finding.target_id.slice(0, 8)}</span>
                )}
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Found</span>
                <span className="text-xs">{formatDate(finding.created_at)}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
