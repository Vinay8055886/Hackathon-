# Aegis-LLM web — run doc

This thread serves the **Next.js operator console** in `aegis-llm-web/` (the
Aegis-LLM frontend). It runs in **mock mode** (`NEXT_PUBLIC_API_MOCK=true`) so
no backend is required — all data is served from an in-memory dataset with a
simulated live stream, and any credentials sign in as `admin`.

## Reproducing the uncommitted artifacts (fresh checkout)

1. **Install dependencies** (project's package manager is npm):

   ```bash
   cd aegis-llm-web
   npm install
   ```

2. **Create `.env.local`** in `aegis-llm-web/` (copied from the committed
   `.env.example`, adapted for local preview). This file is gitignored and
   must be recreated per checkout — it contains no secrets, only dev values:

   ```
   NEXT_PUBLIC_API_MOCK=true
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_MOCK_ROLE=admin
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=dev-only-aegis-secret-change-me
   ```

   Procedure: `copy .env.example .env.local`, then set the values above.
   (To point at a live backend instead: `NEXT_PUBLIC_API_MOCK=false`.)

## Running the server

- Default port: **3000** (Next.js default; free on this machine).
- Dev server:

  ```bash
  cd aegis-llm-web
  npm run dev
  ```

- URL: http://localhost:3000 — unauthenticated traffic is redirected to
  `/login` by `middleware.ts`; in mock mode sign in with any credentials.

### Detached start (Windows)

```powershell
powershell -NoProfile -Command "(Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','dev' -WorkingDirectory 'C:\Users\ramch\Downloads\hackrhon_cognizent\aegis-llm-web' -RedirectStandardOutput 'C:\Users\ramch\Downloads\hackrhon_cognizent\.freebuff\preview-5bf7504a-29ae-43d5-a4ba-55617704ebc4.log' -RedirectStandardError 'C:\Users\ramch\Downloads\hackrhon_cognizent\.freebuff\preview-5bf7504a-29ae-43d5-a4ba-55617704ebc4.log.err' -WindowStyle Hidden -PassThru).Id"
```

Note: `-WorkingDirectory` is required because `npm run dev` must run from
`aegis-llm-web/` (where `package.json` lives). stdout and stderr go to
separate files, per the Start-Process requirement.

**Port pitfall:** this environment exports `PORT=0`, which makes `next dev`
bind a *random* port instead of 3000. Pin the port explicitly when starting:

```powershell
# prepend the env var inside the ArgumentList, e.g.:
#   -ArgumentList 'run','dev','--port','3000'
```

or set `PORT=3000` for the process before launching. Then confirm the URL
answers on 3000 before registering the preview.
