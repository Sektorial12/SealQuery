# Security policy

SealQuery is a **testnet prototype**, not a production security boundary. Do not
use it for mainnet funds, regulated data, or a real pilot without a separate
security and legal review.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting / Security Advisories for this
repository. Do not open a public issue for a suspected vulnerability.

Include:

- the affected component and commit
- a minimal reproduction
- the impact and whether funds, keys, or data are at risk
- any relevant transaction, query, task, or proof bundle IDs

We will acknowledge a report as soon as possible and coordinate disclosure.

## Scope

In scope:

- contract authorization, escrow, refunds, budgets, and settlement
- agent and API key validation
- attestation verification and proof-bundle handling
- worker/job state, duplicate settlement, and replay
- raw-data or canary leakage
- deployment and secret-file handling

Out of scope for this prototype:

- Intel TDX or OutLayer infrastructure vulnerabilities
- NEAR testnet or public RPC outages
- issues requiring mainnet funds or a production data agreement
- automated scanners without a reproducible impact

## Known security limits

- OutLayer governance and worker registration remain centralized/trusted.
- The TEE proves which code ran on which input/output, not that the computation
  is semantically correct.
- The contract does not verify TDX quotes on-chain.
- The public browser query endpoint spends the demo agent’s testnet balance.
- No differential privacy or sybil-resistant identity layer is implemented.
- The demo API is single-process unless deployed with Postgres/Redis as in
  `compose.yaml`.

See `docs/threat-model.md` for the full model.
