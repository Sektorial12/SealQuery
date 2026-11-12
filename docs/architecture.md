# Architecture

SealQuery sells an approved computation over a private dataset and returns only
the aggregate plus a TDX attestation.

Current deployment: contract `0.2.3` on NEAR testnet, API `0.6.2`, one live
dataset (`retail_v1`) and one approved computation (`spend_growth_v1`).

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

1. The contract owner onboards a dataset owner and the owner registers an
   approved computation. The browser/agent submits a dataset/computation request.
2. FastAPI writes a queued job and returns `202` with a `job_id`.
3. Worker claims the job, asks the contract for a quote, and pays the query price.
4. Contract requests OutLayer execution and later receives the callback.
5. Worker waits for the result, runs `outlayer-verify`, and accepts, refunds, or
   leaves a ready result for timeout settlement to the owner.
6. Query history and owner earnings are persisted in Postgres.
7. Indexer syncs contract views and event logs for history/tx mapping.

## Trust boundaries

- Browser/API keys: the browser never holds a NEAR key; machine clients use
  `X-API-Key` for `/api/v1/*`.
- Agent key: only the worker holds the server-side access-key file/keychain.
- Contract: registry, escrow, budgets, acceptance, refunds, and timeout
  settlement.
- OutLayer: TDX execution and attestation; governance is external/trusted.
- Verifier: `outlayer-verify` checks Intel collateral, measurements, and I/O
  binding; proof bundles verify offline.
- Postgres/Redis: operational state, not the source of truth for settlement.

## Deployment surfaces

- `compose.yaml`: canonical self-host stack.
- `render.yaml`: managed public testnet mirror using Neon and Upstash.
- `backend/`: FastAPI, worker, indexer, models.
- `frontend/`: Next.js product app.

## Known limits

- TEE proves execution, not semantic correctness.
- No differential privacy; budget/cohort/rounding are the current controls.
- Ready results are public on-chain and through the API; raw rows are not.
- A ready query cannot be refunded; timeout settlement pays the owner and is not
  proof-gated on-chain.
- The verifier checks the worker measurement/task binding but not an independently
  registered application wasm hash.
- Public Neardata is limited to about 30 blocks/minute, so event catch-up can lag.
- The browser query endpoint is dataset-allowlisted, key-free, globally and
  per-caller rate-limited, and disabled when the daily demo budget is exhausted.
- Unused OutLayer compute remains in the contract; there is no agent withdrawal path.
- Contract state has no migration path yet.
