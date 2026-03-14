"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login, register } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex items-center justify-center">
      <div className="w-full max-w-sm border border-term-border bg-term-bg">
        {/* Header */}
        <div className="terminal-header flex items-center justify-between">
          <span>{mode === "login" ? "LOGIN" : "REGISTER"} | AUTH &raquo;</span>
          <span className="text-term-dim font-normal">GLOOMBERG</span>
        </div>

        <div className="p-4">
          {/* Tabs */}
          <div className="flex mb-4 border border-term-border">
            <button
              onClick={() => { setMode("login"); setError(""); }}
              className={`flex-1 py-1.5 text-xs font-bold transition-colors ${
                mode === "login"
                  ? "bg-term-orange text-term-black"
                  : "bg-term-surface text-term-muted hover:text-term-white"
              }`}
            >
              LOGIN
            </button>
            <button
              onClick={() => { setMode("register"); setError(""); }}
              className={`flex-1 py-1.5 text-xs font-bold transition-colors ${
                mode === "register"
                  ? "bg-term-orange text-term-black"
                  : "bg-term-surface text-term-muted hover:text-term-white"
              }`}
            >
              REGISTER
            </button>
          </div>

          {error && (
            <div className="mb-3 px-2 py-1.5 bg-term-red/10 border border-term-red/30 text-term-red text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="text-xxs text-term-muted uppercase block mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-term-black border border-term-border text-term-white text-sm px-2 py-1.5 focus:border-term-orange"
                placeholder="trader@example.com"
              />
            </div>
            <div>
              <label className="text-xxs text-term-muted uppercase block mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full bg-term-black border border-term-border text-term-white text-sm px-2 py-1.5 focus:border-term-orange"
                placeholder="Min 6 characters"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-term-orange text-term-black text-xs font-bold hover:bg-term-orange-dim disabled:opacity-30 transition-colors"
            >
              {loading
                ? "PROCESSING..."
                : mode === "login"
                ? "LOGIN"
                : "CREATE ACCOUNT"}
            </button>
          </form>

          <div className="mt-4 pt-3 border-t border-term-border text-center">
            <span className="text-xxs text-term-dim">
              {mode === "login"
                ? "No account? "
                : "Already have an account? "}
            </span>
            <button
              onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
              className="text-xxs text-term-orange hover:text-term-orange-dim"
            >
              {mode === "login" ? "Register" : "Login"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
