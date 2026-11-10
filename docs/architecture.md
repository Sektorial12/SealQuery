# Architecture

SealQuery sells an approved computation over a private dataset and returns only
the aggregate plus a TDX attestation.

## Components

```text
Agent / MCP / browser
        |
        v
Next.js app  ──HTTP──>  FastAPI  ──enqueue──>  Postgres job queue
        |                   |                       |
        |                   |                       v
        |                   |                 async worker
        |                   |                   /       \
        |                   |                  v         v
        |                   |              NEAR contract  OutLayer TDX
        |                   |                  |              |
        |                   |                  └── callback ──┘
        |                   |                       |
        |                   └────── Postgres <── worker verify/accept/refund
        |
        └── read state/jobs/proofs ──> FastAPI ──> contract views / Postgres

Indexer ──> NEAR RPC contract views + Neardata NEP-297 events ──> Postgres
```

## Request lifecycle

1. Agent submits a dataset/computation request.
2. FastAPI writes a queued job and returns `202` with a `job_id`.
3. Worker claims the job, asks the contract for a quote, and pays the query price.
4. Contract requests OutLayer execution and later receives the callback.
5. Worker waits for the result, runs `outlayer-verify`, and accepts or refunds.
6. Query history and owner earnings are persisted in Postgres.
7. Indexer syncs contract views and event logs for history/tx mapping.

## Trust boundaries

- Browser/API keys: the browser never holds a NEAR key; machine clients use
  `X-API-Key` for `/api/v1/*`.
- Agent key: server-side access-key file or NEAR keychain.
- Contract: registry, escrow, budgets, acceptance, refunds.
- OutLayer: TDX execution and attestation; governance is external/trusted.
- Verifier: `outlayer-verify` checks Intel collateral, measurements, and I/O
  binding; proof bundles verify offline.
- Postgres/Redis: operational state, not the source of truth for settlement.

## Deployment surfaces

- `compose.yaml`: canonical self-host stack.
- `render.yaml`: managed public testnet mirror using Neon and Upstash.
- `backend/`: FastAPI, worker, indexer, models.
- `frontend/`: Next.js product app.
- `api/` + `web/`: legacy Flask demo fallback.

## Known limits

- TEE proves execution, not semantic correctness.
- No differential privacy; budget/cohort/rounding are the current controls.
- Public Neardata rate limits make full historical event backfill optional.
- The public browser query endpoint spends the demo agent balance; gate it
  before publicizing.
