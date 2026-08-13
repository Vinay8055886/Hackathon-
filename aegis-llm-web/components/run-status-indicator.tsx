import { cn } from "@/lib/utils";
import { RunStatus } from "@/lib/api/schemas";

const STATUS_META: Record<RunStatus, { label: string; dot: string; pulse?: boolean }> = {
  scheduled: { label: "Queued", dot: "bg-muted-foreground" },
  running: { label: "Running", dot: "bg-severity-low", pulse: true },
  completed: { label: "Completed", dot: "bg-emerald-500" },
  failed: { label: "Failed", dot: "bg-severity-critical" },
  cancelled: { label: "Stopped", dot: "bg-muted-foreground" },
};

export function RunStatusIndicator({ status, className }: { status: RunStatus; className?: string }) {
  const meta = STATUS_META[status] ?? STATUS_META.scheduled;
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-sm", className)} data-testid="run-status">
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          meta.dot,
          meta.pulse && "animate-pulse-soft",
        )}
      />
      {meta.label}
    </span>
  );
}
