"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import UpgradeModal from "@/components/UpgradeModal";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  limitReached?: boolean;
}

const SUGGESTIONS = [
  "Why is the market down today?",
  "What stocks have the strongest momentum?",
  "Compare NVDA vs AMD",
  "What's the outlook for Bitcoin?",
  "Best sectors for current macro environment?",
  "Explain the yield curve inversion",
];

export default function ChatPage() {
  const { user, refresh } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [upgradeMsg, setUpgradeMsg] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const now = () =>
    new Date().toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });

  const sendMessage = async (text?: string) => {
    const message = text || input.trim();
    if (!message || loading) return;
    setInput("");

    const userMsg: ChatMessage = { role: "user", content: message, timestamp: now() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const assistantMsg: ChatMessage = { role: "assistant", content: "", timestamp: now() };
    setMessages((prev) => [...prev, assistantMsg]);

    let content = "";
    let hitLimit = false;
    try {
      for await (const chunk of streamChat(message)) {
        content += chunk;
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { ...assistantMsg, content };
          return updated;
        });
      }
    } catch (e: any) {
      content = `ERROR: ${e.message}. Verify backend at http://localhost:8000`;
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { ...assistantMsg, content };
        return updated;
      });
    } finally {
      setLoading(false);
      if (user) refresh();
    }
  };

  const remaining = user
    ? Math.max(0, user.limits.ai_messages_per_day - user.usage.ai_messages)
    : null;

  return (
    <div className="h-full flex flex-col">
      {upgradeMsg && (
        <UpgradeModal message={upgradeMsg} onClose={() => setUpgradeMsg("")} />
      )}

      {/* Title */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-term-bg border-b border-term-border">
        <div className="flex items-center gap-3">
          <span className="text-term-orange font-bold text-sm">AI MARKET RESEARCH</span>
          <span className="text-term-dim text-xxs">GLOOMBERG CHAT</span>
        </div>
        <div className="flex items-center gap-3">
          {user && remaining !== null && (
            <span className={`text-xxs font-bold ${
              remaining <= 3 ? "text-term-red" : "text-term-muted"
            }`}>
              {remaining} / {user.limits.ai_messages_per_day} MSGS LEFT TODAY
            </span>
          )}
          <span className="text-xxs text-term-dim">{messages.length} MESSAGES</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto font-terminal">
        {messages.length === 0 ? (
          <div className="p-4">
            <div className="text-term-orange text-sm font-bold mb-2">
              GLOOMBERG AI RESEARCH TERMINAL
            </div>
            <div className="text-term-dim text-xs mb-4">
              Ask questions about markets, stocks, crypto, and trading strategies.
              Type your question below or select a prompt.
            </div>

            <div className="text-xxs text-term-muted mb-2 uppercase">Suggested Queries:</div>
            <div className="space-y-1">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="block w-full text-left px-2 py-1.5 text-xs border border-term-border bg-term-bg hover:bg-term-surface hover:border-term-orange/30 transition-colors"
                >
                  <span className="text-term-yellow mr-2">{i + 1}.</span>
                  <span className="text-term-text">{s}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-2 space-y-0">
            {messages.map((msg, i) => (
              <div key={i} className="mb-2">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xxs text-term-dim">{msg.timestamp}</span>
                  {msg.role === "user" ? (
                    <span className="text-xxs text-term-blue font-bold">YOU &gt;</span>
                  ) : (
                    <span className="text-xxs text-term-orange font-bold">GLOOM &gt;</span>
                  )}
                </div>
                <div
                  className={`pl-4 text-xs leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "text-term-white"
                      : msg.content.startsWith("ERROR:")
                      ? "text-term-red"
                      : "text-term-green"
                  }`}
                >
                  {msg.content}
                  {msg.role === "assistant" && !msg.content && loading && (
                    <span className="text-term-orange blink">█</span>
                  )}
                </div>
              </div>
            ))}
            <div ref={endRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-term-border bg-term-bg px-2 py-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex items-center gap-2"
        >
          <span className="text-term-orange text-xs font-bold">&gt;_</span>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your market question..."
            disabled={loading}
            className="flex-1 bg-transparent text-term-white text-sm py-1 placeholder:text-term-dim disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-3 py-1 bg-term-orange text-term-black text-xs font-bold hover:bg-term-orange-dim disabled:opacity-30"
          >
            {loading ? "PROCESSING..." : "SEND"}
          </button>
        </form>
      </div>
    </div>
  );
}
