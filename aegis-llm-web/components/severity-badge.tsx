import { cn } from "@/lib/utils";
import { Severity } from "@/lib/api/schemas";

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "bg-severity-critical/15 text-severity-critical border-severity-critical/40",
  high: "bg-severity-high/15 text-severity-high border-severity-high/40",
  medium: "bg-severity-medium/15 text-severity-medium border-severity-medium/40",
  low: "bg-severity-low/15 text-severity-low border-severity-low/40",
};

export function SeverityBadge({
  severity,
  className,
}: {
  severity: Severity | string;
  className?: string;
}) {
  const s = (severity as Severity) in SEVERITY_STYLES ? (severity as Severity) : "info";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide",
        s === "info" ? "border-border bg-muted text-muted-foreground" : SEVERITY_STYLES[s],
        className,
      )}
      data-testid={`severity-${severity}`}
    >
      {severity}
    </span>
  );
}
