"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { streamResearch, type ResearchEvent } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import UpgradeModal from "@/components/UpgradeModal";

interface ToolCall {
  tool: string;
  ticker?: string;
  args?: Record<string, unknown>;
  status: "running" | "done" | "error";
  summary?: string;
  error?: string;
}

interface ResearchSession {
  query: string;
  thinking: string[];
  tools: ToolCall[];
  answer: string;
  status: "running" | "done" | "error";
  iterations?: number;
  toolsCalled?: number;
  timeMs?: number;
}

const SUGGESTIONS = [
  "Deep dive into NVDA — financials, valuation, and outlook",
  "Compare AAPL vs MSFT revenue growth and profitability",
  "Why has TSLA stock been moving recently?",
  "Analyze Amazon's cash flow and balance sheet health",
  "What do analyst estimates say about Google's future?",
  "Show insider trading activity for AAPL",
];

function formatToolName(name: string): string {
  return name
    .replace(/^get_/, "")
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function ResearchPage() {
  const { user, refresh } = useAuth();
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [upgradeMsg, setUpgradeMsg] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessions]);

  const runResearch = async (text?: string) => {
    const query = text || input.trim();
    if (!query || loading) return;
    setInput("");
    setLoading(true);

    const session: ResearchSession = {
      query,
      thinking: [],
      tools: [],
      answer: "",
      status: "running",
    };
    setSessions((prev) => [...prev, session]);

    const idx = sessions.length;

    const update = (fn: (s: ResearchSession) => ResearchSession) => {
      setSessions((prev) => prev.map((s, i) => (i === idx ? fn(s) : s)));
    };

    try {
      for await (const event of streamResearch(query)) {
        switch (event.type) {
          case "thinking":
            update((s) => ({
              ...s,
              thinking: [...s.thinking, event.content || ""],
            }));
            break;

          case "tool_start":
            update((s) => ({
              ...s,
              tools: [
                ...s.tools,
                {
                  tool: event.tool || "",
                  ticker: event.ticker,
                  args: event.args,
                  status: "running",
                },
              ],
            }));
            break;

          case "tool_end":
            update((s) => {
              const tools = [...s.tools];
              const last = tools.findLastIndex(
                (t) => t.tool === event.tool && t.status === "running"
              );
              if (last >= 0) {
                tools[last] = {
                  ...tools[last],
                  status: "done",
                  ticker: event.ticker || tools[last].ticker,
                  summary: event.result_summary,
                };
              }
              return { ...s, tools };
            });
            break;

          case "tool_error":
            update((s) => {
              const tools = [...s.tools];
              const last = tools.findLastIndex(
                (t) => t.tool === event.tool && t.status === "running"
              );
              if (last >= 0) {
                tools[last] = {
                  ...tools[last],
                  status: "error",
                  error: event.error,
                };
              }
              return { ...s, tools };
            });
            break;

          case "answer":
            update((s) => ({
              ...s,
              answer: event.content || "",
            }));
            break;

          case "done":
            update((s) => ({
              ...s,
              status: "done",
              iterations: event.iterations,
              toolsCalled: event.tools_called,
              timeMs: event.time_ms,
            }));
            break;
        }
      }
    } catch (e: any) {
      update((s) => ({
        ...s,
        answer: `ERROR: ${e.message}`,
        status: "error",
      }));
    } finally {
      setLoading(false);
      if (user) refresh();
    }
  };

  const remaining = user
    ? Math.max(
        0,
        user.limits.ai_messages_per_day - user.usage.ai_messages
      )
    : null;

  return (
    <div className="h-full flex flex-col">
      {upgradeMsg && (
        <UpgradeModal message={upgradeMsg} onClose={() => setUpgradeMsg("")} />
      )}

      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-term-bg border-b border-term-border">
        <div className="flex items-center gap-3">
          <span className="text-term-orange font-bold text-sm">
            DEEP RESEARCH
          </span>
          <span className="text-term-dim text-xxs">
            POWERED BY DEXTER AGENT
          </span>
        </div>
        <div className="flex items-center gap-3">
          {user && remaining !== null && (
            <span
              className={`text-xxs font-bold ${
                remaining <= 3 ? "text-term-red" : "text-term-muted"
              }`}
            >
              {remaining} / {user.limits.ai_messages_per_day} MSGS LEFT TODAY
            </span>
          )}
          <span className="text-xxs text-term-dim">
            {sessions.length} RESEARCH{sessions.length !== 1 ? "ES" : ""}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto font-terminal">
        {sessions.length === 0 ? (
          <div className="p-4">
            <div className="text-term-orange text-sm font-bold mb-1">
              DEXTER AUTONOMOUS RESEARCH AGENT
            </div>
            <div className="text-term-dim text-xs mb-1">
              Powered by the same Financial Datasets API used by{" "}
              <span className="text-term-blue">virattt/dexter</span>.
            </div>
            <div className="text-term-dim text-xs mb-4">
              Ask a complex financial question. Dexter will autonomously plan
              research steps, gather real market data (income statements,
              balance sheets, cash flow, prices, news, analyst estimates), and
              synthesize a data-driven answer.
            </div>

            <div className="text-xxs text-term-muted mb-2 uppercase">
              Try These:
            </div>
            <div className="space-y-1">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={s}
                  onClick={() => runResearch(s)}
                  className="block w-full text-left px-2 py-1.5 text-xs border border-term-border bg-term-bg hover:bg-term-surface hover:border-term-orange/30 transition-colors"
                >
                  <span className="text-term-yellow mr-2">{i + 1}.</span>
                  <span className="text-term-text">{s}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-2 space-y-4">
            {sessions.map((session, si) => (
              <div key={si} className="border border-term-border bg-term-bg">
                {/* Query */}
                <div className="px-3 py-2 border-b border-term-border bg-term-surface/50">
                  <div className="flex items-center gap-2">
                    <span className="text-xxs text-term-blue font-bold">
                      QUERY
                    </span>
                    {session.status === "running" && (
                      <span className="text-xxs text-term-yellow blink">
                        RESEARCHING...
                      </span>
                    )}
                    {session.status === "done" && session.timeMs && (
                      <span className="text-xxs text-term-green">
                        COMPLETE ({formatDuration(session.timeMs)} /{" "}
                        {session.iterations} iterations /{" "}
                        {session.toolsCalled} tool calls)
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-term-white mt-0.5">
                    {session.query}
                  </div>
                </div>

                {/* Thinking */}
                {session.thinking.length > 0 && (
                  <div className="px-3 py-2 border-b border-term-border/50">
                    <div className="text-xxs text-term-muted font-bold mb-1 uppercase">
                      Agent Reasoning
                    </div>
                    {session.thinking.map((t, ti) => (
                      <div
                        key={ti}
                        className="text-xs text-term-dim italic pl-2 border-l border-term-border/50 mb-1"
                      >
                        {t}
                      </div>
                    ))}
                  </div>
                )}

                {/* Tool Calls */}
                {session.tools.length > 0 && (
                  <div className="px-3 py-2 border-b border-term-border/50">
                    <div className="text-xxs text-term-muted font-bold mb-1 uppercase">
                      Data Gathering
                    </div>
                    <div className="space-y-1">
                      {session.tools.map((tc, ti) => (
                        <div
                          key={ti}
                          className="flex items-center gap-2 text-xs"
                        >
                          {tc.status === "running" && (
                            <span className="text-term-yellow blink">●</span>
                          )}
                          {tc.status === "done" && (
                            <span className="text-term-green">✓</span>
                          )}
                          {tc.status === "error" && (
                            <span className="text-term-red">✗</span>
                          )}
                          <span className="text-term-blue font-bold">
                            {formatToolName(tc.tool)}
                          </span>
                          {tc.ticker && (
                            <span className="text-term-yellow">{tc.ticker}</span>
                          )}
                          {tc.status === "done" && tc.summary && (
                            <span className="text-term-dim truncate max-w-[300px]">
                              — {tc.summary}
                            </span>
                          )}
                          {tc.status === "error" && tc.error && (
                            <span className="text-term-red truncate max-w-[300px]">
                              — {tc.error}
                            </span>
                          )}
                          {tc.status === "running" && (
                            <span className="text-term-dim">fetching...</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Answer */}
                {session.answer && (
                  <div className="px-3 py-2">
                    <div className="text-xxs text-term-orange font-bold mb-1 uppercase">
                      Research Report
                    </div>
                    <div className="text-xs text-term-green leading-relaxed prose-terminal">
                      <ReactMarkdown
                        components={{
                          h1: ({ children }) => <div className="text-sm text-term-orange font-bold mt-3 mb-1">{children}</div>,
                          h2: ({ children }) => <div className="text-sm text-term-orange font-bold mt-3 mb-1">{children}</div>,
                          h3: ({ children }) => <div className="text-xs text-term-yellow font-bold mt-2 mb-1">{children}</div>,
                          h4: ({ children }) => <div className="text-xs text-term-yellow font-bold mt-2 mb-0.5">{children}</div>,
                          strong: ({ children }) => <span className="text-term-white font-bold">{children}</span>,
                          em: ({ children }) => <span className="text-term-dim italic">{children}</span>,
                          p: ({ children }) => <p className="mb-2">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-0.5">{children}</ol>,
                          li: ({ children }) => <li>{children}</li>,
                          table: ({ children }) => <table className="w-full mb-2 border border-term-border">{children}</table>,
                          thead: ({ children }) => <thead className="bg-term-surface">{children}</thead>,
                          th: ({ children }) => <th className="text-left px-2 py-1 text-xxs text-term-yellow font-bold border-b border-term-border">{children}</th>,
                          td: ({ children }) => <td className="px-2 py-0.5 text-xxs border-b border-term-border/50">{children}</td>,
                          code: ({ children }) => <code className="text-term-cyan bg-term-surface px-1">{children}</code>,
                        }}
                      >
                        {session.answer}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Loading indicator when no answer yet */}
                {!session.answer && session.status === "running" && (
                  <div className="px-3 py-2">
                    <span className="text-term-orange text-xs blink">
                      █ Synthesizing research...
                    </span>
                  </div>
                )}
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
            runResearch();
          }}
          className="flex items-center gap-2"
        >
          <span className="text-term-orange text-xs font-bold">&gt;_</span>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a deep financial research question..."
            disabled={loading}
            className="flex-1 bg-transparent text-term-white text-sm py-1 placeholder:text-term-dim disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-3 py-1 bg-term-orange text-term-black text-xs font-bold hover:bg-term-orange-dim disabled:opacity-30"
          >
            {loading ? "RESEARCHING..." : "RESEARCH"}
          </button>
        </form>
      </div>
    </div>
  );
}
