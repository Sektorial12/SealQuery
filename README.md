# SealQuery

SealQuery lets AI agents pay to execute approved computations against privately held datasets without receiving the raw data.

A data owner registers a dataset and the computations it permits. An agent requests one approved computation and pays for execution. The computation runs inside a trusted execution environment. The agent receives an attested result; the data owner receives payment or royalties. The raw data is never delivered to the agent.

## Status

Early development. The current goal is a testnet proof of the technical thesis:

- one real dataset stored privately;
- one approved computation executed in a real TEE;
- one agent query with on-chain payment;
- independent attestation verification;
- on-chain settlement only after the agent verifies the result;
- rejection of unauthorized computations, unauthorized agents, replayed results, and privacy-budget violations.

No production deployment yet.

## Stack

- NEAR testnet for dataset registration, query escrow, callbacks, settlement, and royalties.
- OutLayer for Intel TDX confidential computation and execution attestations.
- Rust/WASI workload for the approved computation.
- Rust `near-sdk` contract for the registry and escrow.

## Repository layout

```
contracts/sealquery/   NEAR contract
workload/              approved WASI computation
agent/                 agent client
indexer/               attestation/task indexer
scripts/               deployment and test scripts
docs/                  evidence and design notes
```

## Development

Build the contract:

```bash
cargo near build
```

Build the workload:

```bash
cargo build --target wasm32-wasip2 --release -p sealquery-workload
```

Run tests:

```bash
cargo test
```

Exact testnet commands and reproducible evidence will be added as the implementation reaches each capability.
