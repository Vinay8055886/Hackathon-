"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ShieldAlert } from "lucide-react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useCreateRun } from "@/lib/hooks/use-runs";
import { useTargets } from "@/lib/hooks/use-targets";
import { usePayloadPacks } from "@/lib/hooks/use-payload-packs";
import { runCreateSchema } from "@/lib/api/schemas";
import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type FormValues = {
  target_id: string;
  payload_pack_ids: string[];
  dry_run: boolean;
  max_turns?: number;
  token_budget?: number;
};

export default function NewRunPage() {
  return (
    <Suspense fallback={null}>
      <NewRunForm />
    </Suspense>
  );
}

function NewRunForm() {
  const router = useRouter();
  const params = useSearchParams();
  const targets = useTargets(true); // only allow-listed targets are runnable
  const packs = usePayloadPacks();
  const createRun = useCreateRun();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(runCreateSchema),
    defaultValues: {
      target_id: params.get("target") ?? "",
      payload_pack_ids: [],
      dry_run: true, // safe by default — live runs must be explicitly enabled
    },
  });

  const dryRun = watch("dry_run");
  const selectedPacks = watch("payload_pack_ids");

  const togglePack = (id: string) => {
    const next = selectedPacks.includes(id) ? selectedPacks.filter((p) => p !== id) : [...selectedPacks, id];
    setValue("payload_pack_ids", next, { shouldValidate: true });
  };

  const onSubmit = async (values: FormValues) => {
    setError(null);
    try {
      const run = await createRun.mutateAsync({
        target_id: values.target_id,
        payload_pack_ids: values.payload_pack_ids,
        run_origin: "real",
        dry_run: values.dry_run,
        max_turns: values.max_turns || undefined,
        token_budget: values.token_budget || undefined,
      });
      router.push(`/runs/${run.id}`);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <Link href="/runs" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Runs
      </Link>
      <div>
        <h1 className="text-xl font-semibold">Launch a run</h1>
        <p className="text-sm text-muted-foreground">
          Runs default to <b>dry-run</b> — the full pipeline executes without touching the target.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Run configuration</CardTitle>
          <CardDescription>Target, payload packs, and safety budgets.</CardDescription>
        </CardHeader>
        <CardContent>
          <RoleGate required="operator" fallback={<p className="text-sm text-severity-critical">Operator role required to launch runs.</p>}>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <Label>Target (allow-listed only)</Label>
                <Select value={watch("target_id")} onValueChange={(v) => setValue("target_id", v, { shouldValidate: true })}>
                  <SelectTrigger><SelectValue placeholder="Select a target" /></SelectTrigger>
                  <SelectContent>
                    {(targets.data ?? []).map((t) => (
                      <SelectItem key={t.id} value={t.id}>
                        {t.name} · {t.connector_type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.target_id ? <p className="text-xs text-severity-critical">{errors.target_id.message}</p> : null}
                {(targets.data ?? []).length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    No allow-listed targets. <Link href="/targets/new" className="underline">Register one</Link>, then allow-list it.
                  </p>
                ) : null}
              </div>

              <div className="space-y-2">
                <Label>Payload packs</Label>
                <div className="grid gap-2 sm:grid-cols-2">
                  {(packs.data ?? []).map((pack) => (
                    <label
                      key={pack.id}
                      className="flex cursor-pointer items-start gap-2 rounded border p-3 text-sm hover:bg-muted/40 data-[selected=true]:border-primary"
                      data-selected={selectedPacks.includes(pack.id)}
                    >
                      <input
                        type="checkbox"
                        className="mt-0.5"
                        checked={selectedPacks.includes(pack.id)}
                        onChange={() => togglePack(pack.id)}
                      />
                      <span>
                        <span className="font-mono">{pack.name}</span>
                        <span className="block text-xs text-muted-foreground">
                          {pack.payload_count} payloads · {pack.owasp_categories.join(", ")}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
                {errors.payload_pack_ids ? <p className="text-xs text-severity-critical">{errors.payload_pack_ids.message}</p> : null}
              </div>

              <div className="flex items-center justify-between rounded border p-3">
                <div>
                  <Label htmlFor="dry-run">Dry-run mode</Label>
                  <p className="text-xs text-muted-foreground">
                    Execute the full pipeline with a simulated responder — no traffic reaches the target.
                  </p>
                </div>
                <Switch id="dry-run" checked={dryRun} onCheckedChange={(v) => setValue("dry_run", v)} />
              </div>
              {!dryRun ? (
                <div className="flex items-start gap-2 rounded border border-severity-medium/40 bg-severity-medium/10 p-3 text-sm text-severity-medium">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>
                    This will send live attack traffic to the selected target. Only proceed for systems you own or are
                    explicitly authorized to test. Every request is rate-limited, budgeted, circuit-broken, and audit-logged.
                  </span>
                </div>
              ) : null}

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="max_turns">Max turns</Label>
                  <Input id="max_turns" type="number" placeholder="10" {...register("max_turns", { valueAsNumber: true })} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="token_budget">Token budget</Label>
                  <Input id="token_budget" type="number" placeholder="200000" {...register("token_budget", { valueAsNumber: true })} />
                </div>
              </div>

              {error ? <p className="text-sm text-severity-critical">{error}</p> : null}
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => router.push("/runs")}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting} variant={dryRun ? "default" : "destructive"}>
                  {isSubmitting ? "Launching…" : dryRun ? "Launch dry-run" : "Launch live run"}
                </Button>
              </div>
            </form>
          </RoleGate>
        </CardContent>
      </Card>
    </div>
  );
}
