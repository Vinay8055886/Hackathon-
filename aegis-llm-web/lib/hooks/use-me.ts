"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { qk } from "@/lib/hooks/query-keys";

export function useMe() {
  return useQuery({
    queryKey: qk.me,
    queryFn: () => api.me(),
    // role/identity is already mirrored from the session by <SessionSync>;
    // this is a refresh for the settings page.
    staleTime: 60_000,
  });
}
