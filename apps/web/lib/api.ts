const RAW_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
export const API_BASE = RAW_BASE.replace(/\/$/, "");

const TOKEN_KEY = "tb_ws";

export class ApiError extends Error {
  code: string;
  status: number;
  title: string;
  detail: string;

  constructor(status: number, code: string, title: string, detail: string) {
    super(detail || title);
    this.status = status;
    this.code = code;
    this.title = title;
    this.detail = detail;
  }
}

function readStoredToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // private mode: token stays in memory for this session only
  }
}

let memoryToken: string | null = null;

export async function getToken(): Promise<string> {
  if (memoryToken) return memoryToken;
  const stored = readStoredToken();
  if (stored) {
    memoryToken = stored;
    return stored;
  }
  const response = await fetch(`${API_BASE}/v1/workspaces/session`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{}",
  });
  if (!response.ok) {
    throw new ApiError(response.status, "session_failed", "Could not start a session", "");
  }
  const payload = (await response.json()) as { workspace_token: string };
  memoryToken = payload.workspace_token;
  storeToken(payload.workspace_token);
  return payload.workspace_token;
}

async function request<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const workspaceToken = token ?? (await getToken());
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "X-Workspace-Token": workspaceToken,
      ...(init?.body instanceof FormData ? {} : { "content-type": "application/json" }),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let code = "request_failed";
    let title = response.statusText || "Request failed";
    let detail = "";
    try {
      const payload = (await response.json()) as {
        code?: string;
        title?: string;
        detail?: string;
      };
      code = payload.code ?? code;
      title = payload.title ?? title;
      detail = payload.detail ?? detail;
    } catch {
      // non-JSON error body
    }
    throw new ApiError(response.status, code, title, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  postForm: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
};

export function sseUrl(path: string, token: string): string {
  const separator = path.includes("?") ? "&" : "?";
  return `${API_BASE}${path}${separator}token=${encodeURIComponent(token)}`;
}
