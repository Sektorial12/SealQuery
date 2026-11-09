# Testnet Production Notes

This document covers deployment, secrets, versioning, migration, and operations for the testnet build. It is a working checklist, not a mainnet readiness claim.

## Reproducible builds

Contract:

```bash
cd contracts/sealquery
cargo near build reproducible-wasm --locked --no-abi
```

Workload:

```bash
cargo build -p sealquery-workload \
  --bin sealquery-approved \
  --target wasm32-wasip2 \
  --release \
  --locked \
  --features wasm
sha256sum target/wasm32-wasip2/release/sealquery-approved.wasm
```

Record both hashes in `docs/evidence.md` and in the release notes. The workload version must match the hash registered in `register_computation`.

## Deployment

Set the values from `.env.example` in the environment, then:

```bash
# Fresh contract account
INIT=1 ./scripts/deploy_contract.sh

# Existing contract account, code-only upgrade
./scripts/deploy_contract.sh

# OutLayer workload
OUTLAYER_PROJECT_NAME=sealquery-approved ./scripts/deploy_workload.sh

# Dataset and computation registration
./scripts/register_computation.sh
```

Deploy scripts never read keys from the repository. The NEAR CLI uses the local keychain; OutLayer uses its own credentials under `~/.outlayer/`.

## Secrets

- Agent and data-owner keys must live in a secret manager or the local keychain, never in `.env` files committed to the repository.
- OutLayer upload and compute secrets are generated inside the TEE with `PROTECTED_*` names.
- The compute secret access condition must be `Predecessor` scoped to the SealQuery contract, not a personal account.
- Rotate agent keys and payment keys on a schedule and after any suspected exposure.
- Run `./scripts/check_secrets.sh` before every commit.

## Versioning and migration

- The contract exposes `version()` and `get_dataset`, `get_computation`, `get_query`, `get_budget`.
- State layout changes require a migration method and a release note. Do not silently redeploy a layout change.
- Workload changes require a new hash, a new OutLayer project version, and an `update_computation` call if the existing computation should point at the new build.
- Dataset rotation requires a new dataset version and hash; old query results must not be replayed as the new version.

## CI

`.github/workflows/ci.yml` runs:

- `cargo fmt --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo test --workspace`
- approved workload WASM build
- contract WASM build
- secret scan

A manual `workflow_dispatch` job runs the reproducible contract build.

## Operations checklist

- Monitor failed queries, OutLayer callback timeouts, budget exhaustion, low balances, and payout failures.
- Keep an OutLayer outage runbook: stop new requests, refund failed queries, communicate status.
- Keep a contract upgrade runbook: build, hash, deploy, migrate, verify, update evidence.
- Keep a key-rotation runbook for agent, data-owner, and payment keys.
- Run load and chaos tests before a pilot: concurrent agents, callback timeout, duplicate settlement, stale result.
- Review privacy controls: minimum cohort, rounding, daily budget, canary absence, output leakage.
- Never claim on-chain TDX quote verification; verification is performed by `outlayer-verify` and the proof bundle is retained.
