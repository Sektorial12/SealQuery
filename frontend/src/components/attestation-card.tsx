"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Download, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { explorerTx, short } from "@/lib/format";
import { cn } from "@/lib/utils";

const checks = ["authenticity", "identity", "binding", "input", "output"] as const;

export function AttestationCard({ txHash }: { txHash: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["attestation", txHash],
    queryFn: () => api.attestation(txHash),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="rounded-xl border border-line bg-panel-2 p-4">
        <p className="text-xs text-muted">Verifying Intel TDX report…</p>
        <div className="mt-3 grid gap-2 sm:grid-cols-5">
          {checks.map((check) => (
            <div key={check} className="skeleton h-16" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data?.attestation) {
    return (
      <div className="rounded-xl border border-line bg-panel-2 p-4 text-xs text-muted">
        Attestation report unavailable for this transaction.{" "}
        <a href={explorerTx(txHash)} target="_blank" rel="noreferrer" className="text-accent">
          Inspect the transaction
        </a>
        .
      </div>
    );
  }

  const report = data.attestation;

  return (
    <div className="rounded-xl border border-line bg-panel-2 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-accent" />
          <span className="text-sm font-semibold">Intel TDX attestation</span>
        </div>
        <span className={cn("pill", data.proven ? "pill-accent" : "pill-danger")}>
          {data.proven ? "ALL CHECKS PASS" : "NOT PROVEN"}
        </span>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-5">
        {checks.map((name) => {
          const check = report[name];
          return (
            <div
              key={name}
              className={cn(
                "rounded-lg border p-3",
                check?.verdict === "pass" ? "border-accent/20 bg-accent/[0.035]" : "border-danger/25 bg-danger/[0.04]",
              )}
            >
              <p className="metric-label text-[9px]">{name}</p>
              <p className={cn("mt-1 font-mono text-xs", check?.verdict === "pass" ? "text-accent" : "text-danger")}>
                {check?.verdict ?? "unknown"}
              </p>
              <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-muted">{check?.detail}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px] text-muted">
        <span>Task <code className="text-ink">{report.task_id}</code></span>
        <span>Type <code className="text-ink">{report.task_type}</code></span>
        <span>TCB <code className="text-ink">{report.tcb_status}</code></span>
        <span>
          MRTD <code className="text-ink">{short(report.measurements?.mrtd, 18, 10)}</code>
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <a className="btn btn-ghost btn-sm" href={`/api/attestation/${txHash}/bundle`}>
          <Download size={13} /> Download proof bundle
        </a>
        <a className="btn btn-ghost btn-sm" href={explorerTx(txHash)} target="_blank" rel="noreferrer">
          Request tx <ArrowUpRight size={13} />
        </a>
      </div>
    </div>
  );
}
