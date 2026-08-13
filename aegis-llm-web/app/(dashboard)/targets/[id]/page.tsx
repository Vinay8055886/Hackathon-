"use client";

import Link from "next/link";
import { ArrowLeft, Play } from "lucide-react";
import { useTarget } from "@/lib/hooks/use-targets";
import { useRuns } from "@/lib/hooks/use-runs";
import { formatDate } from "@/lib/utils";
import { TargetAllowlistToggle } from "@/components/target-allowlist-toggle";
import { RunStatusIndicator } from "@/components/run-status-indicator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function TargetDetailPage({ params }: { params: { id: string } }) {
  const { data: target, isLoading, isError } = useTarget(params.id);
  const runs = useRuns(undefined, params.id);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  if (isError || !target) return <p className="text-severity-critical">Target not found.</p>;

  const targetRuns = (runs.data ?? []).slice(0, 8);

  return (
    <div className="space-y-4">
      <Link href="/targets" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Targets
      </Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">{target.name}</h1>
            {target.allowlisted ? (
              <Badge className="bg-emerald-500/15 text-emerald-500">Allow-listed</Badge>
            ) : (
              <Badge variant="secondary">Blocked</Badge>
            )}
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{target.description || target.endpoint}</p>
        </div>
        <div className="flex items-center gap-2">
          <TargetAllowlistToggle
            targetId={target.id}
            allowlisted={target.allowlisted}
            approvedBy={target.approved_by}
            approvalNote={target.approval_note}
          />
          {target.allowlisted ? (
            <Button asChild>
              <Link href={`/runs/new?target=${target.id}`}>
                <Play className="h-4 w-4" /> Launch run
              </Link>
            </Button>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Connector</span>
              <Badge variant="secondary">{target.connector_type}</Badge>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Endpoint</span>
              <span className="break-all font-mono text-xs">{target.endpoint}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Owner</span>
              <span className="font-mono text-xs">{target.owner_id}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Rate limit</span>
              <span className="font-mono text-xs">{target.rate_limit_per_minute ?? "default"}/min</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Token budget</span>
              <span className="font-mono text-xs">{target.max_tokens_per_run?.toLocaleString() ?? "default"}</span>
            </div>
            {Object.keys(target.config ?? {}).length > 0 ? (
              <div>
                <p className="mb-1 text-muted-foreground">Connector config</p>
                <pre className="overflow-x-auto rounded border bg-muted/40 p-2 font-mono text-xs">
                  {JSON.stringify(target.config, null, 2)}
                </pre>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Allow-list status</CardTitle>
            <CardDescription>Approval record — the audit trail for this target.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Status</span>
              <span>{target.allowlisted ? "Allow-listed" : "Blocked (cannot be attacked)"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Approved by</span>
              <span className="font-mono text-xs">{target.approved_by ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Registered</span>
              <span className="text-xs">{formatDate(target.created_at)}</span>
            </div>
            {target.approval_note ? (
              <div>
                <p className="mb-1 text-muted-foreground">Approval note</p>
                <p className="rounded border bg-muted/40 p-2 text-xs">{target.approval_note}</p>
              </div>
            ) : null}
            <p className="pt-2 text-xs text-muted-foreground">
              Changing allow-list status requires the operator role and writes an audit record. All interaction is
              additionally rate-limited, budgeted, and circuit-broken at the interaction layer.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent runs against this target</CardTitle>
        </CardHeader>
        <CardContent>
          {targetRuns.length === 0 ? (
            <p className="text-sm text-muted-foreground">No runs yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Findings</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Started</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {targetRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>
                      <Link href={`/runs/${run.id}`} className="font-mono text-xs hover:underline">
                        {run.id.slice(0, 8)}
                      </Link>
                    </TableCell>
                    <TableCell><RunStatusIndicator status={run.status} /></TableCell>
                    <TableCell>{run.findings_count}</TableCell>
                    <TableCell>{run.dry_run ? <Badge variant="secondary">dry-run</Badge> : <Badge>live</Badge>}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(run.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
