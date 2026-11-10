"use client";

import { useQuery } from "@tanstack/react-query";
import { KeyRound, Terminal } from "lucide-react";
import Link from "next/link";
import { QueryHistory } from "@/components/query-history";
import { CopyButton, SectionHeading, Stat } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { formatNear, short } from "@/lib/format";

export default function AgentPage() {
  const { data: state, isLoading } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const { data: metrics } = useQuery({ queryKey: ["metrics"], queryFn: api.metrics, refetchInterval: 20_000 });

  if (isLoading) return <div className="skeleton h-80" />;

  const queries = state?.recent_queries ?? [];
  const settled = queries.filter((query) => query.status === "settled" || query.status === "ready").length;
  const refunds = queries.filter((query) => query.status === "refunded").length;
  const dataset = state?.datasets[0];
  const remaining = dataset ? Math.max(0, dataset.dataset.budget_per_day - dataset.budget.count) : 0;

  const mcpConfig = `{
  "mcpServers": {
    "sealquery": {
      "command": "python3",
      "args": ["mcp/server.py"],
      "env": {
        "SEALQUERY_API_URL": "http://127.0.0.1:8000",
        "SEALQUERY_API_KEY": "<your key>"
      }
    }
  }
}`;

  const curl = `curl -s http://127.0.0.1:8000/api/state | jq '{paused, datasets: [.datasets[] | {dataset_id, price: .quote.price_yocto}]}'`;

  return (
    <div className="space-y-5">
      <SectionHeading
        eyebrow="Agent"
        title="Agent workspace"
        description="The configured agent runs server-side with the demo key. Use this page for balances, budgets, API access, and MCP wiring."
      />

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Stat label="Agent" value={short(state?.agent, 14, 8)} hint="NEAR testnet" />
        <Stat label="Balance" value={`${formatNear(metrics?.balances.agent, 3)} NEAR`} tone="accent" />
        <Stat label="Recent settled" value={settled} />
        <Stat label="Budget left" value={remaining} hint={`${dataset?.dataset.budget_per_day ?? 0}/day`} tone={remaining ? "default" : "warning"} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="panel p-5">
          <div className="flex items-center gap-2">
            <KeyRound size={16} className="text-accent" />
            <h2 className="text-lg font-semibold">API access</h2>
          </div>
          <p className="mt-2 text-xs leading-6 text-muted">
            Browser queries use the same-origin demo endpoint. Machine clients use the authenticated
            version and an idempotency key.
          </p>
          <div className="mt-4 grid gap-2">
            <Endpoint method="GET" path="/api/state" note="contract state, datasets, budgets" />
            <Endpoint method="POST" path="/api/query" note="browser demo query" />
            <Endpoint method="POST" path="/api/v1/query" note="machine query · X-API-Key" />
            <Endpoint method="GET" path="/api/attestation/:tx" note="structured TDX report" />
          </div>
          <div className="mt-4 rounded-xl border border-line bg-[#080c10] p-3">
            <div className="flex items-center justify-between">
              <span className="metric-label">Quick check</span>
              <CopyButton value={curl} label="Copy" />
            </div>
            <pre className="mt-2 overflow-x-auto text-[10px] leading-5 text-muted">{curl}</pre>
          </div>
        </section>

        <section className="panel p-5">
          <div className="flex items-center gap-2">
            <Terminal size={16} className="text-accent" />
            <h2 className="text-lg font-semibold">MCP</h2>
          </div>
          <p className="mt-2 text-xs leading-6 text-muted">
            Expose <code className="font-mono text-accent">list_datasets</code>, <code className="font-mono text-accent">quote</code>,{" "}
            <code className="font-mono text-accent">run_query</code>, <code className="font-mono text-accent">get_query</code>, and{" "}
            <code className="font-mono text-accent">verify_query</code> to Claude, Cursor, or another MCP client.
          </p>
          <div className="mt-4 rounded-xl border border-line bg-[#080c10] p-3">
            <div className="flex items-center justify-between">
              <span className="metric-label">Client config</span>
              <CopyButton value={mcpConfig} label="Copy" />
            </div>
            <pre className="mt-2 max-h-72 overflow-auto text-[10px] leading-5 text-muted">{mcpConfig}</pre>
          </div>
          <Link href="/docs#mcp" className="btn btn-ghost btn-sm mt-3">MCP reference</Link>
        </section>
      </div>

      <section className="panel p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="eyebrow">Usage</p>
            <h2 className="mt-1 text-lg font-semibold">Recent agent activity</h2>
          </div>
          <span className="pill">{queries.length} queries · {refunds} refunds</span>
        </div>
        <div className="mt-3">
          <QueryHistory queries={queries} limit={8} />
        </div>
      </section>
    </div>
  );
}

function Endpoint({ method, path, note }: { method: string; path: string; note: string }) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-line bg-panel-2 px-3 py-2">
      <span className="pill text-[9px]">{method}</span>
      <code className="font-mono text-[11px] text-ink">{path}</code>
      <span className="ml-auto text-[10px] text-faint">{note}</span>
    </div>
  );
}
