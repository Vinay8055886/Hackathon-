"use client";

import Link from "next/link";
import { Plus } from "lucide-react";
import { useTargets } from "@/lib/hooks/use-targets";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

  const targets = data ?? [];

  // Backend-driven target statistics
  const totalTargets = targets.length;

  const allowlistedTargets = targets.filter(
    (target) => target.allowlisted,
  ).length;

  const blockedTargets = targets.filter(
    (target) => !target.allowlisted,
  ).length;

  const restTargets = targets.filter(
    (target) => target.connector_type === "rest",
  ).length;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Targets</h1>

          <p className="text-sm text-muted-foreground">
            Registered LLM systems under test. Nothing is attackable until it
            is allow-listed.
          </p>
        </div>

        <Button asChild>
          <Link href="/targets/new">
            <Plus className="h-4 w-4" />
            Register target
          </Link>
        </Button>
      </div>

      {/* Target security summary */}
      {!isLoading && !isError && totalTargets > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardContent className="p-5">
              <p className="text-sm text-muted-foreground">
                Total targets
              </p>

              <p className="mt-1 text-2xl font-semibold">
                {totalTargets}
              </p>

              <p className="mt-0.5 text-xs text-muted-foreground">
                registered LLM systems
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <p className="text-sm text-muted-foreground">
                Allow-listed
              </p>

              <p className="mt-1 text-2xl font-semibold text-emerald-500">
                {allowlistedTargets}
              </p>

              <p className="mt-0.5 text-xs text-muted-foreground">
                ready for security testing
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <p className="text-sm text-muted-foreground">
                Blocked
              </p>

              <p className="mt-1 text-2xl font-semibold">
                {blockedTargets}
              </p>

              <p className="mt-0.5 text-xs text-muted-foreground">
                protected from attack runs
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <p className="text-sm text-muted-foreground">
                REST targets
              </p>

              <p className="mt-1 text-2xl font-semibold">
                {restTargets}
              </p>

              <p className="mt-0.5 text-xs text-muted-foreground">
                REST API connectors
              </p>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {/* Registered targets */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Registered targets
          </CardTitle>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : isError ? (
            <p className="text-sm text-severity-critical">
              Failed to load targets.
            </p>
          ) : targets.length === 0 ? (
            <EmptyState
              title="No targets registered"
              description="Register your first LLM application. It will be created closed — an operator must allow-list it before any run."
              action={
                <Button asChild>
                  <Link href="/targets/new">
                    Register target
                  </Link>
                </Button>
              }
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
                {targets.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell>
                      <span className="font-medium">
                        {t.name}
                      </span>

                      {t.description ? (
                        <p className="max-w-[240px] truncate text-xs text-muted-foreground">
                          {t.description}
                        </p>
                      ) : null}
                    </TableCell>

                    <TableCell>
                      <Badge variant="secondary">
                        {CONNECTOR_LABEL[t.connector_type] ??
                          t.connector_type}
                      </Badge>
                    </TableCell>

                    <TableCell className="max-w-[260px] truncate font-mono text-xs">
                      {t.endpoint}
                    </TableCell>

                    <TableCell>
                      {t.allowlisted ? (
                        <Badge className="bg-emerald-500/15 text-emerald-500">
                          Ready for testing
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          Protected
                        </Badge>
                      )}
                    </TableCell>

                    <TableCell className="text-xs text-muted-foreground">
                      {t.approved_by ?? "—"}
                    </TableCell>

                    <TableCell className="text-xs text-muted-foreground">
                      {formatDate(t.created_at)}
                    </TableCell>

                    <TableCell className="text-right">
                      <Button
                        asChild
                        variant="ghost"
                        size="sm"
                      >
                        <Link href={`/targets/${t.id}`}>
                          view
                        </Link>
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