"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  LineChart,
  FlaskConical,
  Search,
  Terminal,
  Microscope,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/research", label: "Deep Research", icon: Microscope },
  { href: "/strategy", label: "Strategy Lab", icon: FlaskConical },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [query, setQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/asset/${query.trim().toUpperCase()}`);
      setQuery("");
    }
  };

  return (
    <aside className="w-64 h-screen bg-gloom-surface border-r border-gloom-border flex flex-col fixed left-0 top-0 z-50">
      <div className="p-5 border-b border-gloom-border">
        <Link href="/" className="flex items-center gap-2.5">
          <Terminal className="w-6 h-6 text-gloom-orange" />
          <span className="text-xl font-bold tracking-tight">
            <span className="text-gloom-orange">GLOOM</span>
            <span className="text-gloom-text">BERG</span>
          </span>
        </Link>
        <p className="text-[10px] text-gloom-muted mt-1 uppercase tracking-widest">
          Financial Intelligence Terminal
        </p>
      </div>

      <form onSubmit={handleSearch} className="p-3 border-b border-gloom-border">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gloom-muted" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search ticker..."
            className="w-full bg-gloom-bg border border-gloom-border rounded-md pl-9 pr-3 py-2 text-sm text-gloom-text placeholder:text-gloom-muted focus:outline-none focus:border-gloom-orange transition-colors"
          />
        </div>
      </form>

      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                active
                  ? "bg-gloom-orange/10 text-gloom-orange border border-gloom-orange/20"
                  : "text-gloom-muted hover:text-gloom-text hover:bg-gloom-hover"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}

        <div className="pt-4 pb-2">
          <p className="text-[10px] text-gloom-muted uppercase tracking-widest px-3">
            Quick Access
          </p>
        </div>
        {["AAPL", "NVDA", "MSFT", "TSLA", "BTC-USD"].map((t) => (
          <Link
            key={t}
            href={`/asset/${t}`}
            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
              pathname === `/asset/${t}`
                ? "bg-gloom-blue/10 text-gloom-blue"
                : "text-gloom-muted hover:text-gloom-text hover:bg-gloom-hover"
            }`}
          >
            <LineChart className="w-3.5 h-3.5" />
            {t}
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-gloom-border">
        <div className="text-[10px] text-gloom-muted">
          <p>Gloomberg Terminal v0.1</p>
          <p className="mt-0.5">Data: Yahoo Finance</p>
        </div>
      </div>
    </aside>
  );
}
