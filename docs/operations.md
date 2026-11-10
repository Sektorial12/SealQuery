# Operations runbook

SealQuery is currently a single-node testnet deployment. This runbook covers
monitoring, incident response, key rotation, upgrades, and the limits of the
current demo.

## Service surface

- **Contract:** `contract.sealquery-v2-1794194344.testnet`
- **Agent:** `agent2.sealquery-1794187176.testnet`
- **FastAPI:** `http://127.0.0.1:8000`
- **Next.js app:** `http://127.0.0.1:3000`
- **Compose/Caddy:** `http://127.0.0.1:8080`
- **Legacy Flask console:** `http://127.0.0.1:8080` (when not using Compose)
- **OutLayer project:** `sealquery-1794187176.testnet/sealquery-approved`
- **Proof bundles:** `data/proofs/*.json` (ignored local artifacts)

The API is the only process that holds the demo agent's keychain access. It
runs the agent loop server-side; the browser never receives a key.

## Monitoring

```bash
python3 scripts/monitor.py --once
python3 scripts/monitor.py --interval 30
# Compose/Caddy:
python3 scripts/monitor.py --url http://127.0.0.1:8080/api/metrics --once
```

The monitor polls `GET /api/metrics`. Prometheus can scrape `GET /metrics`.
Worker/indexer heartbeats are exposed as `sealquery_service_stale_seconds` and
surface as `worker_missing`/`worker_stale` or `indexer_missing`/`indexer_stale`
alerts. Alerts:

| Code | Severity | Meaning |
|---|---|---|
| `contract_paused` | critical | New queries are rejected. |
| `dataset_unavailable` | critical | A contract view or dataset lookup failed. |
| `low_agent_balance` | critical | Agent below 0.1 NEAR. |
| `low_contract_balance` | warning | Contract below 0.5 NEAR. |
| `budget_exhausted` | warning | A per-agent/per-dataset daily budget is used up. |
| `recent_failed_queries` | warning | At least one recent query failed. |
| `recent_refunds` | info | A recent query was refunded. |

`--once` exits `0` when there are no critical alerts and `2` when a critical
alert is present. A fetch failure exits `1`.

Read-path load test:

```bash
python3 scripts/load_test.py --requests 10 --concurrency 3
```

The state endpoint has a 5-second cache (`SEALQUERY_STATE_TTL_SECONDS`). The
2026-11-09 run with 6 requests and concurrency 3 returned 0 errors and p95
`54.9 ms` warm. A cold state read was `4.15 s`; RPC-backed reads are cached
briefly to avoid public-RPC rate limits. The agent RPC client limits concurrent
calls with `NEAR_RPC_CONCURRENCY` (default `3`) and retries `429`/`5xx`.

## SLOs (testnet scope)

- API health endpoint responds within 1 second when the API is up.
- Warm state reads: p95 below 1 second.
- Cold state reads: p95 below 15 seconds.
- Valid queries with an allowed dataset/computation/params: 100% reach
  `PROVEN` or fail safely with a refund.
- Attestation verification: 100% of valid proof bundles verify offline.
- Failed or timed-out queries: refund recorded within one block of the failure
  transaction.
- No critical monitoring alert is ignored during a demo.

These are testnet targets, not production SLAs.

## Runbooks

### OutLayer outage

1. Stop issuing new queries; the UI/API will return errors.
2. Check `GET /api/metrics` and the OutLayer status.
3. If queries are stuck, do not accept unproven results.
4. Let timeouts complete, then refund failed queries with `refund_query`.
5. Pause the contract if the outage is prolonged:
   ```bash
   near contract call-function as-transaction "$CONTRACT_ACCOUNT" set_paused \
     json-args '{"paused":true}' prepaid-gas '30 Tgas' attached-deposit '0 NEAR' \
     sign-as "$OWNER_ACCOUNT" network-config testnet sign-with-keychain send
   ```
6. Publish an incident note and unpause only after a successful smoke query.

### Callback timeout

1. Read the query record with `get_query`.
2. If it is `failed` or timed out, call `refund_query` as the agent.
3. Confirm the agent balance and that the query status is `refunded`.
4. Do not retry the same computation blindly; use a new query ID.

### Refund backlog

1. List recent queries with `get_queries_for_agent`.
2. Inspect each `get_query` record; refund every failed query once.
3. Confirm each refund transaction and agent balance delta.
4. A repeated refund must fail because the query is no longer refundable.

### Contract pause and unpause

Pause rejects new queries without affecting existing refunds:

```bash
DRILL_CONFIRM=1 \
CONTRACT_ACCOUNT="$CONTRACT_ACCOUNT" \
OWNER_ACCOUNT="$OWNER_ACCOUNT" \
API_URL=http://127.0.0.1:8000 \
./scripts/incident_drill.sh

# Compose: set API_URL=http://127.0.0.1:8080
```

The drill pauses, attempts a query, verifies rejection, unpauses, and verifies
service restoration. It requires `DRILL_CONFIRM=1` to prevent accidental use.

### Contract upgrade

1. Build reproducibly: `cd contracts/sealquery && cargo near build reproducible-wasm`.
2. Record the new SHA-256 in `docs/evidence.md`.
3. Deploy and inspect the code hash on-chain.
4. Run a smoke query and verify the attestation.
5. Keep the previous WASM and evidence until the new deployment is verified.

### Key rotation

- **Agent key:** create a new agent account/key, fund it, update
  `AGENT_ACCOUNT`, restart the API, run a smoke query, retire the old key.
- **API key:** generate a new `SEALQUERY_API_KEY`, restart the API, update MCP
  client configs, then revoke the old value.
- **OutLayer payment key:** create/top up a new project-scoped key, update the
  local secret environment, run a smoke query, revoke the old nonce.
- **Compute secret access:** update the OutLayer access condition to the new
  contract only after the contract upgrade is verified.
- Never place keys in the browser, repository, README, or commit messages.

### API restart or crash

Restart with `./scripts/run_backend.sh` (FastAPI) or `./scripts/run_demo.sh` (legacy Flask) and the required environment. The contract
remains authoritative. In-memory idempotency and rate-limit state is lost on
restart; clients should retry with a new idempotency key only after checking the
query history.

## Backups and restore

Use a Neon **direct** connection for backups. The script strips `+psycopg` and
`-pooler` from `DATABASE_URL` automatically.

```bash
export DATABASE_URL='postgresql+psycopg://...-pooler.../neondb?sslmode=require'
./scripts/backup_postgres.sh
```

Backups land in `backups/` (ignored). Restore is guarded:

```bash
export DATABASE_URL='postgresql+psycopg://.../neondb?sslmode=require'
export BACKUP_FILE='backups/sealquery-....dump'
RESTORE_CONFIRM=1 ./scripts/restore_postgres.sh
```

Render disks holding proof bundles are not backed up automatically; copy them to
object storage before relying on them. Neon point-in-time recovery is the
database backup of record.

## Secret management

- Local development uses `.env` (ignored) and the NEAR keychain.
- Container/Render deployments use a mounted access-key JSON file via
  `NEAR_ACCESS_KEY_FILE`; never bake the key into the image.
- The OutLayer payment key and compute secret are local environment/CLI
  secrets, never in the repo.
- Production should use a central secret manager, short-lived credentials, and
  per-service least privilege. That is not implemented in this testnet demo.
- Rotate keys on personnel changes, suspected exposure, and at least quarterly.

## Incident drill evidence

- Pause transaction: `9TGfh93yB6RFGQCMMA3RNvuEr9c8haJ7QXMWvkscUKJ6`
- Query rejected while paused: `Eep8SArVr9RNCSx6xnHV19ZZhQN2ac7U1VDyK6ZP66AN`
- Unpause transaction: `AfLEwDXbZuBKWnazcVKWNq9Sb6okcKUuAAYhiobFmHh8`
- Result: `DRILL PASSED`

## Open production gaps

- No centralized secret manager or on-call rotation.
- Idempotency/rate-limit state is in process memory.
- No full OutLayer outage simulation or paid concurrent-query load test.
- Public RPC and OutLayer testnet are external dependencies.
- The demo UI uses the server-side agent key; a human wallet flow is deferred.
