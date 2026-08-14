import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { Role } from "@/lib/store/use-ui-store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const IS_MOCK = process.env.NEXT_PUBLIC_API_MOCK === "true";

/**
 * NextAuth config.
 *
 * Local dev (and preview): a Credentials provider that authenticates against
 * the FastAPI backend's `POST /auth/login` and stores the returned JWT in the
 * session so the API client can attach `Authorization: Bearer <token>`.
 * In mock mode (NEXT_PUBLIC_API_MOCK=true) any credentials sign in as the
 * configured mock role (default: admin) — no backend required.
 *
 * Enterprise SSO (Okta / Azure AD / Google Workspace): set OIDC_ISSUER,
 * OIDC_CLIENT_ID, OIDC_CLIENT_SECRET and the OidcProvider below activates
 * (auth via the backend's /auth/oidc/login + callback).
 */
export const authOptions: NextAuthOptions = {
  session: { strategy: "jwt", maxAge: 60 * 60 * 8 },
  pages: { signIn: "/login" },
  providers: [
    CredentialsProvider({
      id: "aegis-credentials",
      name: "Aegis-LLM",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const username = credentials?.username ?? "";
        const password = credentials?.password ?? "";
        if (!username || !password) return null;

        if (IS_MOCK) {
          const role = (process.env.NEXT_PUBLIC_MOCK_ROLE || "admin") as Role;
          return {
            id: "mock-user",
            name: username,
            email: `${username}@aegis.local`,
            role,
            accessToken: "mock-token",
          };
        }

        try {
          const login = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
          });
          if (!login.ok) {
            console.error("Login failed:", login.status, await login.text().catch(() => ""));
            return null;
          }
          const { access_token: accessToken } = await login.json();

          const me = await fetch(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${accessToken}` },
          });
          if (!me.ok) {
            console.error("Auth /me failed:", me.status, await me.text().catch(() => ""));
            return null;
          }
          const profile = await me.json();
          return {
            id: profile.id,
            name: profile.username,
            email: profile.email,
            role: profile.role as Role,
            accessToken,
          };
        } catch (err) {
          console.error("Authorize connection error to backend:", err);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
        token.role = user.role;
        token.name = user.name;
        token.email = user.email;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      if (session.user) {
        session.user.role = token.role;
        session.user.name = token.name ?? session.user.name;
        session.user.email = token.email ?? session.user.email;
      }
      return session;
    },
  },
};
