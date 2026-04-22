"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, clearTokens, setAccessToken } from "@/lib/api-client";
import { LoginPayload, LoginResponse } from "@/types";

type AuthContextType = {
  isAuthenticated: boolean;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refresh = async () => {
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      clearTokens();
      setIsAuthenticated(false);
      return false;
    }

    const data = (await response.json()) as Partial<LoginResponse>;
    if (!data.access_token) {
      clearTokens();
      setIsAuthenticated(false);
      return false;
    }

    setAccessToken(data.access_token);
    setIsAuthenticated(true);
    return true;
  };

  useEffect(() => {
    const boot = async () => {
      await refresh();
      setLoading(false);
    };

    boot();
  }, []);

  const login = async (payload: LoginPayload) => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    });

    if (!response.ok) throw new Error("Credenciales inválidas");

    const data = (await response.json()) as LoginResponse;
    setAccessToken(data.access_token);
    setIsAuthenticated(true);
  };

  const logout = async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      clearTokens();
      setIsAuthenticated(false);
      router.push("/login");
    }
  };

  const value = useMemo(
    () => ({ isAuthenticated, loading, login, logout, refresh }),
    [isAuthenticated, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used within AuthProvider");
  return ctx;
}

export async function fetchWithAuth(path: string, init?: RequestInit) {
  return apiFetch(path, init);
}
