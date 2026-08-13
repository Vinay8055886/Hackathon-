"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { qk } from "@/lib/hooks/query-keys";

export interface FindingFilters {
  severity?: string;
  runId?: string;
  category?: string;
  owaspCategory?: string;
}

export function useFindings(filters?: FindingFilters) {
  return useQuery({
    queryKey: qk.findings(filters as Record<string, string | undefined>),
    queryFn: () => api.listFindings(filters),
  });
}

export function useFinding(id: string | undefined) {
  return useQuery({
    queryKey: qk.finding(id ?? ""),
    queryFn: () => api.getFinding(id as string),
    enabled: !!id,
  });
}
