# SealQuery MCP Server

`mcp/server.py` exposes the SealQuery agent API as MCP tools over stdio.

## Prerequisites

Start the demo API first:

```bash
export CONTRACT_ACCOUNT='<v2 contract>'
export AGENT_ACCOUNT='<agent account>'
export SEALQUERY_API_KEY='<local secret>'
./scripts/run_backend.sh
```

## Client configuration

Claude Desktop, Cursor, or another MCP client can launch the server with:

```json
{
  "mcpServers": {
    "sealquery": {
      "command": "python3",
      "args": ["/absolute/path/to/code/mcp/server.py"],
      "env": {
        "SEALQUERY_API_URL": "http://127.0.0.1:8000",
        "SEALQUERY_API_KEY": "<same local secret>"
      }
    }
  }
}
```

## Tools

- `list_datasets` — datasets, approved computations, owners, prices, budgets
- `quote` — on-chain quote and remaining privacy budget
- `run_query` — pay, execute, verify attestation, and settle; returns aggregate output
- `get_query` — read a contract query record
- `verify_query` — independently re-verify an OutLayer attestation

`run_query` performs a real testnet transaction and a real TEE execution. It
returns the aggregate result and settlement metadata, never raw rows.

## Smoke test

With the API running:

```bash
python3 scripts/mcp_smoke_test.py
python3 scripts/mcp_smoke_test.py --query
```

The first command exercises discovery and quoting. The second also performs a
real paid query through MCP.
