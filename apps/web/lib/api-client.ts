const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

let accessTokenMemory: string | null = null;

export function setAccessToken(token: string | null) {
  accessTokenMemory = token;
}

export function clearTokens() {
  setAccessToken(null);
}

async function refreshAccessToken(): Promise<string | null> {
  const response = await fetch("/api/auth/refresh", {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    clearTokens();
    return null;
  }

  const data = await response.json();
  if (!data?.access_token) {
    clearTokens();
    return null;
  }

  setAccessToken(data.access_token);
  return data.access_token;
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers || {});
  headers.set("Content-Type", "application/json");

  if (accessTokenMemory) {
    headers.set("Authorization", `Bearer ${accessTokenMemory}`);
  }

  let response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (response.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await fetch(`${API_URL}${path}`, {
        ...init,
        headers,
        credentials: "include",
      });
    }
  }

  return response;
}
