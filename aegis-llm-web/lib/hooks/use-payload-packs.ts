"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { qk } from "@/lib/hooks/query-keys";

export function usePayloadPacks() {
  return useQuery({ queryKey: qk.packs, queryFn: () => api.listPayloadPacks() });
}

export function usePayloads(packId: string | undefined) {
  return useQuery({
    queryKey: qk.payloads(packId ?? ""),
    queryFn: () => api.listPayloads(packId as string),
    enabled: !!packId,
  });
}
