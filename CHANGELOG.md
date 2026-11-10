# Changelog

## 0.3.4 — 2026-11-10

- Made event indexing and service heartbeats idempotent under replay/restart races.
- Indexer now retries integrity conflicts without a 60-second stall.

## 0.3.3 — 2026-11-10

- Removed empty directories and fixed the frontend Docker build without a `public/` directory.
- Sanitized local paths and placeholder keys in documentation.
- Clarified early web evidence versus the current FastAPI hosted path.

## 0.3.2 — 2026-11-10

- Removed the legacy Flask API and static demo console.
- Consolidated API, deployment, and architecture documentation on FastAPI + Next.js.
- Removed local-only transaction-map fallback and stale placeholder files.
- Added readiness, Prometheus metrics, worker/indexer heartbeats, and backup scripts.

## 0.3.1 — 2026-11-10

- Added database readiness checks and PostgreSQL indexes.
- Added guarded PostgreSQL backup/restore scripts.
- Added Prometheus metrics and worker/indexer heartbeats.
- Added worker/indexer stale-service alerts.

## 0.3.0 — 2026-11-10

- Added the Next.js product app: landing, agent console, datasets, queries,
  proof explorer, owner earnings, agent workspace, pricing, security, status,
  and docs.
- Added the FastAPI service with Postgres history, Redis-backed limits,
  idempotency, an async query worker, refund reconciler, and polling indexer.
- Added incremental Neardata NEP-297 event indexing.
- Added Docker Compose deployment with Next.js, FastAPI, worker, indexer,
  Postgres, Redis, and Caddy.
- Added the Render + Neon + Upstash hosted mirror and static-asset fix.
- Added MCP tooling and an end-to-end demo flow script.

## 0.2.0 — 2026-11-09

- Added the v2 multi-tenant contract: multiple owners/datasets, dataset rotation,
  pause, per-dataset budgets, protocol fees, and query history.
- Added reproducible v2 build and hosted/Compose evidence.

## 0.1.0 — 2026-11-09

- First NEAR testnet proof: private dataset in OutLayer storage, approved TDX
  computation, escrow/settlement contract, agent verification, refunds, and
  negative-path evidence.
