# Threat model and privacy review

Scope: the SealQuery testnet proof. This document states what is protected, what
is assumed, and what remains unsolved. It is not a production security audit.

## Assets

- Raw dataset rows and the protected dataset file.
- The compute secret and the upload secret.
- Agent funds and owner payouts.
- Query parameters and aggregate results. Aggregate results are public: they
  are stored on-chain and served by the public API. Raw rows are never delivered.
- Attestation evidence and proof bundles.
- Contract state: datasets, computations, budgets, queries.

## Actors

- **Data owner:** registers datasets and approved computations.
- **Agent:** pays for and requests an approved computation.
- **Contract owner:** pause, fee, and protocol configuration.
- **OutLayer:** runs the TEE workload and publishes execution proofs.
- **NEAR:** executes the contract and callback.
- **Verifier:** runs `outlayer-verify` and checks proof bundles.
- **Attacker:** may be an agent, a data owner, an unprivileged account, or a
  network observer.

## Trust boundaries

1. Browser → demo API: same-origin HTTP, no keys in the browser.
2. Demo API → NEAR RPC: read-only views and transaction submission.
3. Contract → OutLayer: request execution and callback.
4. OutLayer TEE → contract: attested result, limited to about 900 bytes.
5. Data owner → OutLayer secrets: upload secret and compute secret.
6. Verifier → Intel collateral and OutLayer proof data: independent check.

## Threats and mitigations

### Inference and reconstruction

- **Threat:** an agent probes many aggregates to reconstruct rows or infer an
  individual.
- **Present:** per-agent, per-dataset daily budget of 20; minimum cohort 100;
  spend rounded to 1,000; growth rounded to 0.1%; cohort counts suppressed or
  reported as `100+`; canary row must never appear.
- **Residual:** no differential privacy; multiple agents/accounts can pool
  queries; daily budgets reset; small cohorts near the threshold can still leak.
- **Production need:** identity or stake for agents, cross-agent budgets,
  formal DP review, and licensing/DPIA approval.

### Output leakage

- **Threat:** raw rows, canary rows, or sensitive fields appear in a result.
- **Present:** workload accepts only allowlisted countries and periods, returns
  only aggregate fields, and the approved WASM is the only code allowed to read
  the dataset. The canary is checked in tests and evidence.
- **Residual:** the TEE proves which code ran, not that the code is bug-free.

### Sybil resistance

- **Threat:** an attacker creates many agent accounts to bypass budgets.
- **Present:** budget is enforced per NEAR account.
- **Residual:** testnet accounts are cheap; no identity, payment stake, or
  global rate limit prevents sybil querying.
- **Production need:** allowlisted buyers, deposits/stake, or a privacy budget
  shared across identities.

### Unauthorized computation and direct OutLayer access

- **Threat:** an agent runs different code or calls OutLayer directly with a
  stolen payment key.
- **Present:** the contract allowlist checks dataset/computation; the compute
  secret access condition requires the SealQuery contract as predecessor;
  direct-call, unauthorized acceptance, and replay tests fail safely.
- **Residual:** OutLayer governance and the payment key issuer remain trusted.

### TEE and OutLayer compromise

- **Threat:** a malicious worker, forged attestation, or compromised OutLayer
  governance returns a false result.
- **Present:** Intel TDX quote verification, collateral validity, TCB status,
  measurement approval, input/output binding, and offline proof bundles.
- **Residual:** OutLayer controls worker registration and governance keys; the
  TEE does not prove the approved computation is semantically correct. No
  on-chain TDX quote verification is claimed.

### Attestation identity scope

The online verifier checks the OutLayer worker measurement and task binding. SealQuery
does not independently compare the executed application wasm hash in the report to the
registered computation; the contract pins the requested source version and the workload
checks the dataset hash. Offline bundle identity depends on unsigned bundle metadata.
This is a known gap for a production deployment.

### Callback and result manipulation

- **Threat:** a malicious callback changes the result, replays an old result, or
  causes duplicate settlement.
- **Present:** the callback is bound to the query; only the requesting agent can
  accept; acceptance checks `ready` status; replay and duplicate-settlement
  tests fail; refunds are one-shot.
- **Residual:** the callback payload is limited to about 900 bytes; large
  results need an off-chain delivery plus hash-settlement design.

### Payment and refund

- **Threat:** an agent pays but receives no result, or a failed query is not
  refunded.
- **Present:** escrow, explicit `refund_query`, failure tests, and evidence of
  refunds. Paused contracts reject new queries.
- **Residual:** transaction fees are not refunded; retry loops can cost gas.

### Key compromise

- **Threat:** stolen agent, owner, OutLayer, or API keys.
- **Present:** keys stay in the NEAR keychain/local environment; `.env` is
  ignored; the browser never receives keys; the secret scanner and CI run on
  every change.
- **Residual:** no central secret manager, short-lived credentials, or HSM in
  the demo. A compromised agent key can spend its balance and exhaust its
  budget.

### Dataset substitution and rotation

- **Threat:** a data owner or operator swaps the dataset behind a registered
  hash.
- **Present:** dataset hashes are registered and checked by the workload;
  registration is contract-owner gated, so a different account cannot create a
  new owner record for an existing dataset;
  rotation is owner-controlled and logged.
- **Residual:** there is no historical version registry; the active version is
  the source of truth.

### Availability and denial of service

- **Threat:** public RPC rate limits, OutLayer outage, API crash, or query spam.
- **Present:** RPC semaphore/retries, state caching, API rate limit, refunds,
  pause, and monitoring.
- **Residual:** single-process API, in-memory limits, external testnet
  dependencies, no on-call rotation.

## Privacy review

- The dataset is public UCI Online Retail data used as a private-data stand-in;
  the privacy claim is architectural, not about this source.
- The canary row (`CANARY-0001` / `Canaryland` / customer `99999`) must never
  appear in a result or agent log.
- Minimum cohort, rounding, and daily budgets are the first privacy controls.
  Differential privacy is not implemented.
- A real deployment needs a data-processing agreement, licensing review, DPIA,
  retention policy, and incident notification process.

## Independent verification

- `outlayer-verify` checks authenticity, identity, binding, input, output, and
  Intel collateral.
- Proof bundles are downloadable from the API and verify offline with
  `outlayer-verify bundle <file> --offline --short`.
- The contract does not verify TDX quotes on-chain; verification is off-chain
  and the proof bundle is the evidence.

## Findings

No critical finding was identified within the testnet proof scope. The open
production gaps above are material: centralized OutLayer governance, no
central secret manager, no sybil-resistant identity, no differential privacy,
and no large-result delivery. These must be addressed before a paid production
pilot.
