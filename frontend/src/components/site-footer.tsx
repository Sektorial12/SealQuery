import Link from "next/link";
import { BrandMark } from "@/components/brand-mark";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto grid w-full max-w-[1240px] gap-10 px-5 py-12 sm:px-8 md:grid-cols-[1.2fr_2fr]">
        <div>
          <div className="flex items-center gap-3">
            <BrandMark />
            <span className="text-sm font-bold">SealQuery</span>
          </div>
          <p className="mt-4 max-w-sm text-xs leading-6 text-muted">
            Sell the answer, not the dataset. Approved computations over private data, executed in
            Intel TDX, verified with OutLayer, and settled on NEAR.
          </p>
          <p className="mt-4 text-[11px] text-faint">
            Open-source testnet prototype. Not a production security audit.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-8 text-sm sm:grid-cols-4">
          <FooterColumn title="Product">
            <Link href="/app">Agent console</Link>
            <Link href="/app/datasets">Datasets</Link>
            <Link href="/app/proofs">Proof explorer</Link>
            <Link href="/pricing">Pricing</Link>
          </FooterColumn>
          <FooterColumn title="Build">
            <Link href="/docs">Docs</Link>
            <Link href="/docs#api">API</Link>
            <Link href="/docs#mcp">MCP</Link>
            <Link href="/status">Status</Link>
          </FooterColumn>
          <FooterColumn title="Trust">
            <Link href="/security">Security</Link>
            <Link href="/app/proofs">Attestations</Link>
            <Link href="/docs#contract">Contract</Link>
          </FooterColumn>
          <FooterColumn title="Network">
            <a href="https://testnet.near.org" target="_blank" rel="noreferrer">NEAR testnet</a>
            <a href="https://outlayer.ai" target="_blank" rel="noreferrer">OutLayer</a>
            <a href="https://github.com" target="_blank" rel="noreferrer">GitHub</a>
          </FooterColumn>
        </div>
      </div>
      <div className="border-t border-line px-5 py-5 text-center text-[11px] text-faint sm:px-8">
        MIT licensed · Testnet only · No raw data leaves the enclave
      </div>
    </footer>
  );
}

function FooterColumn({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="metric-label mb-3">{title}</p>
      <div className="grid gap-2.5 text-xs text-muted [&_a:hover]:text-ink">{children}</div>
    </div>
  );
}
