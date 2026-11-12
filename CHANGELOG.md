# Changelog

## Unreleased

- Added the SealQuery README banner, web header mark, and favicon.
- Refreshed README, architecture, operations, security, evidence, and MCP docs
  for the current contract/API and known limitations.
- Clarified onboarding, public aggregate results, timeout settlement, compute
  surplus, and verifier scope in the docs.

## 0.6.2 — 2026-11-11

- Retried near CLI submissions that fail with an expired transaction before
  broadcast (no transaction ID).

## 0.6.1 — 2026-11-11

- Retried transient attestation verification and acceptance calls.

## 0.6.0 — 2026-11-11

- Added `register_dataset_for` and `transfer_dataset_owner` for real owner onboarding.
- Made reconciliation recover a crashed job's query from on-chain history and apply
  the dataset binding check before acceptance.
- Added a global browser-query rate limit and trusted Cloudflare client identity.
- Fixed refund timeline labels, settlement labels, and documented upload input,
  deploy_init, agent funding, and local-vs-hosted load numbers.

## 0.5.7 — 2026-11-11

- Bound each aggregate to the registered dataset hash/version before acceptance.
- Removed the one-shot API event reset after the q37 backfill completed.

## 0.5.6 — 2026-11-11

- Reset the event checkpoint from the API startup hook so the indexer can
  backfill the q37 request/settlement links.

## 0.5.5 — 2026-11-11

- Reindexed recent contract events from the q37 backfill block and disabled
  fast-forward when an explicit start block is configured.

## 0.5.4 — 2026-11-11

- Fixed the missing event-indexer lag setting that stopped the indexer heartbeat.

## 0.5.3 — 2026-11-11

- Added proof-endpoint rate limiting, an indexer error heartbeat, sitemap output,
  and owner summaries filtered to configured datasets.
- Documented the agent gas reserve, public aggregates, invoice-based cohorts, and
  trapped compute surplus.

## 0.5.2 — 2026-11-11

- Made idempotency reservation atomic and rate-limit identity use the trusted proxy hop.
- Added critical job-error and low-balance alerts, plus an agent balance preflight.
- Fast-forwarded the event indexer and added a testnet backfill start block.
- Funded the demo agent after the balance fell below the gas-plus-deposit requirement.

## 0.5.1 — 2026-11-11

- Added sanitized near CLI diagnostics and explicit key-file checks.
- Distinguished no-transaction, refunded, and unproven-result UI states.
- Corrected the security page and MCP guidance to disclose timeout settlement.
- Installed rustfmt/clippy explicitly in CI.

## 0.5.0 — 2026-11-10

- Blocked refunds of ready results; added permissionless owner settlement after timeout.
- Contract-owner-gated dataset registration and removed the duplicate `retail_alt` copy.
- Froze protocol fees after the first query.
- Added owner-only demo budget reset and dataset removal.
- Normalized stale budget days, disabled exhausted CTAs, and disclosed public aggregate results.
- Sanitized transaction errors, refunded timed-out pending jobs, and removed the agent key from the public API process.
- Added pandas/openpyxl to the documented Python requirements, robots.txt, and Caddy security headers.

## 0.4.1 — 2026-11-10

- Pinned backend dependencies and the external verifier revision.
- Clarified the reproducible build commit for the deployed contract.
- Exposed the API version on `/api/health`.

## 0.4.0 — 2026-11-10

- Fixed the late-callback/refund state machine and added replay/duplicate-refund tests.
- Rejected duplicate computation IDs and enforced the economics invariant.
- Blocked economics changes after a dataset has queries.
- Removed owner escrow withdrawal.
- Allowlisted browser query datasets and removed synchronous paid routes.
- Added RPC snapshot fallback, stricter proxy handling, UI attestation retries, and honest proof badges.
- Updated the async incident drill and p95 calculation.
- Paused queries now fail before transaction submission.

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
