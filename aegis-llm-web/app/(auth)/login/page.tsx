"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const mockMode = process.env.NEXT_PUBLIC_API_MOCK === "true";

  useEffect(() => {
    if (params.get("error")) setError("Sign-in failed — check your credentials.");
  }, [params]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await signIn("aegis-credentials", {
      username,
      password,
      redirect: false,
    });
    setLoading(false);
    if (res?.error) {
      setError("Invalid username or password.");
    } else {
      router.push(params.get("callbackUrl") ?? "/");
      router.refresh();
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <ShieldCheck className="h-10 w-10 text-severity-low" />
          <h1 className="text-xl font-semibold">Aegis-LLM</h1>
          <p className="text-sm text-muted-foreground">LLM red-teaming operator console</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Sign in</CardTitle>
            <CardDescription>
              {mockMode
                ? "Mock mode — any credentials work, signed in as admin."
                : "Use your platform credentials or company SSO."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={submit} className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="username">Username</Label>
                <Input id="username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
              {error ? <p className="text-sm text-severity-critical">{error}</p> : null}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Signing in…" : mockMode ? "Sign in (mock admin)" : "Sign in"}
              </Button>
            </form>
            {process.env.OIDC_ISSUER ? (
              <div className="relative py-1 text-center text-xs text-muted-foreground">
                <span>or</span>
              </div>
            ) : null}
            {process.env.OIDC_ISSUER ? (
              <Button variant="outline" className="w-full" onClick={() => signIn("oidc")}>
                Continue with company SSO
              </Button>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
