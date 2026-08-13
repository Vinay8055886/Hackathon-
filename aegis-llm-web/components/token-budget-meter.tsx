import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

export function TokenBudgetMeter({
  tokensUsed,
  tokenBudget,
  costUsd,
  className,
}: {
  tokensUsed: number;
  tokenBudget: number;
  costUsd: number;
  className?: string;
}) {
  const pct = tokenBudget > 0 ? Math.min(100, Math.round((tokensUsed / tokenBudget) * 100)) : 0;
  const over = tokensUsed >= tokenBudget;
  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-medium">Token budget</span>
        <span className="font-mono text-xs text-muted-foreground">
          {tokensUsed.toLocaleString()} / {tokenBudget.toLocaleString()} tokens · $
          {costUsd.toFixed(4)}
        </span>
      </div>
      <Progress
        value={pct}
        indicatorClassName={cn(over ? "bg-severity-critical" : pct > 75 ? "bg-severity-medium" : "")}
        aria-label={`${pct}% of token budget consumed`}
      />
    </div>
  );
}
