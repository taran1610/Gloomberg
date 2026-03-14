"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { createCheckout, createPortalSession, getBillingStatus } from "@/lib/api";
import Link from "next/link";

const TIERS = [
  {
    name: "FREE",
    price: "$0",
    period: "forever",
    features: [
      "Market dashboard & asset pages",
      "10 AI chat messages / day",
      "3 backtests / day",
      "Basic technical indicators",
    ],
    excluded: [
      "AI Strategy Generator",
      "Extended backtest windows",
      "Priority data refresh",
    ],
    plan: "free" as const,
  },
  {
    name: "PRO",
    price: "$29",
    period: "/month",
    features: [
      "Everything in Free, plus:",
      "200 AI chat messages / day",
      "50 backtests / day",
      "AI Strategy Generator",
      "All technical indicators",
      "Extended backtest windows (5yr+)",
      "Priority data refresh",
    ],
    excluded: [],
    plan: "pro" as const,
  },
];

function PricingContent() {
  const { user, refresh } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [billingConfigured, setBillingConfigured] = useState(false);
  const [checkingBilling, setCheckingBilling] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const success = searchParams.get("success") === "true";
  const canceled = searchParams.get("canceled") === "true";

  useEffect(() => {
    getBillingStatus()
      .then((s) => setBillingConfigured(s.configured))
      .catch(() => setBillingConfigured(false))
      .finally(() => setCheckingBilling(false));
  }, []);

  useEffect(() => {
    if (success && user) refresh();
  }, [success]);

  const handleUpgrade = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const { checkout_url } = await createCheckout();
      window.location.href = checkout_url;
    } catch (e: any) {
      setError(e.message || "Failed to start checkout");
    } finally {
      setLoading(false);
    }
  };

  const handlePortal = async () => {
    setLoading(true);
    setError("");
    try {
      const { portal_url } = await createPortalSession();
      window.location.href = portal_url;
    } catch (e: any) {
      setError(e.message || "Failed to open billing portal");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-term-orange font-bold text-lg mb-1">PLANS & PRICING</h1>
          <p className="text-term-dim text-xs">
            Upgrade to unlock the full power of Gloomberg Terminal
          </p>
        </div>

        {/* Success / Cancel banners */}
        {success && (
          <div className="mb-6 px-3 py-2 bg-term-green/10 border border-term-green/30 text-term-green text-xs text-center">
            Subscription activated. Welcome to Pro.
          </div>
        )}
        {canceled && (
          <div className="mb-6 px-3 py-2 bg-term-yellow/10 border border-term-yellow/30 text-term-yellow text-xs text-center">
            Checkout canceled. No charges were made.
          </div>
        )}

        {error && (
          <div className="mb-6 px-3 py-2 bg-term-red/10 border border-term-red/30 text-term-red text-xs text-center">
            {error}
          </div>
        )}

        {/* Usage banner for logged-in users */}
        {user && (
          <div className="mb-6 border border-term-border bg-term-bg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xxs text-term-muted uppercase">Your Plan</span>
              <span className={`text-xs font-bold px-2 py-0.5 ${
                user.plan === "pro"
                  ? "bg-term-orange/20 text-term-orange"
                  : "bg-term-surface text-term-muted"
              }`}>
                {user.plan.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-xxs text-term-dim">AI Messages</div>
                <div className="text-sm font-bold text-term-white tabular-nums">
                  {user.usage.ai_messages} / {user.limits.ai_messages_per_day}
                </div>
              </div>
              <div>
                <div className="text-xxs text-term-dim">Backtests</div>
                <div className="text-sm font-bold text-term-white tabular-nums">
                  {user.usage.backtests} / {user.limits.backtests_per_day}
                </div>
              </div>
              <div>
                <div className="text-xxs text-term-dim">AI Strategy Gen</div>
                <div className={`text-sm font-bold ${
                  user.limits.ai_strategy_generator ? "text-term-green" : "text-term-red"
                }`}>
                  {user.limits.ai_strategy_generator ? "ENABLED" : "LOCKED"}
                </div>
              </div>
            </div>
            {user.plan === "pro" && (
              <button
                onClick={handlePortal}
                disabled={loading}
                className="mt-3 w-full py-1.5 text-xxs text-term-dim border border-term-border hover:text-term-white hover:border-term-dim transition-colors disabled:opacity-30"
              >
                MANAGE SUBSCRIPTION
              </button>
            )}
          </div>
        )}

        {/* Tier cards */}
        <div className="grid grid-cols-2 gap-4">
          {TIERS.map((tier) => {
            const isCurrent = user?.plan === tier.plan;
            const isUpgrade = tier.plan === "pro" && user?.plan !== "pro";
            return (
              <div
                key={tier.plan}
                className={`border flex flex-col ${
                  tier.plan === "pro"
                    ? "border-term-orange/50 bg-term-orange/[0.03]"
                    : "border-term-border bg-term-bg"
                }`}
              >
                {tier.plan === "pro" && (
                  <div className="bg-term-orange text-term-black text-xxs font-bold text-center py-1">
                    RECOMMENDED
                  </div>
                )}

                <div className="p-4 flex-1 flex flex-col">
                  <div className="mb-3">
                    <div className="text-term-white font-bold text-sm">{tier.name}</div>
                    <div className="flex items-baseline gap-1 mt-1">
                      <span className="text-2xl font-bold text-term-orange">{tier.price}</span>
                      <span className="text-xxs text-term-dim">{tier.period}</span>
                    </div>
                  </div>

                  <div className="flex-1 space-y-1.5 mb-4">
                    {tier.features.map((f) => (
                      <div key={f} className="flex items-start gap-2 text-xs">
                        <span className="text-term-green mt-0.5 flex-shrink-0">+</span>
                        <span className="text-term-text">{f}</span>
                      </div>
                    ))}
                    {tier.excluded.map((f) => (
                      <div key={f} className="flex items-start gap-2 text-xs">
                        <span className="text-term-red mt-0.5 flex-shrink-0">-</span>
                        <span className="text-term-dim line-through">{f}</span>
                      </div>
                    ))}
                  </div>

                  {isCurrent ? (
                    <div className="py-2 text-center text-xs font-bold text-term-muted bg-term-surface border border-term-border">
                      CURRENT PLAN
                    </div>
                  ) : isUpgrade ? (
                    <button
                      onClick={handleUpgrade}
                      disabled={loading || (checkingBilling ? true : !billingConfigured)}
                      className="w-full py-2 bg-term-orange text-term-black text-xs font-bold hover:bg-term-orange-dim disabled:opacity-30 transition-colors"
                    >
                      {loading
                        ? "PROCESSING..."
                        : checkingBilling
                        ? "CHECKING..."
                        : !billingConfigured
                        ? "BILLING NOT YET CONFIGURED"
                        : "UPGRADE TO PRO"}
                    </button>
                  ) : !user ? (
                    <Link
                      href="/login"
                      className="block py-2 text-center text-xs font-bold text-term-orange border border-term-orange hover:bg-term-orange hover:text-term-black transition-colors"
                    >
                      SIGN UP FREE
                    </Link>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xxs text-term-dim">
          <p>All plans include unlimited access to the market dashboard and asset pages.</p>
          <p className="mt-1">Usage resets daily at midnight UTC. Cancel anytime.</p>
        </div>
      </div>
    </div>
  );
}

export default function PricingPage() {
  return (
    <Suspense fallback={
      <div className="h-full flex items-center justify-center">
        <span className="text-term-dim text-xs">Loading pricing...</span>
      </div>
    }>
      <PricingContent />
    </Suspense>
  );
}
