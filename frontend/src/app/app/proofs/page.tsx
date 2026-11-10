"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { AttestationCard } from "@/components/attestation-card";
import { CopyButton, SectionHeading } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { explorerTx, short } from "@/lib/format";

export default function ProofsPage() {
  const [input, setInput] = useState("");
  const [tx, setTx] = useState("");
  const { data: state } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const recent = (state?.recent_queries ?? [])
    .filter((query) => query.tx_hash && query.status !== "failed" && query.status !== "refunded")
    .slice()
    .reverse()
    .slice(0, 6);

  return (
    <div className="space-y-5">
      <SectionHeading
        eyebrow="Trust surface"
        title="Proof explorer"
        description="Verify any OutLayer request transaction: authenticity, worker identity, result binding, input, and output. Download the bundle and verify it offline."
      />

      <section className="panel p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="relative flex-1">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-faint" />
            <input
              className="input pl-9 font-mono"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="NEAR request transaction hash"
              onKeyDown={(event) => {
                if (event.key === "Enter") setTx(input.trim());
              }}
            />
          </label>
          <button type="button" className="btn btn-primary" onClick={() => setTx(input.trim())}>
            <ShieldCheck size={15} /> Verify proof
          </button>
        </div>
        <p className="mt-2 text-[10px] text-faint">
          The verifier reads the OutLayer record and Intel collateral. The contract does not verify TDX quotes on-chain.
        </p>
      </section>

      {tx ? (
        <section className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="metric-label">Transaction</p>
              <a href={explorerTx(tx)} target="_blank" rel="noreferrer" className="mt-1 flex items-center gap-1 font-mono text-xs text-accent">
                {short(tx, 26, 14)} <ArrowUpRight size={11} />
              </a>
            </div>
            <CopyButton value={tx} label="Copy tx" />
          </div>
          <AttestationCard txHash={tx} />
        </section>
      ) : null}

      <section className="panel p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="eyebrow">Recent proofs</p>
            <h2 className="mt-1 text-lg font-semibold">Verifiable queries</h2>
          </div>
          <Link href="/app/queries" className="text-[11px] text-accent">All queries →</Link>
        </div>
        <div className="mt-3 grid gap-2">
          {recent.length ? recent.map((query) => (
            <button
              key={query.query_id}
              type="button"
              onClick={() => { setInput(query.tx_hash ?? ""); setTx(query.tx_hash ?? ""); }}
              className="flex flex-col justify-between gap-2 rounded-xl border border-line bg-panel-2 p-3 text-left transition-colors hover:border-line-bright sm:flex-row sm:items-center"
            >
              <div>
                <p className="text-xs font-semibold">#{query.query_id} · {query.dataset_id}</p>
                <p className="mt-1 font-mono text-[10px] text-faint">{short(query.tx_hash, 22, 12)}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="pill pill-accent">PROVEN</span>
                <span className="text-[10px] text-faint">verify →</span>
              </div>
            </button>
          )) : (
            <p className="text-xs text-muted">No proof-bearing queries in the recent window yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}
