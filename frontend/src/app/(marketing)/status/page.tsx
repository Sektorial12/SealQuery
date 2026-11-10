"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";
import { QueryHistory } from "@/components/query-history";
import { SectionHeading, Skeleton, Stat } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { formatNear } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function StatusPage() {
  const metrics = useQuery({ queryKey: ["metrics"], queryFn: api.metrics, refetchInterval: 15_000 });
  const state = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 15_000 });
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, refetchInterval: 30_000 });

  const loading = metrics.isLoading || state.isLoading || health.isLoading;
  const data = metrics.data;
  const critical = data?.alerts.some((alert) => alert.severity === "critical");
  const statusLabel = loading ? "Checking" : critical ? "Attention" : data?.paused ? "Paused" : "Operational";

  return (
    <div className="mx-auto w-full max-w-[1240px] px-5 py-14 sm:px-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <SectionHeading
          eyebrow="Status"
          title="Testnet operations"
          description="Live contract, API, budgets, balances, and alerts. Metrics refresh every 15 seconds; the contract remains the source of truth."
        />
        <div className="flex items-center gap-2">
          <span className={cn("pill", critical ? "pill-danger" : data?.paused ? "pill-warning" : "pill-accent")}>
            {statusLabel}
          </span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => { metrics.refetch(); state.refetch(); health.refetch(); }}>
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div className="mt-8 grid gap-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-64" />
        </div>
      ) : metrics.error || state.error || health.error ? (
        <div className="panel mt-8 border-danger/30 p-5 text-sm text-danger">
          Status endpoint unavailable: {String(metrics.error || state.error || health.error)}
        </div>
      ) : data && state.data && health.data ? (
        <div className="mt-8 space-y-4">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Stat label="API" value={health.data.ok ? "OK" : "Down"} tone={health.data.ok ? "accent" : "danger"} />
            <Stat label="Contract" value={data.paused ? "Paused" : "Live"} tone={data.paused ? "warning" : "accent"} />
            <Stat label="Recent success" value={data.queries.recent_success_rate === null ? "—" : `${Math.round(data.queries.recent_success_rate * 100)}%`} />
            <Stat label="Agent balance" value={`${formatNear(data.balances.agent, 3)} NEAR`} />
          </div>

          <section className="panel p-5">
            <div className="flex items-center gap-2">
              {critical ? <AlertTriangle size={16} className="text-danger" /> : <CheckCircle2 size={16} className="text-accent" />}
              <h2 className="text-lg font-semibold">Alerts</h2>
              <span className="ml-auto text-[10px] text-faint">generated {new Date(data.generated_at).toLocaleTimeString()}</span>
            </div>
            {data.alerts.length ? (
              <div className="mt-3 grid gap-2">
                {data.alerts.map((alert) => (
                  <div key={alert.code} className={cn("rounded-xl border p-3 text-xs", alert.severity === "critical" ? "border-danger/30 bg-danger/[0.05] text-danger" : alert.severity === "warning" ? "border-warning/25 bg-warning/[0.05] text-warning" : "border-line bg-panel-2 text-muted")}>
                    <span className="font-mono text-[10px] uppercase">{alert.severity}</span> · <span className="font-semibold">{alert.code}</span>
                    <p className="mt-1 text-[11px] leading-5">{alert.message}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-xs text-muted">No active alerts.</p>
            )}
          </section>

          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <section className="panel p-5">
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-accent" />
                <h2 className="text-lg font-semibold">Datasets and budgets</h2>
              </div>
              <div className="mt-4 grid gap-3">
                {data.datasets.map((dataset) => {
                  const percent = dataset.limit ? Math.min(100, (dataset.used / dataset.limit) * 100) : 0;
                  return (
                    <div key={dataset.dataset_id} className="rounded-xl border border-line bg-panel-2 p-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold">{dataset.dataset_id}</span>
                        <span className="font-mono text-[10px] text-muted">{dataset.used}/{dataset.limit}</span>
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-panel-3">
                        <div className={cn("h-full rounded-full", dataset.exhausted ? "bg-danger" : "bg-accent")} style={{ width: `${percent}%` }} />
                      </div>
                      <p className="mt-1 truncate font-mono text-[9px] text-faint">{dataset.owner}</p>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                <Balance label="Agent" value={data.balances.agent} />
                <Balance label="Contract" value={data.balances.contract} />
              </div>
            </section>

            <section className="panel p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="eyebrow">Recent activity</p>
                  <h2 className="mt-1 text-lg font-semibold">Queries</h2>
                </div>
                <span className="pill">{data.queries.recent} recent</span>
              </div>
              <div className="mt-3">
                <QueryHistory queries={state.data.recent_queries} limit={5} />
              </div>
            </section>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Balance({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="rounded-xl border border-line bg-panel-2 p-3">
      <p className="metric-label text-[9px]">{label} balance</p>
      <p className="mt-1 font-mono text-xs text-ink">{formatNear(value, 4)} NEAR</p>
    </div>
  );
}
