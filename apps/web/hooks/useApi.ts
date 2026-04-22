"use client";

import { useCallback, useState } from "react";

import { apiFetch } from "@/lib/api-client";

export function useApi<T>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(async (path: string, init?: RequestInit) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch(path, init);
      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }
      const payload = (await response.json()) as T;
      setData(payload);
      return payload;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, request };
}
