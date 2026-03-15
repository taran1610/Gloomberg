"use client";

import { useRouter } from "next/navigation";

interface UpgradeModalProps {
  message: string;
  onClose: () => void;
}

export default function UpgradeModal({ message, onClose }: UpgradeModalProps) {
  const router = useRouter();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-full max-w-sm border border-term-orange/50 bg-term-bg">
        <div className="terminal-header flex items-center justify-between">
          <span>LIMIT REACHED | UPGRADE &raquo;</span>
          <button
            onClick={onClose}
            className="text-term-dim hover:text-term-white text-xs"
          >
            [X]
          </button>
        </div>
        <div className="p-4">
          <div className="text-xs text-term-text mb-4 leading-relaxed">
            {message}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => { onClose(); router.push("/pricing"); }}
              className="flex-1 py-2 bg-term-orange text-term-black text-xs font-bold hover:bg-term-orange-dim transition-colors"
            >
              VIEW PLANS
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-term-surface text-term-muted text-xs border border-term-border hover:text-term-white transition-colors"
            >
              CLOSE
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
