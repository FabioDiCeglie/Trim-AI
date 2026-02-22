const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8787";

function getConnectionId(): string | null {
  return localStorage.getItem("trim_connectionId");
}

function getProvider(): string | null {
  return localStorage.getItem("trim_provider");
}

export function hasConnection(): boolean {
  return !!getConnectionId() && !!getProvider();
}

export function setConnection(connectionId: string, provider: string): void {
  localStorage.setItem("trim_connectionId", connectionId);
  localStorage.setItem("trim_provider", provider);
}

export function clearConnection(): void {
  localStorage.removeItem("trim_connectionId");
  localStorage.removeItem("trim_provider");
}

interface RequestOptions {
  method?: string;
  body?: unknown;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body } = options;
  const token = getConnectionId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error || res.statusText);
  return data as T;
}

export const api = {
  connect: (provider: string, credentials: Record<string, unknown>) =>
    request<{ connectionId: string; provider: string }>("/api/v1/connect", {
      method: "POST",
      body: { provider, credentials },
    }),

  projects: () => {
    const provider = getProvider();
    if (!provider) throw new Error("No provider");
    return request<import("../types").Project[]>(`/api/v1/${provider}/projects`);
  },

  overview: (projectId?: string | null) => {
    const provider = getProvider();
    if (!provider) throw new Error("No provider");
    const url = projectId ? `/api/v1/${provider}/overview?project=${encodeURIComponent(projectId)}` : `/api/v1/${provider}/overview`;
    return request<import("../types").Overview>(url);
  },

  chat: (message: string) =>
    request<import("../types").ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: { message },
    }),
};
