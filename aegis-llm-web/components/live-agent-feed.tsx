"use client";

import { useEffect, useRef } from "react";
import {
  Activity,
  Crosshair,
  FlaskConical,
  MemoryStick,
  RefreshCw,
  Swords,
  TerminalSquare,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { AgentEvent } from "@/lib/api/schemas";
import { StreamStatus } from "@/lib/hooks/use-run-stream";

const AGENT_META: Record<
  string,
  {
    label: string;
    icon: typeof Swords;
    color: string;
  }
> = {
  attacker: {
    label: "Attacker",
    icon: Swords,
    color: "text-severity-low",
  },
  interaction: {
    label: "Target",
    icon: TerminalSquare,
    color: "text-muted-foreground",
  },
  judge: {
    label: "Judge",
    icon: Crosshair,
    color: "text-severity-medium",
  },
  refiner: {
    label: "Refiner",
    icon: RefreshCw,
    color: "text-severity-info",
  },
  memory: {
    label: "Memory",
    icon: MemoryStick,
    color: "text-emerald-500",
  },
  orchestrator: {
    label: "Orchestrator",
    icon: Activity,
    color: "text-foreground",
  },
};

function eventSummary(e: AgentEvent): string {
  const eventType = String(e?.event_type ?? "unknown_event");
  const payload = e?.payload ?? {};

  const p = payload as Record<string, unknown>;

  switch (eventType) {
    case "payload_selected":
      return `Selected payload ${String(p.slug ?? "?")}${
        p.risk ? ` (risk: ${String(p.risk)})` : ""
      }`;

    case "target_response":
      return `HTTP ${String(p.status_code ?? "?")} · ${String(
        p.tokens ?? 0
      )} tokens · ${String(p.duration_ms ?? 0)}ms`;

    case "verdict": {
      const success = Boolean(p.success);

      if (success) {
        const confidence = Number(p.confidence ?? 0);

        return `Attack confirmed — severity ${String(
          p.severity ?? "?"
        )}, confidence ${Math.round(confidence * 100)}%`;
      }

      return "No detector confirmed an attack";
    }

    case "mutation":
      return `Mutated payload with strategy "${String(
        p.strategy ?? "unknown"
      )}"`;

    case "finding_recorded":
      return `Finding recorded: ${String(
        p.category ?? "unknown"
      )} [${String(p.severity ?? "unknown")}]`;

    case "run_started":
      return `Run started (max ${String(p.max_turns ?? "?")} turns)`;

    case "run_finished":
      return `Run finished — ${String(p.status ?? "unknown")}, ${String(
        p.findings ?? 0
      )} findings`;

    case "run_failed":
    case "safety_blocked":
      return String(
        p.message ??
          p.error ??
          eventType
      );

    default:
      return eventType.replace(/_/g, " ");
  }
}

export function LiveAgentFeed({
  events,
  streamStatus,
  reconnectAttempt,
}: {
  events: AgentEvent[];
  streamStatus: StreamStatus;
  reconnectAttempt: number;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [events.length]);

  return (
    <div className="flex h-[420px] flex-col overflow-hidden rounded-lg border">
      {/* Header */}
      <div className="flex items-center justify-between border-b bg-muted/30 px-3 py-2">
        <span className="text-sm font-medium">Agent activity</span>

        {streamStatus === "open" ? (
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-500">
            <span className="h-1.5 w-1.5 animate-pulse-soft rounded-full bg-emerald-500" />
            live
          </span>
        ) : streamStatus === "reconnecting" ||
          streamStatus === "connecting" ? (
          <span className="inline-flex items-center gap-1.5 text-xs text-severity-medium">
            <RefreshCw className="h-3 w-3 animate-spin" />

            {streamStatus === "reconnecting"
              ? `reconnecting… (attempt ${reconnectAttempt})`
              : "connecting…"}
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">
            stream closed
          </span>
        )}
      </div>

      {/* Events */}
      <div className="flex-1 space-y-0 overflow-y-auto p-3 font-mono text-[12px] leading-relaxed">
        {events.length === 0 ? (
          <p className="text-muted-foreground">
            Waiting for events…
          </p>
        ) : (
          events.map((e, i) => {
            /*
             * Defensive handling:
             * Backend/SSE events may occasionally contain missing
             * or non-string agent values.
             */
            const agent = String(e?.agent ?? "unknown");

            const meta = AGENT_META[agent] ?? {
              label: agent,
              icon: FlaskConical,
              color: "text-muted-foreground",
            };

            const Icon = meta.icon;

            return (
              <div
                key={`${String(e?.sequence ?? "event")}-${i}`}
                className="flex gap-2 border-b border-dashed py-1.5 last:border-0"
              >
                <span className="w-6 shrink-0 text-right text-muted-foreground/60">
                  {e?.sequence ?? "-"}
                </span>

                <Icon
                  className={cn(
                    "mt-0.5 h-3.5 w-3.5 shrink-0",
                    meta.color
                  )}
                />

                <span
                  className={cn(
                    "w-24 shrink-0",
                    meta.color
                  )}
                >
                  {meta.label}
                </span>

                <span className="text-foreground/90">
                  {eventSummary(e)}
                </span>
              </div>
            );
          })
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
