"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { BrandMark } from "@/components/brand-mark";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Product" },
  { href: "/app/datasets", label: "Datasets" },
  { href: "/app/proofs", label: "Proofs" },
  { href: "/pricing", label: "Pricing" },
  { href: "/docs", label: "Docs" },
  { href: "/security", label: "Security" },
  { href: "/status", label: "Status" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-[1240px] items-center justify-between gap-4 px-5 sm:px-8">
        <Link href="/" className="flex items-center gap-3">
          <BrandMark />
          <span className="leading-tight">
            <span className="block text-sm font-bold tracking-[-0.02em]">SealQuery</span>
            <span className="hidden text-[11px] text-muted sm:block">Private data compute for AI agents</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex">
          {nav.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-lg px-3 py-2 text-[13px] font-medium transition-colors",
                  active ? "bg-panel-2 text-ink" : "text-muted hover:bg-panel-2 hover:text-ink",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <span className="pill hidden xl:inline-flex">
            <span className="live-dot" /> NEAR testnet
          </span>
          <Link href="/app" className="btn btn-primary btn-sm hidden sm:inline-flex">
            Launch app
          </Link>
          <button
            type="button"
            className="btn btn-ghost btn-sm lg:hidden"
            aria-label="Open menu"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {open ? (
        <div className="border-t border-line bg-background px-5 pb-5 pt-3 lg:hidden">
          <div className="grid gap-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm text-muted hover:bg-panel-2 hover:text-ink"
              >
                {item.label}
              </Link>
            ))}
            <Link href="/app" onClick={() => setOpen(false)} className="btn btn-primary mt-3">
              Launch app
            </Link>
          </div>
        </div>
      ) : null}
    </header>
  );
}
