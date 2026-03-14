"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";

interface UpgradeBannerProps {
  message: string;
  compact?: boolean;
}

export default function UpgradeBanner({ message, compact }: UpgradeBannerProps) {
  const { user } = useAuth();

  if (compact) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-term-orange/10 border border-term-orange/30">
        <span className="text-term-orange text-xs font-bold flex-shrink-0">LIMIT</span>
        <span className="text-xs text-term-text flex-1">{message}</span>
        <Link
          href={user ? "/pricing" : "/login"}
          className="px-3 py-1 bg-term-orange text-term-black text-xxs font-bold hover:bg-term-orange-dim flex-shrink-0 transition-colors"
        >
          {user ? "UPGRADE" : "LOGIN"}
        </Link>
      </div>
    );
  }

  return (
    <div className="border border-term-orange/30 bg-term-orange/[0.05] p-4">
      <div className="flex items-start gap-3">
        <span className="text-term-orange text-lg leading-none">⚡</span>
        <div className="flex-1">
          <div className="text-term-orange font-bold text-xs mb-1">UPGRADE REQUIRED</div>
          <div className="text-xs text-term-text mb-3">{message}</div>
          <div className="flex items-center gap-2">
            <Link
              href={user ? "/pricing" : "/login"}
              className="px-4 py-1.5 bg-term-orange text-term-black text-xs font-bold hover:bg-term-orange-dim transition-colors"
            >
              {user ? "VIEW PLANS" : "LOGIN / SIGN UP"}
            </Link>
            {user && (
              <span className="text-xxs text-term-dim">
                Current plan: {user.plan.toUpperCase()} · {user.usage.ai_messages}/{user.limits.ai_messages_per_day} AI msgs
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
