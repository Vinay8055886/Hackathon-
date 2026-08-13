"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AllowlistRequest, TargetCreate } from "@/lib/api/schemas";
import { qk } from "@/lib/hooks/query-keys";

export function useTargets(allowlisted?: boolean) {
  return useQuery({
    queryKey: qk.targets(allowlisted),
    queryFn: () => api.listTargets(allowlisted),
  });
}

export function useTarget(id: string | undefined) {
  return useQuery({
    queryKey: qk.target(id ?? ""),
    queryFn: () => api.getTarget(id as string),
    enabled: !!id,
  });
}

export function useCreateTarget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TargetCreate) => api.createTarget(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.targets() }),
  });
}

export function useAllowlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AllowlistRequest }) =>
      api.setAllowlist(id, body),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: qk.targets() });
      qc.invalidateQueries({ queryKey: qk.target(vars.id) });
    },
  });
}
