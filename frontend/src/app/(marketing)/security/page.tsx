import {
  ArrowRight,
  Check,
  Cpu,
  EyeOff,
  Fingerprint,
  KeyRound,
  LockKeyhole,
  ShieldAlert,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import Link from "next/link";
import { SectionHeading } from "@/components/ui/primitives";

const threats = [
  ["Inference / reconstruction", "Daily budget, minimum cohort, rounding, suppressed cohorts, and a canary row. No differential privacy yet."],
  ["Output leakage", "Only the approved aggregate leaves the enclave. The canary must never appear in a result or agent log."],
  ["Unauthorized code", "The contract allowlists dataset computations; the compute secret is locked to the contract predecessor."],
  ["Sybil querying", "Budget is per NEAR account. Testnet accounts are cheap; production needs identity, stake, or cross-account budgets."],
  ["TEE / OutLayer compromise", "TDX quote, collateral, TCB status, measurement approval, and I/O binding are verified off-chain. OutLayer governance and worker registration remain trusted."],
  ["Callback / replay", "Result acceptance is bound to the query, only the requesting agent can accept, and replay/duplicate-settlement tests fail safely."],
  ["Infrastructure outage", "Pause, refunds, retries, monitoring, runbooks, and an incident drill are in place. Single-process API and public RPC remain risks."],
];

export default function SecurityPage() {
  return (
    <div className="mx-auto w-full max-w-[1240px] px-5 py-14 sm:px-8">
      <SectionHeading
        eyebrow="Security and trust"
        title="The proof is the product."
        description="SealQuery separates what the TEE proves, what the contract enforces, and what the operator still controls. This page states all three."
      />

      <div className="mt-10 grid gap-3 md:grid-cols-3">
        <TrustCard icon={Cpu} title="TEE execution" text="Approved WASM runs inside Intel TDX on OutLayer. The dataset is readable only by that code." />
        <TrustCard icon={Fingerprint} title="Attestation" text="The verifier checks authenticity, worker identity, result binding, input, output, TCB status, and measurements." />
        <TrustCard icon={LockKeyhole} title="On-chain settlement" text="Escrow, budgets, acceptance, and refunds live in the NEAR contract — not in a trusted backend." />
      </div>

      <section className="panel mt-5 p-6 sm:p-8">
        <div className="flex items-center gap-2">
          <ShieldCheck size={18} className="text-accent" />
          <h2 className="text-xl font-semibold">Attestation, not a promise</h2>
        </div>
        <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_0.9fr]">
          <div className="space-y-3 text-sm leading-7 text-muted">
            <p>
              A successful query produces an OutLayer task and a TDX report. The agent runs
              <code className="mx-1 rounded bg-panel-2 px-1.5 py-0.5 font-mono text-xs text-accent">outlayer-verify</code>
              before calling <code className="rounded bg-panel-2 px-1.5 py-0.5 font-mono text-xs text-accent">accept_result</code>.
              Payment is not released on an unverified result.
            </p>
            <p>
              The proof bundle can be downloaded and checked offline. Verification includes the Intel signature chain,
              worker measurement approval, the task fields committed in report data, and the input/output hashes.
            </p>
            <p className="rounded-xl border border-warning/25 bg-warning/[0.05] p-3 text-xs text-warning">
              The TEE proves which code ran on which input and output. It does not prove the computation is semantically
              correct, and the contract does not verify TDX quotes on-chain.
            </p>
          </div>
          <div className="code-block">
{`outlayer-verify tx <near-tx-hash> \\
  --network testnet \\
  --api https://testnet-api.outlayer.ai \\
  --json

# every layer must pass:
# authenticity, identity, binding, input, output

outlayer-verify bundle proof.json --offline --short
# PROVEN task <id> (execute) ...`}
          </div>
        </div>
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="panel p-6">
          <div className="flex items-center gap-2">
            <ShieldAlert size={17} className="text-warning" />
            <h2 className="text-lg font-semibold">Threat model</h2>
          </div>
          <div className="mt-4 grid gap-2">
            {threats.map(([title, text]) => (
              <div key={title} className="rounded-xl border border-line bg-panel-2 p-3">
                <p className="text-xs font-semibold">{title}</p>
                <p className="mt-1 text-[11px] leading-5 text-muted">{text}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="panel p-6">
            <div className="flex items-center gap-2">
              <EyeOff size={17} className="text-accent" />
              <h2 className="text-lg font-semibold">Privacy controls</h2>
            </div>
            <ul className="mt-4 grid gap-2 text-xs leading-6 text-muted">
              {["Minimum cohort 100", "Spend rounded to 1,000", "Growth rounded to 0.1%", "Cohort counts suppressed", "20 queries per agent / dataset / day", "Canary row must never appear"].map((item) => (
                <li key={item} className="flex items-center gap-2"><Check size={12} className="text-accent" /> {item}</li>
              ))}
            </ul>
          </div>

          <div className="panel border-warning/25 p-6">
            <div className="flex items-center gap-2">
              <TriangleAlert size={17} className="text-warning" />
              <h2 className="text-lg font-semibold">Known limitations</h2>
            </div>
            <p className="mt-3 text-xs leading-6 text-muted">
              This is a testnet prototype. OutLayer governance is centralized, no differential privacy is
              implemented, testnet identities are cheap, and the demo API is single-process. See the
              threat model for the production gaps.
            </p>
            <Link href="/docs#limitations" className="mt-4 inline-flex items-center gap-1 text-[11px] text-accent">
              Read the detailed limitations <ArrowRight size={11} />
            </Link>
          </div>
        </div>
      </section>

      <section className="mt-5 panel flex flex-wrap items-center justify-between gap-4 p-6">
        <div>
          <p className="eyebrow">Try it</p>
          <h2 className="mt-2 text-lg font-semibold">Verify a real testnet proof.</h2>
          <p className="mt-1 text-xs text-muted">Open the proof explorer, paste a request transaction, and inspect every check.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/app/proofs" className="btn btn-primary btn-sm"><KeyRound size={13} /> Proof explorer</Link>
          <Link href="/status" className="btn btn-ghost btn-sm">Status</Link>
        </div>
      </section>
    </div>
  );
}

function TrustCard({ icon: Icon, title, text }: { icon: React.ComponentType<{ size?: number; className?: string }>; title: string; text: string }) {
  return (
    <div className="panel p-5">
      <Icon size={18} className="text-accent" />
      <h3 className="mt-3 text-sm font-semibold">{title}</h3>
      <p className="mt-1 text-[11px] leading-6 text-muted">{text}</p>
    </div>
  );
}
