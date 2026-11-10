"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import type { QueryRecord } from "@/lib/types";
import { explorerTx, statusTone } from "@/lib/format";
import { cn } from "@/lib/utils";
import { EmptyState } from "@/components/ui/primitives";

export function QueryHistory({ queries, limit = 8 }: { queries: QueryRecord[]; limit?: number }) {
  if (!queries.length) {
    return (
      <EmptyState
        title="No queries yet"
        description="Run an approved computation from the agent console. Real testnet queries will appear here with their proof and settlement links."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="data-table">
        <thead>
          <tr>
            <th>Query</th>
            <th>Dataset</th>
            <th>Status</th>
            <th>Block</th>
            <th className="text-right">Links</th>
          </tr>
        </thead>
        <tbody>
          {queries
            .slice()
            .reverse()
            .slice(0, limit)
            .map((query) => (
              <tr key={query.query_id}>
                <td>
                  <Link href={`/app/queries/${query.query_id}`} className="font-mono text-xs text-accent hover:underline">
                    #{query.query_id}
                  </Link>
                </td>
                <td>
                  <span className="text-xs">{query.dataset_id}</span>
                  <span className="ml-2 text-[10px] text-faint">{query.computation_id}</span>
                </td>
                <td>
                  <span className={cn("pill", statusTone(query.status) === "accent" && "pill-accent", statusTone(query.status) === "warning" && "pill-warning", statusTone(query.status) === "danger" && "pill-danger")}>
                    {query.status}
                  </span>
                </td>
                <td className="font-mono text-[10px] text-faint">{query.created_block}</td>
                <td>
                  <div className="flex justify-end gap-2 text-[10px]">
                    {query.tx_hash ? (
                      <a className="text-accent hover:underline" href={explorerTx(query.tx_hash)} target="_blank" rel="noreferrer">
                        request
                      </a>
                    ) : null}
                    {query.accept_tx ? (
                      <a className="text-accent hover:underline" href={explorerTx(query.accept_tx)} target="_blank" rel="noreferrer">
                        accept
                      </a>
                    ) : null}
                    {query.refund_tx ? (
                      <a className="text-warning hover:underline" href={explorerTx(query.refund_tx)} target="_blank" rel="noreferrer">
                        refund
                      </a>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
        </tbody>
      </table>
      <div className="mt-3 flex items-center justify-between">
        <p className="text-[11px] text-faint">Showing the latest {Math.min(limit, queries.length)} query records.</p>
        <Link href="/app/queries" className="inline-flex items-center gap-1 text-[11px] text-accent">
          All queries <ArrowUpRight size={11} />
        </Link>
      </div>
    </div>
  );
}
