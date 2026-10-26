/**
 * Thin client for the SERVE FastAPI backend. Same-origin `/api` — Vite proxies it
 * to the backend in dev, and the backend serves the built app in single-port mode.
 * No secrets live in the browser; the admin token is typed in by staff and kept in
 * sessionStorage for the tab only.
 */

export class ApiError extends Error {
  status: number;
  problems: string[];
  constructor(status: number, message: string, problems: string[] = []) {
    super(message);
    this.status = status;
    this.problems = problems;
  }
}

const ADMIN_KEY = "serve_admin_token";

export const adminToken = {
  get: () => sessionStorage.getItem(ADMIN_KEY) ?? "",
  set: (t: string) => sessionStorage.setItem(ADMIN_KEY, t),
  clear: () => sessionStorage.removeItem(ADMIN_KEY),
};

async function request<T>(method: string, path: string, body?: unknown, admin = false): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (admin) headers["X-Admin-Token"] = adminToken.get();
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Can't reach the SERVE backend. Is it running on port 8000?");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).join("; ")
      : (detail ?? `Request failed (${res.status})`);
    const problems = Array.isArray(data?.problems) ? data.problems : [];
    throw new ApiError(res.status, String(message), problems);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body: unknown) => request<T>("POST", path, body),
  adminGet: <T>(path: string) => request<T>("GET", `/admin${path}`, undefined, true),
  adminPost: <T>(path: string, body: unknown) => request<T>("POST", `/admin${path}`, body, true),
};

/* ---------------- formatting ---------------- */

export function fmtDate(iso: string, opts: Intl.DateTimeFormatOptions = { weekday: "long", month: "long", day: "numeric" }) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", opts);
}

export function fmtTime(hhmm: string) {
  const [h, m] = hhmm.split(":").map(Number);
  const suffix = h >= 12 ? "PM" : "AM";
  return `${((h + 11) % 12) + 1}:${String(m).padStart(2, "0")} ${suffix}`;
}

export function fmtTimestamp(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
