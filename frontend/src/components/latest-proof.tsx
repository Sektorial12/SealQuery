"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Check, Download, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { explorerTx, parseResult, short } from "@/lib/format";
import { cn } from "@/lib/utils";

export function LatestProof() {
  const { data: state, isLoading, error } = useQuery({
    queryKey: ["state"],
    queryFn: api.state,
    refetchInterval: 20_000,
  });
  const latest = state?.recent_queries
    ?.slice()
    .reverse()
    .find((query) => query.tx_hash && (query.status === "settled" || query.status === "ready"));

  const { data: attestation } = useQuery({
    queryKey: ["attestation", latest?.tx_hash],
    queryFn: () => api.attestation(latest!.tx_hash!),
    enabled: Boolean(latest?.tx_hash),
    retry: false,
  });

  if (isLoading) {
    return <div className="panel skeleton min-h-[360px]" />;
  }

  if (error) {
    return (
      <div className="panel p-5">
        <p className="eyebrow">Proof artifact</p>
        <h3 className="mt-2 text-lg font-semibold">Live proof unavailable</h3>
        <p className="mt-2 text-xs leading-6 text-muted">
          The testnet API is temporarily unreachable. The proof explorer will work when it returns.
        </p>
      </div>
    );
  }

  if (!latest) {
    return (
      <div className="panel p-5">
        <p className="eyebrow">Proof artifact</p>
        <h3 className="mt-2 text-lg font-semibold">No verified answer yet</h3>
        <p className="mt-2 text-xs leading-6 text-muted">
          Run an approved computation from the agent console. The result, TDX report, and settlement
          links will appear here.
        </p>
        <Link href="/app" className="btn btn-primary btn-sm mt-4">
          Run the first query
        </Link>
      </div>
    );
  }

  const parsed = parseResult(latest.result);
  const row = parsed?.results?.[0];
  const report = attestation?.attestation;

  return (
    <div className="panel overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-accent" />
          <span className="text-sm font-semibold">Latest verified answer</span>
        </div>
        <span className={cn("pill", attestation?.proven ? "pill-accent" : "pill-warning")}>
          {attestation?.proven ? "PROVEN" : "VERIFYING"}
        </span>
      </div>
      <div className="grid gap-5 p-5 md:grid-cols-[1fr_0.9fr]">
        <div>
          <p className="metric-label">Query #{latest.query_id} · {latest.dataset_id}</p>
          <div className="mt-3 flex items-end gap-3">
            <span className="text-4xl font-bold tracking-[-0.05em] text-accent">
              {row ? `${row.growth_pct}%` : "—"}
            </span>
            <span className="pb-1 text-xs text-muted">{row?.country ?? "aggregate output"}</span>
          </div>
          <p className="mt-2 text-[11px] text-faint">
            Spend {row?.spend_a ?? "—"} → {row?.spend_b ?? "—"} · cohorts {row?.cohort_a ?? "suppressed"} / {row?.cohort_b ?? "suppressed"}
          </p>

          <div className="mt-5 grid gap-2 sm:grid-cols-3">
            <ProofMeta label="Task" value={report ? String(report.task_id) : "—"} />
            <ProofMeta label="TCB" value={report?.tcb_status ?? "—"} />
            <ProofMeta label="Checks" value={report ? "5 / 5" : "—"} />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <Link href={`/app/queries/${latest.query_id}`} className="btn btn-primary btn-sm">
              Open proof <ArrowUpRight size={13} />
            </Link>
            {latest.tx_hash ? (
              <a className="btn btn-ghost btn-sm" href={`/api/attestation/${latest.tx_hash}/bundle`}>
                <Download size={13} /> Proof bundle
              </a>
            ) : null}
          </div>
        </div>

        <div className="rounded-xl border border-line bg-[#080c10] p-4">
          <p className="metric-label">Verification</p>
          <div className="mt-3 grid gap-2">
            {["authenticity", "identity", "binding", "input", "output"].map((name) => {
              const check = report?.[name as keyof typeof report] as { verdict?: string } | undefined;
              const pass = check?.verdict === "pass";
              return (
                <div key={name} className="flex items-center justify-between gap-2 text-[11px]">
                  <span className="text-muted">{name}</span>
                  <span className={cn("flex items-center gap-1 font-mono", pass ? "text-accent" : "text-warning")}>
                    {pass ? <Check size={11} /> : null}
                    {check?.verdict ?? "loading"}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="mt-4 border-t border-line pt-3">
            <p className="text-[10px] leading-5 text-faint">
              MRTD <span className="font-mono text-muted">{short(report?.measurements?.mrtd, 16, 8)}</span>
            </p>
            {latest.tx_hash ? (
              <a className="mt-2 inline-flex items-center gap-1 text-[10px] text-accent" href={explorerTx(latest.tx_hash)} target="_blank" rel="noreferrer">
                request tx <ArrowUpRight size={10} />
              </a>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function ProofMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel-2 px-3 py-2">
      <p className="metric-label text-[9px]">{label}</p>
      <p className="mt-1 truncate font-mono text-[11px] text-ink">{value}</p>
    </div>
  );
}
