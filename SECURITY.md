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
- The contract does not verify TDX quotes on-chain. The agent verifies the happy
  path; a ready query can be settled to the owner after timeout without an
  on-chain proof check.
- The public browser query endpoint spends the demo agent’s testnet balance. It
  is dataset-allowlisted, globally and per-caller rate-limited, and capped by the
  contract’s daily budget.
- Aggregate results are public on-chain and through the API. Raw rows are never
  delivered, but the answer is not exclusive to the buyer.
- Dataset registration and owner onboarding are contract-owner gated; there is
  no independent owner-proof yet.
- Unused OutLayer compute refunds accumulate in the contract; there is no agent
  withdrawal path yet.
- No differential privacy or sybil-resistant identity layer is implemented.
- The verifier checks the OutLayer worker measurement and task binding, but does
  not independently compare the executed application wasm hash in the report to
  the registered computation. Offline identity relies on unsigned bundle metadata.
- The demo API is a single process. Redis backs shared limits when deployed as in
  `compose.yaml`; a Redis outage falls back to per-process memory.
- Contract upgrades have no state-migration framework yet.

See `docs/threat-model.md` for the full model.
