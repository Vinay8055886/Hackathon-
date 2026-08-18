"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { RunCreate } from "@/lib/api/schemas";
import { qk } from "@/lib/hooks/query-keys";

export function useRuns(status?: string, targetId?: string, runOrigin?: string) {
  return useQuery({
    queryKey: qk.runs(status),
    queryFn: () => api.listRuns(status, targetId, runOrigin),
  });
}

export function useRun(id: string | undefined) {
  return useQuery({
    queryKey: qk.run(id ?? ""),
    queryFn: () => api.getRun(id as string),
    enabled: !!id,
    refetchInterval: (query) => {
      const run = query.state.data;
      if (!run) return false;
      return run.status === "scheduled" || run.status === "running" ? 2000 : false;
    },
  });
}

export function useCreateRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RunCreate) => api.createRun(body),
    onSuccess: (run) => {
      qc.invalidateQueries({ queryKey: qk.runs() });
      qc.setQueryData(qk.run(run.id), run);
    },
  });
}

export function useCancelRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.cancelRun(id),
    onSuccess: (run) => {
      qc.setQueryData(qk.run(run.id), run);
      qc.invalidateQueries({ queryKey: qk.runs() });
    },
  });
}
