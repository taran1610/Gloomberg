"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "gloomberg_token";

export interface UserUsage {
  ai_messages: number;
  backtests: number;
}

export interface UserLimits {
  ai_messages_per_day: number;
  backtests_per_day: number;
  ai_strategy_generator: boolean;
}

export interface User {
  id: string;
  email: string;
  plan: "free" | "pro";
  usage: UserUsage;
  limits: UserLimits;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function authFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...options?.headers,
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data as T;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
  });

  const setAuth = (token: string, user: User) => {
    localStorage.setItem(TOKEN_KEY, token);
    setState({ token, user, loading: false });
  };

  const clearAuth = () => {
    localStorage.removeItem(TOKEN_KEY);
    setState({ token: null, user: null, loading: false });
  };

  const refresh = useCallback(async () => {
    const stored = getStoredToken();
    if (!stored) {
      setState({ token: null, user: null, loading: false });
      return;
    }
    try {
      const user = await authFetch<User>("/api/auth/me", {
        headers: { Authorization: `Bearer ${stored}` },
      });
      setState({ token: stored, user, loading: false });
    } catch {
      clearAuth();
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = async (email: string, password: string) => {
    const res = await authFetch<{ token: string; user: User }>(
      "/api/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    );
    setAuth(res.token, res.user);
  };

  const register = async (email: string, password: string) => {
    const res = await authFetch<{ token: string; user: User }>(
      "/api/auth/register",
      { method: "POST", body: JSON.stringify({ email, password }) }
    );
    setAuth(res.token, res.user);
  };

  const logout = () => clearAuth();

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}
