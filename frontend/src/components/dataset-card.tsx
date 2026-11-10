"use client";

import { ArrowUpRight, Database } from "lucide-react";
import Link from "next/link";
import type { DatasetState } from "@/lib/types";
import { formatNear, short } from "@/lib/format";
import { cn } from "@/lib/utils";

export function DatasetTile({
  entry,
  selected = false,
  onSelect,
  href,
}: {
  entry: DatasetState;
  selected?: boolean;
  onSelect?: (entry: DatasetState) => void;
  href?: string;
}) {
  if (entry.error) {
    return (
      <div className="rounded-xl border border-danger/30 bg-danger/5 p-4 text-xs text-danger">
        {entry.dataset_id}: {entry.error}
      </div>
    );
  }

  const content = (
    <>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="grid size-8 place-items-center rounded-lg border border-line bg-panel-3 text-accent">
            <Database size={14} />
          </span>
          <div>
            <p className="text-sm font-semibold">{entry.dataset_id}</p>
            <p className="text-[10px] text-faint">v{entry.dataset.version} · {entry.computation.operation}</p>
          </div>
        </div>
        <span className="text-right text-xs font-semibold text-accent">{formatNear(entry.quote.price_yocto)} NEAR</span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-[11px]">
        <Meta label="Owner" value={short(entry.dataset.owner, 10, 8)} />
        <Meta label="Owner reward" value={`${formatNear(entry.dataset.reward_yocto)} NEAR`} />
        <Meta label="Budget" value={`${entry.budget.count}/${entry.dataset.budget_per_day}${entry.budget_exhausted ? " · exhausted" : " today"}`} />
        <Meta label="Dataset hash" value={short(entry.dataset.data_hash, 10, 8)} />
      </div>

      {href ? (
        <div className="mt-4 flex items-center justify-between text-[11px] text-faint">
          <span>Open dataset</span>
          <ArrowUpRight size={13} />
        </div>
      ) : null}
    </>
  );

  const className = cn(
    "w-full rounded-xl border p-4 text-left transition-all",
    selected
      ? "border-accent/50 bg-accent/[0.055] shadow-[0_0_0_1px_rgba(110,242,200,0.12)]"
      : "border-line bg-panel-2 hover:border-line-bright hover:bg-panel-3",
  );

  if (href) {
    return (
      <Link href={href} className={className}>
        {content}
      </Link>
    );
  }

  return (
    <button type="button" className={className} onClick={() => onSelect?.(entry)}>
      {content}
    </button>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="metric-label text-[9px]">{label}</p>
      <p className="mt-0.5 truncate font-mono text-[10px] text-muted">{value}</p>
    </div>
  );
}
