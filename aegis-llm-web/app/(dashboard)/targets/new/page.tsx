"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useCreateTarget } from "@/lib/hooks/use-targets";
import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().default(""),
  connector_type: z.enum(["rest", "browser", "websocket"]),
  endpoint: z.string().url("Must be an absolute http(s)/ws(s) URL"),
  response_path: z.string().optional(),
  rate_limit_per_minute: z.coerce.number().int().positive().optional(),
  max_tokens_per_run: z.coerce.number().int().positive().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export default function NewTargetPage() {
  const router = useRouter();
  const createTarget = useCreateTarget();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { connector_type: "rest", response_path: "" },
  });
  const connectorType = watch("connector_type");

  const onSubmit = async (values: FormValues) => {
    setError(null);
    try {
      const config: Record<string, unknown> = {};
      if (values.response_path) config.response_path = values.response_path;
      const target = await createTarget.mutateAsync({
        name: values.name,
        description: values.description,
        connector_type: values.connector_type,
        endpoint: values.endpoint,
        config,
        rate_limit_per_minute: values.rate_limit_per_minute,
        max_tokens_per_run: values.max_tokens_per_run,
      });
      router.push(`/targets/${target.id}`);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <Link href="/targets" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Targets
      </Link>
      <div>
        <h1 className="text-xl font-semibold">Register a target</h1>
        <p className="text-sm text-muted-foreground">
          Targets are created <b>closed</b>. An operator must allow-list the target before any run can touch it.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Connector configuration</CardTitle>
          <CardDescription>How Aegis-LLM should reach this system under test.</CardDescription>
        </CardHeader>
        <CardContent>
          <RoleGate required="operator" fallback={<p className="text-sm text-severity-critical">Operator role required to register targets.</p>}>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" placeholder="acme-chat" {...register("name")} />
                  {errors.name ? <p className="text-xs text-severity-critical">{errors.name.message}</p> : null}
                </div>
                <div className="space-y-1.5">
                  <Label>Connector type</Label>
                  <Select value={connectorType} onValueChange={(v) => setValue("connector_type", v as FormValues["connector_type"])}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rest">REST API</SelectItem>
                      <SelectItem value="browser">Browser (Playwright)</SelectItem>
                      <SelectItem value="websocket">WebSocket chat</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="endpoint">Endpoint URL</Label>
                <Input id="endpoint" placeholder="https://chat.acme.internal/v1/chat" {...register("endpoint")} />
                {errors.endpoint ? <p className="text-xs text-severity-critical">{errors.endpoint.message}</p> : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="description">Description</Label>
                <Textarea id="description" rows={2} placeholder="What is this system and who owns it?" {...register("description")} />
              </div>
              {connectorType === "rest" ? (
                <div className="space-y-1.5">
                  <Label htmlFor="response_path">Response path (JSON)</Label>
                  <Input id="response_path" placeholder="reply or choices.0.message.content" {...register("response_path")} />
                  <p className="text-xs text-muted-foreground">Dotted path into the response JSON to extract the assistant reply.</p>
                </div>
              ) : null}
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="rate_limit">Rate limit (per minute)</Label>
                  <Input id="rate_limit" type="number" placeholder="60" {...register("rate_limit_per_minute")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="max_tokens">Max tokens per run</Label>
                  <Input id="max_tokens" type="number" placeholder="200000" {...register("max_tokens_per_run")} />
                </div>
              </div>
              {error ? <p className="text-sm text-severity-critical">{error}</p> : null}
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => router.push("/targets")}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Registering…" : "Register target"}
                </Button>
              </div>
            </form>
          </RoleGate>
        </CardContent>
      </Card>
    </div>
  );
}
