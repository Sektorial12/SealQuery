# SealQuery web

Next.js product app for the SealQuery testnet prototype.

## Run

The FastAPI service must be running on `http://127.0.0.1:8000` (see the root README).

```bash
pnpm install
API_URL=http://127.0.0.1:8000 pnpm dev
```

Open `http://127.0.0.1:3000`.

The Next.js server proxies `/api/*` to `API_URL`, so the browser never talks to
a different origin and no CORS configuration is needed.

## Routes

- `/` — landing, live network stats, latest proof
- `/app` — agent console, datasets, query timeline, result, TDX proof
- `/app/datasets` and `/app/datasets/:id` — dataset inventory and detail
- `/app/queries` and `/app/queries/:id` — durable query history and proof view
- `/app/proofs` — proof explorer
- `/app/owner` — owner console
- `/app/agent` — agent usage, API and MCP reference
- `/pricing`, `/security`, `/status`, `/docs` — public product surfaces

## Checks

```bash
pnpm lint
pnpm build
```

The canonical deployment is `compose.yaml` at the repository root.
