import {
  ArrowRight,
  BadgeCheck,
  Bot,
  Building2,
  Check,
  Cpu,
  EyeOff,
  Fingerprint,
  LockKeyhole,
  Network,
  ShieldCheck,
  Sparkles,
  Wallet,
} from "lucide-react";
import Link from "next/link";
import { LatestProof } from "@/components/latest-proof";
import { LiveStats } from "@/components/live-stats";
import { SectionHeading } from "@/components/ui/primitives";

export default function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden border-b border-line">
        <div className="absolute inset-0 bg-grid" />
        <div className="absolute inset-0 hero-glow" />
        <div className="relative mx-auto grid w-full max-w-[1240px] gap-12 px-5 pb-16 pt-16 sm:px-8 lg:grid-cols-[1.1fr_0.9fr] lg:pt-24">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="pill pill-accent"><span className="live-dot bg-[#06110d]" /> NEAR testnet live</span>
              <span className="pill">Intel TDX · OutLayer verified</span>
            </div>
            <h1 className="display mt-7 max-w-3xl text-[clamp(3rem,7vw,6.2rem)] font-semibold">
              Sell the answer.
              <br />
              <span className="text-accent">Not the dataset.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-8 text-muted">
              AI agents pay for approved computations over private data. The job runs inside Intel TDX,
              returns only the aggregate, and comes back with a cryptographic receipt. The data owner
              gets paid. The agent never sees the rows.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/app" className="btn btn-primary">
                Launch the agent console <ArrowRight size={15} />
              </Link>
              <Link href="/docs" className="btn btn-ghost">Read the quickstart</Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-[11px] text-faint">
              <span className="flex items-center gap-1.5"><Check size={12} className="text-accent" /> on-chain escrow</span>
              <span className="flex items-center gap-1.5"><Check size={12} className="text-accent" /> TDX attestation</span>
              <span className="flex items-center gap-1.5"><Check size={12} className="text-accent" /> raw rows never leave</span>
            </div>
          </div>

          <div className="relative flex items-center">
            <div className="absolute -inset-8 rounded-full bg-accent/10 blur-3xl" />
            <div className="relative w-full rounded-2xl border border-line bg-panel/90 p-4 shadow-2xl backdrop-blur">
              <div className="flex items-center justify-between border-b border-line pb-3">
                <div className="flex items-center gap-2 text-xs font-semibold"><Network size={14} className="text-accent" /> Query receipt</div>
                <span className="pill pill-accent">PROVEN</span>
              </div>
              <div className="mt-4 grid gap-2 text-[11px]">
                <ReceiptRow label="Dataset" value="retail_v1 · private" />
                <ReceiptRow label="Computation" value="spend_growth · approved" />
                <ReceiptRow label="Execution" value="Intel TDX · OutLayer" />
                <ReceiptRow label="Result" value="aggregate only · canary absent" />
                <ReceiptRow label="Settlement" value="owner paid on acceptance" />
              </div>
              <div className="mt-4 rounded-xl border border-line bg-[#080c10] p-3">
                <div className="flex items-center justify-between text-[10px] text-faint"><span>Verification layers</span><span>5 / 5</span></div>
                <div className="mt-2 grid gap-1.5">
                  {["authenticity", "identity", "binding", "input", "output"].map((name) => (
                    <div key={name} className="flex items-center justify-between text-[10px]">
                      <span className="text-muted">{name}</span>
                      <span className="flex items-center gap-1 font-mono text-accent"><Check size={10} /> pass</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-[10px] text-faint">
                <span>task 30170 · TCB UpToDate</span>
                <Link href="/app/proofs" className="text-accent">open proof explorer →</Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-[1240px] px-5 py-10 sm:px-8">
        <div className="mb-3 flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Live network</p>
            <p className="mt-1 text-xs text-muted">A real testnet snapshot, not a mock.</p>
          </div>
          <Link href="/status" className="text-[11px] text-accent">Full status →</Link>
        </div>
        <LiveStats />
      </section>

      <section className="mx-auto w-full max-w-[1240px] px-5 py-12 sm:px-8">
        <div className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="panel p-6 sm:p-8">
            <p className="eyebrow">The loop</p>
            <SectionHeading
              title="A private dataset. A paid answer. A verifiable receipt."
              description="SealQuery turns data access into a metered computation. The owner defines what can run and at what price. The agent pays on-chain. The enclave executes the approved code and the agent verifies the proof before payment settles."
            />
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              <Step icon={Wallet} number="01" title="Pay on-chain" text="The agent escrows the query price in the NEAR contract." />
              <Step icon={Cpu} number="02" title="Compute in TDX" text="OutLayer runs the approved WASM over the private dataset." />
              <Step icon={Fingerprint} number="03" title="Verify the proof" text="The agent checks the TDX report, measurements, and I/O binding." />
              <Step icon={BadgeCheck} number="04" title="Settle the owner" text="Acceptance releases the owner reward; failure refunds the agent." />
            </div>
          </div>
          <LatestProof />
        </div>
      </section>

      <section className="border-y border-line bg-panel/40">
        <div className="mx-auto w-full max-w-[1240px] px-5 py-16 sm:px-8">
          <SectionHeading
            eyebrow="Why SealQuery"
            title="Data utility without data exposure."
            description="The most valuable datasets cannot be copied, shipped, or pasted into a prompt. SealQuery lets agents buy the smallest useful thing: a computed answer with provenance."
          />
          <div className="mt-10 grid gap-3 md:grid-cols-3">
            <Value icon={Building2} title="For data owners" text="Set the price, allowed computations, daily budget, and version. Keep the raw data inside encrypted storage. Get paid per accepted answer." />
            <Value icon={Bot} title="For agent builders" text="One REST or MCP call. Get an aggregate, a proof, and a settlement receipt without building a data pipeline or a TEE stack." />
            <Value icon={ShieldCheck} title="For verifiers" text="Every result has a task ID, TDX measurements, five pass/fail checks, transaction links, and a downloadable bundle that verifies offline." />
          </div>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-[1240px] gap-5 px-5 py-16 sm:px-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="panel p-6 sm:p-8">
          <p className="eyebrow">Privacy by construction</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">What the agent never gets</h2>
          <p className="mt-4 text-sm leading-7 text-muted">
            The approved WASM is the only code allowed to read the dataset. The result is an aggregate:
            minimum cohort 100, rounded spend and growth, suppressed small cohorts, and a canary row that
            must never appear.
          </p>
          <div className="mt-6 grid gap-2">
            {[
              ["Raw rows", "Stay in encrypted worker storage; never delivered."],
              ["Small cohorts", "Suppressed below the minimum cohort size."],
              ["Unlimited probing", "Per-agent, per-dataset daily budget."],
              ["Unapproved code", "Compute secret is locked to the contract."],
            ].map(([title, text]) => (
              <div key={title} className="flex gap-3 rounded-lg border border-line bg-panel-2 p-3">
                <EyeOff size={14} className="mt-0.5 shrink-0 text-accent" />
                <div>
                  <p className="text-xs font-semibold">{title}</p>
                  <p className="mt-0.5 text-[11px] leading-5 text-muted">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="panel flex flex-col justify-between overflow-hidden p-6 sm:p-8">
          <div>
            <p className="eyebrow">Economics</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.035em]">Priced per answer, not per seat.</h2>
            <p className="mt-4 max-w-lg text-sm leading-7 text-muted">
              The owner sets a query price. The contract separates the compute deposit, the owner reward,
              and an optional protocol fee. Failed or rejected queries refund the agent. No token is
              required to use the testnet.
            </p>
          </div>
          <div className="mt-8 grid gap-2 sm:grid-cols-3">
            <Econ label="Query price" value="owner-set" />
            <Econ label="Settlement" value="on acceptance" />
            <Econ label="Failure" value="refunded" />
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            <Link href="/pricing" className="btn btn-ghost btn-sm">See pricing <ArrowRight size={13} /></Link>
            <Link href="/security" className="btn btn-ghost btn-sm">Read the threat model</Link>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-[1240px] px-5 pb-20 sm:px-8">
        <div className="relative overflow-hidden rounded-3xl border border-accent/20 bg-gradient-to-br from-accent/[0.10] via-panel to-accent-2/[0.08] p-8 sm:p-12">
          <div className="absolute right-0 top-0 size-72 rounded-full bg-accent/10 blur-3xl" />
          <div className="relative max-w-2xl">
            <div className="flex items-center gap-2 text-accent"><Sparkles size={16} /><span className="text-[11px] font-bold uppercase tracking-[0.18em]">Testnet production prototype</span></div>
            <h2 className="mt-4 text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">Run the full loop on NEAR testnet.</h2>
            <p className="mt-3 text-sm leading-7 text-muted">
              Start with the agent console, inspect a real proof, then download the bundle and verify it
              offline. The rejected-query path is one click away.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/app" className="btn btn-primary">Open agent console <ArrowRight size={15} /></Link>
              <Link href="/app/proofs" className="btn btn-ghost"><LockKeyhole size={14} /> Verify a proof</Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

function ReceiptRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-line bg-panel-2 px-3 py-2">
      <span className="text-muted">{label}</span>
      <span className="text-right font-mono text-[10px] text-ink">{value}</span>
    </div>
  );
}

function Step({ icon: Icon, number, title, text }: { icon: React.ComponentType<{ size?: number; className?: string }>; number: string; title: string; text: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel-2 p-4">
      <div className="flex items-center justify-between">
        <Icon size={16} className="text-accent" />
        <span className="font-mono text-[10px] text-faint">{number}</span>
      </div>
      <p className="mt-3 text-sm font-semibold">{title}</p>
      <p className="mt-1 text-[11px] leading-5 text-muted">{text}</p>
    </div>
  );
}

function Value({ icon: Icon, title, text }: { icon: React.ComponentType<{ size?: number; className?: string }>; title: string; text: string }) {
  return (
    <div className="panel p-5">
      <Icon size={18} className="text-accent" />
      <h3 className="mt-4 text-sm font-semibold">{title}</h3>
      <p className="mt-2 text-xs leading-6 text-muted">{text}</p>
    </div>
  );
}

function Econ({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel-2 p-4">
      <p className="metric-label text-[9px]">{label}</p>
      <p className="mt-1 text-sm font-semibold text-accent">{value}</p>
    </div>
  );
}
