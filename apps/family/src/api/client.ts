import { API_BASE_URL } from "./config";
import { ApiError } from "./errors";
import { getTokenStore } from "./tokenStore";
import type { ApiErrorBody, TokenPair } from "./types";

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean;
  query?: Record<string, string | number | undefined>;
  skipRefresh?: boolean;
};

let refreshInFlight: Promise<string | null> | null = null;

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(path.replace(/^\//, ""), `${API_BASE_URL.replace(/\/$/, "")}/`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function parseBody(response: Response): Promise<ApiErrorBody | null> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as ApiErrorBody;
  } catch {
    return { detail: text };
  }
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshInFlight) {
    return refreshInFlight;
  }
  refreshInFlight = (async () => {
    const store = getTokenStore();
    const refresh = await store.getRefreshToken();
    if (!refresh) {
      return null;
    }
    const response = await fetch(buildUrl("/auth/token/refresh/"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!response.ok) {
      await store.clear();
      return null;
    }
    const data = (await response.json()) as { access: string };
    await store.setTokens(data.access, refresh);
    return data.access;
  })();
  try {
    return await refreshInFlight;
  } finally {
    refreshInFlight = null;
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const store = getTokenStore();
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.auth !== false) {
    const access = await store.getAccessToken();
    if (access) {
      headers.Authorization = `Bearer ${access}`;
    }
  }

  const response = await fetch(buildUrl(path, options.query), {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (response.status === 401 && options.auth !== false && !options.skipRefresh) {
    const next = await refreshAccessToken();
    if (next) {
      return apiRequest<T>(path, { ...options, skipRefresh: true });
    }
  }

  if (!response.ok) {
    const body = await parseBody(response);
    const message = typeof body?.detail === "string" ? body.detail : `HTTP ${response.status}`;
    throw new ApiError(response.status, body, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export async function login(phone: string, password: string): Promise<TokenPair> {
  return apiRequest<TokenPair>("/auth/token/", {
    method: "POST",
    auth: false,
    body: { phone, password },
  });
}

export async function refreshSession(refresh: string): Promise<{ access: string }> {
  return apiRequest<{ access: string }>("/auth/token/refresh/", {
    method: "POST",
    auth: false,
    body: { refresh },
  });
}
