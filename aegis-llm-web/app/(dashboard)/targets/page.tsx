"use client";

import Link from "next/link";
import { Plus } from "lucide-react";
import { useTargets } from "@/lib/hooks/use-targets";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/empty-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const CONNECTOR_LABEL: Record<string, string> = {
  rest: "REST",
  browser: "Browser",
  websocket: "WebSocket",
};

export default function TargetsPage() {
  const { data, isLoading, isError } = useTargets();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Targets</h1>
          <p className="text-sm text-muted-foreground">
            Registered LLM systems under test. Nothing is attackable until it is allow-listed.
          </p>
        </div>
        <Button asChild>
          <Link href="/targets/new">
            <Plus className="h-4 w-4" /> Register target
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Registered targets</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : isError ? (
            <p className="text-sm text-severity-critical">Failed to load targets.</p>
          ) : (data ?? []).length === 0 ? (
            <EmptyState
              title="No targets registered"
              description="Register your first LLM application. It will be created closed — an operator must allow-list it before any run."
              action={<Button asChild><Link href="/targets/new">Register target</Link></Button>}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Target</TableHead>
                  <TableHead>Connector</TableHead>
                  <TableHead>Endpoint</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Approved by</TableHead>
                  <TableHead>Registered</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data ?? []).map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>
                      <span className="font-medium">{t.name}</span>
                      {t.description ? <p className="max-w-[240px] truncate text-xs text-muted-foreground">{t.description}</p> : null}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{CONNECTOR_LABEL[t.connector_type] ?? t.connector_type}</Badge>
                    </TableCell>
                    <TableCell className="max-w-[260px] truncate font-mono text-xs">{t.endpoint}</TableCell>
                    <TableCell>
                      {t.allowlisted ? (
                        <Badge className="bg-emerald-500/15 text-emerald-500">Allow-listed</Badge>
                      ) : (
                        <Badge variant="secondary">Blocked</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{t.approved_by ?? "—"}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(t.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <Button asChild variant="ghost" size="sm">
                        <Link href={`/targets/${t.id}`}>view</Link>
                      </Button>
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
