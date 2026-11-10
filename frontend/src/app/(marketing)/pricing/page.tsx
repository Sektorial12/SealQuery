"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Calculator, Check, Coins, ReceiptText } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { SectionHeading, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { formatNear } from "@/lib/format";

export default function PricingPage() {
  const { data: state, isLoading } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const [selected, setSelected] = useState(0);
  const [count, setCount] = useState(10);

  if (isLoading) return <div className="mx-auto max-w-[1240px] px-5 py-16 sm:px-8"><Skeleton className="h-96" /></div>;
  const datasets = state?.datasets ?? [];
  const entry = datasets[selected] ?? datasets[0];
  const bps = state?.protocol_fee_bps ?? 0;

  const price = entry ? BigInt(entry.quote.price_yocto) : 0n;
  const reward = entry ? BigInt(entry.dataset.reward_yocto) : 0n;
  const compute = entry ? BigInt(entry.dataset.compute_deposit_yocto) : 0n;
  const feePerQuery = (reward * BigInt(bps)) / 10_000n;
  const total = price * BigInt(count);
  const ownerGross = reward * BigInt(count);
  const ownerNet = (reward - feePerQuery) * BigInt(count);
  const computeTotal = compute * BigInt(count);
  const protocolFee = feePerQuery * BigInt(count);

  return (
    <div className="mx-auto w-full max-w-[1240px] px-5 py-14 sm:px-8">
      <SectionHeading
        eyebrow="Pricing"
        title="Pay for the answer, not the dataset."
        description="Each dataset sets its own per-query price. The contract separates the compute deposit, the owner reward, and an optional protocol fee. Failed or rejected queries are refunded."
      />

      <div className="mt-10 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="panel p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <Coins size={16} className="text-accent" />
            <h2 className="text-lg font-semibold">Dataset pricing</h2>
          </div>
          <div className="mt-4 grid gap-2">
            {datasets.map((item, index) => (
              <button
                key={item.dataset_id}
                type="button"
                onClick={() => setSelected(index)}
                className={`rounded-xl border p-3 text-left transition-colors ${index === selected ? "border-accent/50 bg-accent/[0.05]" : "border-line bg-panel-2 hover:border-line-bright"}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">{item.dataset_id}</span>
                  <span className="text-xs font-semibold text-accent">{formatNear(item.quote.price_yocto)} NEAR</span>
                </div>
                <p className="mt-1 text-[10px] text-faint">
                  {item.computation_id} · owner reward {formatNear(item.dataset.reward_yocto)} NEAR · budget {item.dataset.budget_per_day}/day
                </p>
              </button>
            ))}
          </div>

          <div className="mt-5 grid gap-2">
            <PriceRow label="Compute deposit" value={`${formatNear(compute.toString())} NEAR`} />
            <PriceRow label="Owner reward" value={`${formatNear(reward.toString())} NEAR`} />
            <PriceRow label={`Protocol fee (${bps} bps)`} value={`${formatNear(feePerQuery.toString())} NEAR`} />
            <div className="border-t border-line pt-2">
              <PriceRow label="Agent pays" value={`${formatNear(price.toString())} NEAR`} strong />
            </div>
          </div>
        </section>

        <section className="panel p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <Calculator size={16} className="text-accent" />
            <h2 className="text-lg font-semibold">Query calculator</h2>
          </div>
          <p className="mt-2 text-xs leading-6 text-muted">
            Estimate the testnet split for a batch of accepted queries. Protocol fees are applied to the
            owner reward, not the compute deposit.
          </p>

          <div className="mt-5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted">Queries</span>
              <span className="font-mono text-accent">{count}</span>
            </div>
            <input
              type="range"
              min={1}
              max={100}
              value={count}
              onChange={(event) => setCount(Number(event.target.value))}
              className="mt-2 w-full accent-[#6ef2c8]"
            />
            <div className="mt-1 flex justify-between text-[10px] text-faint"><span>1</span><span>100</span></div>
          </div>

          <div className="mt-5 grid gap-2">
            <PriceRow label="Agent spend" value={`${formatNear(total.toString())} NEAR`} strong />
            <PriceRow label="Compute budget" value={`${formatNear(computeTotal.toString())} NEAR`} />
            <PriceRow label="Owner gross" value={`${formatNear(ownerGross.toString())} NEAR`} />
            <PriceRow label="Protocol fee" value={`${formatNear(protocolFee.toString())} NEAR`} />
            <PriceRow label="Owner net" value={`${formatNear(ownerNet.toString())} NEAR`} strong />
          </div>

          <div className="mt-5 rounded-xl border border-line bg-panel-2 p-3 text-[11px] leading-6 text-muted">
            <p className="flex items-center gap-1.5 text-accent"><Check size={12} /> Testnet NEAR only</p>
            <p className="mt-1">No token, no subscription, no seat fee. The daily privacy budget and per-query price are enforced by the contract.</p>
          </div>

          <Link href="/app" className="btn btn-primary mt-5">Run a query <ArrowRight size={15} /></Link>
        </section>
      </div>

      <section className="mt-5 grid gap-3 md:grid-cols-3">
        <Feature icon={ReceiptText} title="Owner-set price" text="The publisher chooses the economics for each dataset and version." />
        <Feature icon={Coins} title="Visible split" text="Compute deposit, owner reward, and protocol fee are shown before execution." />
        <Feature icon={Check} title="Refund on failure" text="Rejected or failed queries return the agent deposit instead of silently failing." />
      </section>
    </div>
  );
}

function PriceRow({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 text-xs">
      <span className="text-muted">{label}</span>
      <span className={strong ? "font-mono font-semibold text-accent" : "font-mono text-ink"}>{value}</span>
    </div>
  );
}

function Feature({ icon: Icon, title, text }: { icon: React.ComponentType<{ size?: number; className?: string }>; title: string; text: string }) {
  return (
    <div className="panel p-5">
      <Icon size={16} className="text-accent" />
      <p className="mt-3 text-sm font-semibold">{title}</p>
      <p className="mt-1 text-[11px] leading-6 text-muted">{text}</p>
    </div>
  );
}
