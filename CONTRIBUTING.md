# Contributing to SealQuery

SealQuery is a testnet prototype for private data computation with NEAR,
OutLayer, and Intel TDX. Contributions should keep the core loop real: no mocked
TEE execution, no fabricated attestations, no simulated payments, and no raw
dataset delivery to agents.

## Repository layout

- `contracts/sealquery/` — NEAR registry and escrow contract
- `workload/` — approved WASI computation
- `agent/` — agent client
- `backend/` — FastAPI API, async worker, indexer, Postgres models
- `frontend/` — Next.js product app
- `api/`, `web/` — legacy Flask API and demo console
- `mcp/` — MCP stdio server
- `scripts/` — dataset, deploy, verification, monitoring, demo tools
- `docs/` — evidence, operations, threat model, architecture

## Development checks

Run the checks that apply to your change:

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace

python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
CONTRACT_ACCOUNT=contract.testnet AGENT_ACCOUNT=agent.testnet \
  DATABASE_URL=sqlite:////tmp/sealquery-test.db REDIS_URL= \
  PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests -q

cd frontend
pnpm install --frozen-lockfile
pnpm lint
pnpm build
```

For a full local stack, copy `.env.example` to `.env`, set the testnet accounts
and `NEAR_ACCESS_KEY_FILE`, then run:

```bash
docker compose up -d --build
```

## Coding conventions

- Rust: `cargo fmt` and clippy-clean.
- Python: keep FastAPI routes thin; put chain/DB logic in `backend/app/services.py`.
- TypeScript: strict mode, typed API responses, no `any` unless unavoidable.
- Do not add comments that only restate the code.
- Keep user-facing claims reproducible and backed by `docs/evidence.md`.

## Secrets and local artifacts

Never commit:

- `.env`, access-key JSON, private keys, seed phrases, API keys, payment keys
- `data/`, generated proofs, local databases, build output
- local research notes, roadmap files, or agent configuration

If you accidentally expose a secret, stop and contact the maintainers; do not
rewrite public history without approval.

## Pull requests

- Keep changes focused and explain the capability, not a planning phase.
- Include tests or evidence for behavior changes.
- Update `docs/evidence.md` for new on-chain or attestation evidence.
- Update the README when a public command, endpoint, or deployment surface changes.
- Confirm `./scripts/check_secrets.sh` and `git diff --check` pass.

Security issues should follow `SECURITY.md`, not a public issue.
