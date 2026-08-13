"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { api } from "@/lib/api";
import { userCreateSchema } from "@/lib/api/schemas";
import { qk } from "@/lib/hooks/query-keys";
import { useMe } from "@/lib/hooks/use-me";
import { RoleGate } from "@/components/role-gate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function RoleBadge({ role }: { role: string }) {
  return (
    <Badge variant={role === "admin" ? "default" : "secondary"} className="uppercase">
      {role}
    </Badge>
  );
}

export default function SettingsPage() {
  const { data: session } = useSession();
  const me = useMe();
  const healthz = useQuery({ queryKey: qk.healthz, queryFn: () => api.healthz() });
  const [slackEnabled, setSlackEnabled] = useState(false);

  // Mock user directory for the demo; real deployments query /auth/users.
  const users = useQuery({
    queryKey: ["users"],
    queryFn: async () => [
      { id: "u-admin", username: session?.user?.name ?? "admin", email: session?.user?.email ?? "admin@aegis.local", role: session?.user?.role ?? "admin" },
    ],
  });

  const role = (session?.user?.role ?? me.data?.role ?? "viewer") as string;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Account, roles, integrations, and platform status.</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current user</CardTitle>
            <CardDescription>Identity and role from /auth/me.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Username</span>
              <span className="font-medium">{me.data?.username ?? session?.user?.name ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Email</span>
              <span>{me.data?.email ?? session?.user?.email ?? "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Role</span>
              <RoleBadge role={role} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Integrations</CardTitle>
            <CardDescription>Chat alerts and CI/CD policy gates.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded border p-3">
              <div>
                <p className="text-sm font-medium">Slack alerts on critical findings</p>
                <p className="text-xs text-muted-foreground">Notify a channel when a critical/high finding is recorded.</p>
              </div>
              <Switch checked={slackEnabled} onCheckedChange={setSlackEnabled} />
            </div>
            <div className="flex items-center justify-between rounded border p-3">
              <div>
                <p className="text-sm font-medium">CI policy gate</p>
                <p className="text-xs text-muted-foreground">
                  POST /ci/gate blocks PRs when findings meet the severity threshold.
                </p>
              </div>
              <Badge variant="secondary">enabled</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">User management (RBAC)</CardTitle>
          <CardDescription>
            Roles: viewer (read-only) · operator (targets, runs) · admin (users, everything).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(users.data ?? []).map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.username}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{u.email}</TableCell>
                  <TableCell><RoleBadge role={u.role} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <RoleGate required="admin">
            <CreateUserForm />
          </RoleGate>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Platform status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">API</span>
            <Badge className={healthz.data?.status === "ok" ? "bg-emerald-500/15 text-emerald-500" : "bg-severity-critical/15 text-severity-critical"}>
              {healthz.data?.status ?? "unknown"}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Backend URL</span>
            <span className="font-mono text-xs">{process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Mode</span>
            <span>{process.env.NEXT_PUBLIC_API_MOCK === "true" ? "mock (no backend required)" : "live backend"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">SSO</span>
            <span>{process.env.OIDC_ISSUER ? "OIDC configured" : "credentials only"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Runner</span>
            <span className="font-mono text-xs">{healthz.data?.runner ?? "—"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Vector store</span>
            <span className="font-mono text-xs">{healthz.data?.vector_store ?? "—"}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function CreateUserForm() {
  const qc = useQueryClient();
  const [values, setValues] = useState({ username: "", email: "", password: "", role: "viewer" });
  const [message, setMessage] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    const parsed = userCreateSchema.safeParse(values);
    if (!parsed.success) {
      setMessage(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }
    try {
      await api.me(); // ensure session
      setMessage("User created (stub — wire to POST /auth/users in production).");
      qc.invalidateQueries({ queryKey: ["users"] });
    } catch {
      setMessage("Failed to reach the backend.");
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-2 rounded border p-3">
      <div className="space-y-1">
        <Label htmlFor="u">Username</Label>
        <Input id="u" value={values.username} onChange={(e) => setValues({ ...values, username: e.target.value })} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="e">Email</Label>
        <Input id="e" type="email" value={values.email} onChange={(e) => setValues({ ...values, email: e.target.value })} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="p">Password</Label>
        <Input id="p" type="password" value={values.password} onChange={(e) => setValues({ ...values, password: e.target.value })} />
      </div>
      <div className="space-y-1">
        <Label>Role</Label>
        <Select value={values.role} onValueChange={(role) => setValues({ ...values, role })}>
          <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="viewer">viewer</SelectItem>
            <SelectItem value="operator">operator</SelectItem>
            <SelectItem value="admin">admin</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button type="submit" size="sm">Create user</Button>
      {message ? <p className="w-full text-xs text-muted-foreground">{message}</p> : null}
    </form>
  );
}
