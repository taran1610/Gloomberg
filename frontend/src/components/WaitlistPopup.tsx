"use client";

import { useState, useEffect } from "react";

const STORAGE_KEY = "gloomberg_waitlist_popup";

export default function WaitlistPopup() {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const dismissed = sessionStorage.getItem(STORAGE_KEY);
    if (dismissed) return;
    const t = setTimeout(() => setOpen(true), 5000);
    return () => clearTimeout(t);
  }, []);

  const close = () => {
    setOpen(false);
    if (typeof window !== "undefined") sessionStorage.setItem(STORAGE_KEY, "1");
  };

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
      setTimeout(() => {
        close();
      }, 1500);
    } catch {
      setStatus("error");
      setMessage("Network error. Please try again.");
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6">
      <div className="w-full max-w-2xl border-2 border-term-orange bg-term-bg shadow-lg">
        <div className="flex items-center justify-between border-b border-term-border px-6 py-4 bg-term-panel">
          <span className="text-term-orange font-bold text-lg">JOIN THE WAITLIST</span>
          <button
            type="button"
            onClick={close}
            className="text-term-dim hover:text-term-white text-2xl leading-none transition-colors"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="p-8">
          <p className="text-term-muted text-sm mb-6 leading-relaxed">
            Get early access to Gloomberg — Bloomberg-style terminal for retail traders.
          </p>
          {status === "success" ? (
            <p className="text-term-green text-base font-medium">{message}</p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                disabled={status === "loading"}
                className="w-full px-4 py-3 bg-term-black border border-term-border text-term-white text-base placeholder:text-term-dim focus:border-term-orange transition-colors"
                autoFocus
              />
              {message && status === "error" && (
                <p className="text-term-red text-sm">{message}</p>
              )}
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={status === "loading"}
                  className="flex-1 py-3 bg-term-orange text-term-black font-bold text-sm hover:bg-term-orange-dim disabled:opacity-50 transition-colors"
                >
                  {status === "loading" ? "JOINING..." : "JOIN"}
                </button>
                <button
                  type="button"
                  onClick={close}
                  className="px-5 py-3 border border-term-border text-term-muted text-sm hover:text-term-white transition-colors"
                >
                  Maybe later
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
