"use client";

import { useQuery } from "@tanstack/react-query";
import { BookOpen, Code2, Server, Terminal } from "lucide-react";
import { CopyButton, SectionHeading, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { short } from "@/lib/format";

const queryCurl = `curl -s http://127.0.0.1:8000/api/query \\
  -H 'Content-Type: application/json' \\
  -d '{"dataset_id":"retail_v1","computation_id":"spend_growth_v1"}' | jq`;

const machineCurl = `curl -s http://127.0.0.1:8000/api/v1/query \\
  -H "X-API-Key: $SEALQUERY_API_KEY" \\
  -H 'Idempotency-Key: demo-1' \\
  -H 'Content-Type: application/json' \\
  -d '{"dataset_id":"retail_v1"}' | jq`;

const verify = `outlayer-verify tx <request-tx-hash> \\
  --network testnet \\
  --api https://testnet-api.outlayer.ai \\
  --json

outlayer-verify bundle proof.json --offline --short`;

export default function DocsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 30_000 });

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

  return (
    <div className="mx-auto w-full max-w-[1240px] px-5 py-14 sm:px-8">
      <SectionHeading
        eyebrow="Developer docs"
        title="Integrate a private-data answer."
        description="One REST call or MCP tool for the full loop: quote, pay, execute, verify, and settle. The response is an aggregate plus a proof — never raw rows."
      />

      <div className="mt-10 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <aside className="panel h-fit p-5 lg:sticky lg:top-24">
          <p className="metric-label">On this page</p>
          <nav className="mt-3 grid gap-1 text-xs text-muted">
            {[
              ["#quickstart", "Quickstart"],
              ["#api", "REST API"],
              ["#mcp", "MCP"],
              ["#contract", "Contract"],
              ["#verification", "Proof verification"],
              ["#limitations", "Limitations"],
              ["#self-host", "Self-host"],
            ].map(([href, label]) => (
              <a key={href} href={href} className="rounded-lg px-2 py-1.5 hover:bg-panel-2 hover:text-ink">{label}</a>
            ))}
          </nav>
          <div className="mt-5 rounded-xl border border-line bg-panel-2 p-3">
            <p className="metric-label text-[9px]">Open source</p>
            <p className="mt-1 text-[11px] leading-5 text-muted">MIT licensed. Self-host path and Docker Compose are part of the production prototype.</p>
          </div>
        </aside>

        <div className="space-y-5">
          <section id="quickstart" className="panel p-6">
            <div className="flex items-center gap-2"><BookOpen size={16} className="text-accent" /><h2 className="text-lg font-semibold">Quickstart</h2></div>
            <p className="mt-2 text-xs leading-6 text-muted">
              Start the API and the Next.js app, then run the first query. The browser console and the REST API hit the same real testnet flow.
            </p>
            <div className="code-block mt-4">
{`# terminal 1: FastAPI
export CONTRACT_ACCOUNT='<v2 contract>'
export AGENT_ACCOUNT='<agent account>'
export SEALQUERY_API_KEY='<local-demo-key>'
./scripts/run_backend.sh

# terminal 2: Next.js app
cd frontend
pnpm install
API_URL=http://127.0.0.1:8000 pnpm dev`}
            </div>
            <p className="mt-2 text-[10px] text-faint">The FastAPI service is served at :8000; the Next.js app is served at :3000 and proxies /api to it.</p>
          </section>

          <section id="api" className="panel p-6">
            <div className="flex items-center gap-2"><Code2 size={16} className="text-accent" /><h2 className="text-lg font-semibold">REST API</h2></div>
            <p className="mt-2 text-xs leading-6 text-muted">The browser route is same-origin and key-free. Machine clients use <code className="font-mono text-accent">/api/v1/query</code> with an API key and idempotency key.</p>
            <div className="mt-4 grid gap-3">
              <CodeBlock title="Run a query" code={queryCurl} />
              <CodeBlock title="Machine query" code={machineCurl} />
            </div>
            <div className="mt-4 overflow-x-auto">
              <table className="data-table">
                <thead><tr><th>Endpoint</th><th>Purpose</th></tr></thead>
                <tbody>
                  {[
                    ["GET /api/state", "datasets, budgets, recent queries"],
                    ["GET /api/metrics", "alerts, balances, query status"],
                    ["GET /api/queries", "agent query history"],
                    ["GET /api/queries/:id", "one query record"],
                    ["POST /api/query", "enqueue browser query; 202 + job_id"],
                    ["GET /api/jobs/:job_id", "poll browser job"],
                    ["GET /api/owner/summary", "indexed owner earnings"],
                    ["POST /api/v1/query", "enqueue machine query; X-API-Key"],
                    ["GET /api/v1/jobs/:job_id", "poll machine job"],
                    ["GET /api/attestation/:tx", "structured TDX report"],
                    ["GET /api/attestation/:tx/bundle", "download proof bundle"],
                  ].map(([path, note]) => (
                    <tr key={path}><td className="font-mono text-[11px] text-accent">{path}</td><td className="text-xs text-muted">{note}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section id="mcp" className="panel p-6">
            <div className="flex items-center gap-2"><Terminal size={16} className="text-accent" /><h2 className="text-lg font-semibold">MCP</h2></div>
            <p className="mt-2 text-xs leading-6 text-muted">Expose SealQuery as tools to Claude, Cursor, or any MCP client. <code className="font-mono text-accent">run_query</code> performs a real paid testnet query and returns the aggregate plus proof metadata.</p>
            <CodeBlock title="Client configuration" code={mcpConfig} />
            <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-muted">
              {["list_datasets", "quote", "run_query", "get_query", "verify_query"].map((tool) => <span key={tool} className="pill">{tool}</span>)}
            </div>
          </section>

          <section id="contract" className="panel p-6">
            <div className="flex items-center gap-2"><Server size={16} className="text-accent" /><h2 className="text-lg font-semibold">Contract</h2></div>
            {isLoading ? <Skeleton className="mt-4 h-24" /> : (
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                <Address label="Contract" value={data?.contract} />
                <Address label="Agent" value={data?.agent} />
              </div>
            )}
            <p className="mt-3 text-[10px] text-faint">NEAR testnet · escrow, dataset registry, privacy budget, query history, acceptance, refunds.</p>
          </section>

          <section id="verification" className="panel p-6">
            <h2 className="text-lg font-semibold">Proof verification</h2>
            <p className="mt-2 text-xs leading-6 text-muted">Do not trust the UI badge. Verify the transaction or the downloaded bundle independently.</p>
            <CodeBlock title="Verify" code={verify} />
            <p className="mt-2 text-[10px] text-faint">A valid result must pass authenticity, identity, binding, input, and output; TCB should be UpToDate.</p>
          </section>

          <section id="limitations" className="panel border-warning/25 p-6">
            <h2 className="text-lg font-semibold">Limitations</h2>
            <ul className="mt-3 grid gap-2 text-xs leading-6 text-muted">
              <li>• Testnet only; NEAR testnet payments and OutLayer testnet compute.</li>
              <li>• Public dataset used as a private-data stand-in.</li>
              <li>• No differential privacy; budget + cohort + rounding are the current controls.</li>
              <li>• OutLayer governance is centralized; the TEE proves what ran, not correctness.</li>
              <li>• No token, no mainnet deployment, no human wallet flow yet.</li>
            </ul>
          </section>

          <section id="self-host" className="panel p-6">
            <h2 className="text-lg font-semibold">Self-host</h2>
            <p className="mt-2 text-xs leading-6 text-muted">
              The canonical deployment is a Docker Compose stack: Next.js web, FastAPI API, indexer, Postgres, Redis, and Caddy. The hosted mirror uses Render + Neon. Docker builds <code className="font-mono">near-cli-rs</code> and <code className="font-mono">outlayer-verify</code> from source for the backend image.
            </p>
            <div className="code-block mt-4">{`cp .env.example .env
# fill CONTRACT_ACCOUNT, AGENT_ACCOUNT, SEALQUERY_API_KEY,
# NEAR_CREDENTIALS_DIR
docker compose up --build`}</div>
            <p className="mt-2 text-[10px] text-faint">Open http://127.0.0.1:8080. Caddy routes /api to FastAPI and the rest to Next.js.</p>
          </section>
        </div>
      </div>
    </div>
  );
}

function CodeBlock({ title, code }: { title: string; code: string }) {
  return (
    <div className="rounded-xl border border-line bg-[#080c10] p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="metric-label text-[9px]">{title}</p>
        <CopyButton value={code} label="Copy" />
      </div>
      <pre className="mt-2 overflow-x-auto text-[10px] leading-5 text-muted">{code}</pre>
    </div>
  );
}

function Address({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel-2 p-3">
      <p className="metric-label text-[9px]">{label}</p>
      <p className="mt-1 truncate font-mono text-[11px] text-ink" title={value}>{short(value, 22, 12)}</p>
    </div>
  );
}
