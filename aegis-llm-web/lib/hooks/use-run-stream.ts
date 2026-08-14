"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { AgentEvent } from "@/lib/api/schemas";
import { API_BASE, IS_MOCK } from "@/lib/api/client";
import { useUiStore } from "@/lib/store/use-ui-store";
import { mockStream } from "@/lib/api/mock";
import { qk } from "@/lib/hooks/query-keys";

export type StreamStatus = "connecting" | "open" | "reconnecting" | "closed";

/**
 * Live run stream (SSE over fetch, since the backend requires an
 * Authorization header that plain EventSource cannot send).
 *
 * - Reconnects with exponential backoff (1s → 2s → … capped at 15s).
 * - Exposes typed events and a connection status for the UI.
 * - Merges status/finding events back into the TanStack Query cache so list
 *   and detail views stay consistent.
 */
export function useRunStream(runId: string | undefined) {
  const qc = useQueryClient();
  const [status, setStatus] = useState<StreamStatus>("closed");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const aborterRef = useRef<AbortController | null>(null);
  const stopRef = useRef(false);

  const handleEvent = useCallback(
    (event: AgentEvent) => {
      setEvents((prev) => {
        if (prev.some((e) => e.sequence === event.sequence)) return prev;
        return [...prev, event];
      });

      // ── merge into the query cache ──────────────────────────────────────
      if (!runId) return;
      if (event.event_type === "finding_recorded") {
        qc.invalidateQueries({ queryKey: qk.findings({ runId }) });
        qc.setQueryData(qk.run(runId), (old?: { findings_count?: number }) =>
          old ? { ...old, findings_count: (old.findings_count ?? 0) + 1 } : old,
        );
      }
      if (event.event_type === "target_response") {
        const tokens = Number(event.payload?.tokens ?? 0);
        if (tokens > 0) {
          qc.setQueryData(qk.run(runId), (old?: { tokens_used?: number }) =>
            old ? { ...old, tokens_used: (old.tokens_used ?? 0) + tokens } : old,
          );
        }
      }
      if (event.event_type === "run_finished" || event.event_type === "run_failed") {
        qc.setQueryData(qk.run(runId), (old?: { status?: string }) =>
          old
            ? {
                ...old,
                status:
                  event.event_type === "run_failed"
                    ? "failed"
                    : (event.payload?.status as string) ?? "completed",
                finished_at: new Date().toISOString(),
              }
            : old,
        );
        setStatus("closed");
      }
    },
    [qc, runId],
  );

  useEffect(() => {
    if (!runId) return;
    stopRef.current = false;
    setEvents([]);
    setStatus("connecting");

    if (IS_MOCK) {
      setStatus("open");
      const cancel = mockStream(runId, handleEvent);
      return () => {
        stopRef.current = true;
        cancel();
        setStatus("closed");
      };
    }

    let attempt = 0;
    let cancelled = false;

    const connect = async () => {
      if (cancelled || stopRef.current) return;
      setStatus(attempt === 0 ? "connecting" : "reconnecting");
      const controller = new AbortController();
      aborterRef.current = controller;
      const token = useUiStore.getState().token;

      try {
        const res = await fetch(`${API_BASE}/runs/${runId}/stream`, {
          headers: { Accept: "text/event-stream", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          signal: controller.signal,
        });
        if (!res.ok || !res.body) throw new Error(`stream ${res.status}`);
        setStatus("open");
        attempt = 0;

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const blocks = buffer.split("\n\n");
          buffer = blocks.pop() ?? "";
          for (const block of blocks) {
            for (const line of block.split("\n")) {
              if (!line.startsWith("data: ")) continue;
              try {
                const parsed = JSON.parse(line.slice(6));
                const eventType = parsed?.event_type || parsed?.event;
                if (eventType === "stream_end") {
                  setStatus("closed");
                  return;
                }
                if (parsed && typeof parsed === "object") {
                  handleEvent({
                    sequence: parsed.sequence ?? 0,
                    run_id: parsed.run_id ?? runId,
                    agent: parsed.agent ?? "orchestrator",
                    event_type: eventType ?? "event",
                    payload: parsed.payload ?? {},
                  });
                }
              } catch {
                /* skip malformed frames */
              }
            }
          }
        }
        // stream ended without stream_end (run finished server-side)
        setStatus("closed");
      } catch (err) {
        if (cancelled || stopRef.current || (err as Error).name === "AbortError") {
          return;
        }
        // Reconnect with backoff.
        attempt += 1;
        setReconnectAttempt(attempt);
        const backoff = Math.min(1000 * 2 ** (attempt - 1), 15_000);
        setTimeout(connect, backoff);
      }
    };

    connect();
    return () => {
      cancelled = true;
      stopRef.current = true;
      aborterRef.current?.abort();
      setStatus("closed");
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  return { status, events, reconnectAttempt };
}
