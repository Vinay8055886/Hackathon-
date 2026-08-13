"use client";

import { useState } from "react";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { useAllowlist } from "@/lib/hooks/use-targets";
import { useUiStore } from "@/lib/store/use-ui-store";
import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";

/**
 * Safety-critical control: allow-listing a target requires the operator role,
 * an explicit approver identity, and an audit note. Always gated by RoleGate.
 */
export function TargetAllowlistToggle({
  targetId,
  allowlisted,
  approvedBy,
  approvalNote,
}: {
  targetId: string;
  allowlisted: boolean;
  approvedBy?: string | null;
  approvalNote?: string;
}) {
  const user = useUiStore((s) => s.user);
  const allowlist = useAllowlist();
  const [note, setNote] = useState(approvalNote ?? "");
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setError(null);
    try {
      await allowlist.mutateAsync({
        id: targetId,
        body: {
          allowlisted: !allowlisted,
          approved_by: user?.name ?? user?.id ?? "unknown",
          approval_note: note,
        },
      });
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <RoleGate required="operator" mode="disable">
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant={allowlisted ? "outline" : "default"} data-testid="allowlist-toggle">
            {allowlisted ? <ShieldCheck className="h-4 w-4 text-emerald-500" /> : <ShieldAlert className="h-4 w-4" />}
            {allowlisted ? "De-list target" : "Allow-list target"}
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {allowlisted ? "De-list this target?" : "Allow-list this target?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {allowlisted
                ? "De-listing blocks all future interaction. Existing audit records are retained."
                : "Allow-listing permits the platform to send attack traffic to this target. Only do this for systems you own or are explicitly authorized to test. This action is recorded in the audit log."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          {!allowlisted ? (
            <div className="space-y-2">
              <Label htmlFor="approval-note">Approval note (audit trail)</Label>
              <Input
                id="approval-note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="e.g. Own staging target — approved by product security"
              />
            </div>
          ) : (
            <div className="space-y-1 text-sm text-muted-foreground">
              <p>
                Approved by: <Badge variant="secondary">{approvedBy ?? "—"}</Badge>
              </p>
              {approvalNote ? <p className="text-xs">{approvalNote}</p> : null}
            </div>
          )}
          {error ? <p className="text-sm text-severity-critical">{error}</p> : null}
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={submit}
              className={allowlisted ? "" : "bg-destructive text-destructive-foreground hover:bg-destructive/90"}
              disabled={!allowlisted && !note.trim()}
            >
              {allowlisted ? "De-list" : "Allow-list"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </RoleGate>
  );
}
