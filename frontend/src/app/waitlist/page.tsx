"use client";

import { useState } from "react";
import Link from "next/link";

export default function WaitlistPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("loading");
    setMessage("");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setStatus("error");
        setMessage(data.error || "Something went wrong.");
        return;
      }
      setStatus("success");
      setMessage(data.message || "You're on the list!");
      setEmail("");
    } catch {
      setStatus("error");
      setMessage("Network error. Please try again.");
    }
  };

  return (
    <div className="min-h-full flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-md border border-term-border bg-term-panel p-6">
        <div className="border-b border-term-border pb-3 mb-4">
          <h1 className="text-term-orange font-bold text-lg tracking-wide">
            JOIN THE WAITLIST
          </h1>
          <p className="text-term-muted text-xs mt-1">
            Get early access to Gloomberg — Bloomberg-style terminal for retail traders.
          </p>
        </div>

        {status === "success" ? (
          <div className="py-4">
            <p className="text-term-green text-sm font-medium">{message}</p>
            <p className="text-term-muted text-xxs mt-2">
              We&apos;ll notify you when we launch.
            </p>
            <Link
              href="/"
              className="inline-block mt-4 text-term-orange text-xs font-bold hover:underline"
            >
              &larr; Back to Dashboard
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-term-muted text-xxs uppercase mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                disabled={status === "loading"}
                className="w-full px-3 py-2 bg-term-black border border-term-border text-term-white text-sm placeholder:text-term-dim focus:border-term-orange transition-colors"
                autoComplete="email"
              />
            </div>
            {status === "error" && message && (
              <p className="text-term-red text-xs">{message}</p>
            )}
            <button
              type="submit"
              disabled={status === "loading"}
              className="w-full py-2 bg-term-orange text-term-black font-bold text-sm hover:bg-term-orange-dim disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {status === "loading" ? "JOINING..." : "JOIN WAITLIST"}
            </button>
          </form>
        )}

        <p className="text-term-dim text-xxs mt-4 pt-3 border-t border-term-border">
          No spam. Unsubscribe anytime.
        </p>
      </div>

      <Link
        href="/"
        className="mt-6 text-term-muted text-xxs hover:text-term-orange transition-colors"
      >
        &larr; Back to Gloomberg
      </Link>
    </div>
  );
}
