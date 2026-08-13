"use client";

import { ReactNode } from "react";
import { hasRole, useUiStore, type Role } from "@/lib/store/use-ui-store";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

/**
 * RoleGate — hides (or disables) actions based on the current user's role.
 * Safety-critical actions (allow-listing targets, launching live runs,
 * stopping runs) require operator+ and should pass a `disabled` variant to
 * show the reason instead of silently hiding the control.
 */
export function RoleGate({
  required,
  children,
  mode = "hide",
  fallback = null,
}: {
  required: Role;
  children: ReactNode;
  /** hide = render nothing; disable = render wrapped with a locked tooltip */
  mode?: "hide" | "disable";
  fallback?: ReactNode;
}) {
  const user = useUiStore((s) => s.user);
  const allowed = hasRole(user?.role, required);

  if (allowed) return <>{children}</>;
  if (mode === "hide") return <>{fallback}</>;

  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            data-testid="role-gate-locked"
            className="inline-flex cursor-not-allowed opacity-50"
            aria-disabled="true"
          >
            {children}
          </span>
        </TooltipTrigger>
        <TooltipContent>Requires the {required} role</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
