"use client";

import { useEffect, useState, type ReactNode } from "react";
import { SessionProvider, useSession } from "next-auth/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useUiStore } from "@/lib/store/use-ui-store";

/** Mirrors the NextAuth session into the UI store so the plain API client can
 * attach the bearer token without every hook reading useSession(). */
function SessionSync() {
  const { data: session } = useSession();
  const setAuth = useUiStore((s) => s.setAuth);
  useEffect(() => {
    const user = session?.user
      ? {
          id: session.user.id ?? "local",
          name: session.user.name ?? undefined,
          email: session.user.email ?? undefined,
          role: (session.user.role as "viewer" | "operator" | "admin") ?? "viewer",
        }
      : null;
    setAuth(session?.accessToken ?? null, user);
  }, [session, setAuth]);
  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 15_000,
          },
        },
      }),
  );

  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          <SessionSync />
          {children}
        </ThemeProvider>
      </QueryClientProvider>
    </SessionProvider>
  );
}
