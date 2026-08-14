"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { FileText, Play } from "lucide-react";
import { useRuns } from "@/lib/hooks/use-runs";
import { useTargets } from "@/lib/hooks/use-targets";
import { formatDate } from "@/lib/utils";
import { RunStatusIndicator } from "@/components/run-status-indicator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/empty-state";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const STATUS_FILTERS = [
  { value: "all", label: "All statuses" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Stopped" },
];

export default function RunsPage() {
  const [status, setStatus] = useState("all");
  const [targetId, setTargetId] = useState("all");
  const runs = useRuns(status === "all" ? undefined : status, targetId === "all" ? undefined : targetId);
  const targets = useTargets();

  const targetName = useMemo(() => {
    const map = new Map((targets.data ?? []).map((t) => [t.id, t.name]));
    return (id: string) => map.get(id) ?? id.slice(0, 8);
  }, [targets.data]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Runs</h1>
          <p className="text-sm text-muted-foreground">Attack run history — every run is auditable and replayable.</p>
        </div>
        <Button asChild>
          <Link href="/runs/new">
            <Play className="h-4 w-4" /> New run
          </Link>
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
          <SelectContent>
            {STATUS_FILTERS.map((s) => (
              <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={targetId} onValueChange={setTargetId}>
          <SelectTrigger className="w-56"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All targets</SelectItem>
            {(targets.data ?? []).map((t) => (
              <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Run history</CardTitle>
        </CardHeader>
        <CardContent>
          {runs.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : (runs.data ?? []).length === 0 ? (
            <EmptyState
              title="No runs match the filters"
              action={<Button asChild><Link href="/runs/new">Launch a run</Link></Button>}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Target</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Findings</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Tokens</TableHead>
                  <TableHead>Cost</TableHead>
                  <TableHead>Started by</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {(runs.data ?? []).map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>
                      <Link href={`/targets/${run.target_id}`} className="font-medium hover:underline">
                        {targetName(run.target_id)}
                      </Link>
                    </TableCell>
                    <TableCell><RunStatusIndicator status={run.status} /></TableCell>
                    <TableCell className="font-mono text-xs">{run.findings_count}</TableCell>
                    <TableCell>
                      {run.dry_run ? <Badge variant="secondary">dry-run</Badge> : <Badge className="bg-severity-low/15 text-severity-low">live</Badge>}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{run.tokens_used.toLocaleString()}</TableCell>
                    <TableCell className="font-mono text-xs">${run.cost_estimate_usd.toFixed(4)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{run.started_by}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(run.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button asChild variant="ghost" size="sm">
                          <Link href={`/runs/${run.id}`}>open</Link>
                        </Button>
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/reports/${run.id}`}>
                            <FileText className="mr-1 h-3.5 w-3.5" /> report
                          </Link>
                        </Button>
                      </div>
                    </TableCell>
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
