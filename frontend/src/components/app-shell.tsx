"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  Bot,
  Building2,
  Database,
  FileKey,
  History,
  LayoutDashboard,
  Lock,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandMark } from "@/components/brand-mark";
import { api } from "@/lib/api";
import { short } from "@/lib/format";
import { cn } from "@/lib/utils";

const primary = [
  { href: "/app", label: "Overview", icon: LayoutDashboard },
  { href: "/app/datasets", label: "Datasets", icon: Database },
  { href: "/app/queries", label: "Queries", icon: History },
  { href: "/app/proofs", label: "Proofs", icon: ShieldCheck },
  { href: "/app/owner", label: "Owner", icon: Building2 },
  { href: "/app/agent", label: "Agent", icon: Bot },
];

const secondary = [
  { href: "/docs", label: "Docs", icon: BookOpen },
  { href: "/security", label: "Security", icon: Lock },
  { href: "/status", label: "Status", icon: Activity },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data, isError } = useQuery({ queryKey: ["state"], queryFn: api.state, refetchInterval: 20_000 });
  const networkLabel = isError ? "Unavailable" : !data ? "Connecting" : data.paused ? "Paused" : "Live";
  const networkClass = isError || data?.paused ? "pill-danger" : data ? "pill-accent" : "pill-warning";

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-[1560px]">
        <aside className="sticky top-0 hidden h-screen w-[248px] shrink-0 border-r border-line px-4 py-5 lg:flex lg:flex-col">
          <Link href="/" className="flex items-center gap-3 px-2">
            <BrandMark />
            <span className="leading-tight">
              <span className="block text-sm font-bold">SealQuery</span>
              <span className="block text-[10px] uppercase tracking-[0.16em] text-faint">Testnet app</span>
            </span>
          </Link>

          <div className="mt-7">
            <p className="metric-label px-2">Workspace</p>
            <nav className="mt-2 grid gap-1">
              {primary.map((item) => (
                <NavItem key={item.href} {...item} pathname={pathname} />
              ))}
            </nav>
          </div>

          <div className="mt-7">
            <p className="metric-label px-2">Resources</p>
            <nav className="mt-2 grid gap-1">
              {secondary.map((item) => (
                <NavItem key={item.href} {...item} pathname={pathname} />
              ))}
            </nav>
          </div>

          <div className="mt-auto rounded-2xl border border-line bg-panel-2 p-3">
            <div className="flex items-center justify-between">
              <span className="metric-label">Network</span>
              <span className={cn("pill", networkClass)}>
                {networkLabel}
              </span>
            </div>
            <p className="mt-2 truncate font-mono text-[10px] text-muted" title={data?.contract}>
              {short(data?.contract, 12, 8)}
            </p>
            <Link href="/status" className="mt-3 inline-flex items-center gap-1 text-[11px] text-accent">
              Network status <ArrowUpRight size={11} />
            </Link>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-30 border-b border-line bg-background/85 backdrop-blur-xl">
            <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
              <div className="flex min-w-0 items-center gap-3">
                <Link href="/" aria-label="SealQuery home" className="lg:hidden">
                  <BrandMark />
                </Link>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">Agent workspace</p>
                  <p className="truncate text-[11px] text-muted">
                    {isError
                      ? "agent unavailable"
                      : data?.agent
                        ? `agent ${short(data.agent, 12, 8)}`
                        : "connecting to testnet…"}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="pill hidden sm:inline-flex">
                  <span className="live-dot" /> NEAR testnet
                </span>
                <Link href="/docs#api" className="btn btn-ghost btn-sm hidden sm:inline-flex">
                  <FileKey size={13} /> API
                </Link>
                <Link href="/app" className="btn btn-primary btn-sm">
                  New query
                </Link>
              </div>
            </div>
            <nav className="flex gap-1 overflow-x-auto px-3 pb-2 lg:hidden">
              {primary.map((item) => (
                <NavItem key={item.href} {...item} pathname={pathname} compact />
              ))}
            </nav>
          </header>

          <main className="px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>

          <footer className="border-t border-line px-4 py-5 text-[11px] text-faint sm:px-6 lg:px-8">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span>SealQuery testnet prototype · no raw data leaves the enclave</span>
              <span className="font-mono">{short(data?.contract, 18, 10)}</span>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}

function NavItem({
  href,
  label,
  icon: Icon,
  pathname,
  compact = false,
}: {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  pathname: string;
  compact?: boolean;
}) {
  const active = href === "/app" ? pathname === "/app" : pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors",
        compact && "shrink-0 px-2.5 py-1.5 text-[12px]",
        active ? "bg-panel-2 text-ink" : "text-muted hover:bg-panel-2 hover:text-ink",
      )}
    >
      <Icon size={compact ? 13 : 15} className={active ? "text-accent" : ""} />
      {label}
    </Link>
  );
}
