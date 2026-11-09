# SealQuery Evidence Log

Record reproducible evidence for each capability below. Include transaction hashes, attestation task IDs, verifier output, and screenshots or logs where useful.

## Environment

- Network: NEAR testnet
- Deployer: `sealquery-1794187176.testnet`
- Contract account: `contract.sealquery-1794187176.testnet` (created, not deployed)
- Data-owner account: `owner.sealquery-1794187176.testnet`
- Agent account: `agent.sealquery-1794187176.testnet`
- OutLayer project: `sealquery-1794187176.testnet/sealquery-probe`
- Tool versions:
  - rustc 1.99.1
  - cargo-near 0.23.0
  - near-cli-rs 0.31.1
  - outlayer 0.2.2
  - wasmtime 50.0.1
  - outlayer-verify 0.1.0

## OutLayer TEE probe

- WASM SHA-256: `3c42ee40fc6d640569068f4ef1be6da09e235bfa22dfca00c1aaca4dffe17197`
- FastFS URL: `https://test.fastfs.io/sealquery-1794187176.testnet/outlayer.testnet/3c42ee40fc6d640569068f4ef1be6da09e235bfa22dfca00c1aaca4dffe17197.wasm`
- Upload transaction: `7ymAHgFdzix7d84PFq5KudqA6xbzRntjfMkSW72XTzVK`
- Project: `sealquery-1794187176.testnet/sealquery-probe`
- Execution transaction: `8pxfgLFmPSmKtpyBrGjEZPLfcqJBLS96zcJJBNcawJ3S`
- Task ID: `29081`
- Attestation record: `https://testnet-api.outlayer.ai/attestations/by-request/29081`
- Verification command:
  ```bash
  outlayer-verify tx 8pxfgLFmPSmKtpyBrGjEZPLfcqJBLS96zcJJBNcawJ3S \
    --network testnet \
    --api https://testnet-api.outlayer.ai \
    --short
  ```
- Verification result: `PROVEN task 29081 (execute) 51626e3ed52949cb…8c587920`
- Testnet limitation: `outlayer-verify` 0.1.0 defaults to the retired `testnet-api.outlayer.fastnear.com` API. Pass `--api https://testnet-api.outlayer.ai`.

## Dataset upload

- Dataset:
- Sample size:
- Dataset SHA-256:
- Canary row hash:
- Upload task ID:
- Upload attestation:

## Approved computation

- Computation ID:
- Workload WASM SHA-256:
- OutLayer project version:
- Test input:
- Expected output:
- Actual output:

## Contract deployment

- Contract address:
- Deploy transaction:
- Initialization transaction:

## End-to-end query

- Agent:
- Query transaction:
- OutLayer task ID:
- Result:
- Attestation verification:
- Acceptance transaction:
- Data-owner payout transaction:

## Negative and failure tests

- Unauthorized computation:
- Unauthorized agent:
- Direct OutLayer call:
- Replay:
- Privacy budget exceeded:
- Timeout/failure:
- Tampered attestation:
- Dataset rotation:

## Privacy checks

- Canary absent from result:
- Canary absent from agent logs:
- Agent has no dataset access:
- Agent has no data-owner secret:
- Reconstruction attempt blocked:
