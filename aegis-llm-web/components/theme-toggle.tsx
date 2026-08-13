"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * next-themes leaves `resolvedTheme` undefined during SSR, which would make
 * the server render a different icon than the client (hydration mismatch).
 * Gate theme-dependent rendering on a mounted flag so server HTML and the
 * first client render always agree; dark-mode-first, so default to <Sun/>.
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const isLight = mounted && resolvedTheme === "light";
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(isLight ? "dark" : "light")}
      aria-label="Toggle theme"
    >
      {isLight ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
    </Button>
  );
}
