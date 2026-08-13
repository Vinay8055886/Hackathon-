"use client";

import { create } from "zustand";

export type Role = "viewer" | "operator" | "admin";

export interface SessionUser {
  id: string;
  name?: string;
  email?: string;
  role: Role;
}

interface UiState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  // Access token + user mirrored from the NextAuth session so the plain API
  // client can attach credentials without every hook reading useSession().
  token: string | null;
  user: SessionUser | null;
  setAuth: (token: string | null, user: SessionUser | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  token: null,
  user: null,
  setAuth: (token, user) => set({ token, user }),
}));

/** Minimum role required for safety-critical actions. */
export const ROLE_RANK: Record<Role, number> = {
  viewer: 0,
  operator: 1,
  admin: 2,
};

export function hasRole(actual: Role | undefined, required: Role): boolean {
  if (!actual) return false;
  return ROLE_RANK[actual] >= ROLE_RANK[required];
}
