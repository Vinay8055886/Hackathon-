"use client";

import { useFindings } from "@/lib/hooks/use-findings";
import { FindingsTable } from "@/components/findings-table";
import { Skeleton } from "@/components/ui/skeleton";

export default function FindingsPage() {
  const { data, isLoading, isError } = useFindings();

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Findings</h1>
        <p className="text-sm text-muted-foreground">
          Confirmed and suspected vulnerabilities across all runs. Evidence is served redacted.
        </p>
      </div>
      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      ) : isError ? (
        <p className="text-severity-critical">Failed to load findings.</p>
      ) : (
        <FindingsTable findings={data ?? []} />
      )}
    </div>
  );
}
