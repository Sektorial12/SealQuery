# SealQuery MCP skill

Use this skill when an agent needs an aggregate answer from a private dataset
without receiving the raw rows.

## Preconditions

- The SealQuery demo API is running and reachable at `SEALQUERY_API_URL`.
- `SEALQUERY_API_KEY` matches the API server.
- The caller has funded the configured agent account and the dataset has
  remaining privacy budget.

## Tools

1. `list_datasets` — discover datasets, computations, owners, prices, and budget.
2. `quote` — read the on-chain quote before paying.
3. `run_query` — pay, execute in the TEE, verify attestation, and settle.
4. `get_query` — read the contract query record and final status.
5. `verify_query` — re-run OutLayer attestation verification.

## Example

```json
{"dataset_id":"retail_v1","computation_id":"spend_growth_v1"}
```

`run_query` returns an aggregate result plus `tx_hash`, `accept_tx`, `proof`,
and `owner_after`. It never returns raw dataset rows.

## Failure handling

- `daily privacy budget exceeded`: wait for the next UTC day or use another
  approved dataset.
- `contract is paused`: the data owner or contract owner must unpause.
- `not proven`: do not accept the result; the agent client refunds the query.
- `unauthorized`: send the configured `X-API-Key`.
