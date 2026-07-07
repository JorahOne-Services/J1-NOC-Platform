// Normalize base so it ALWAYS ends with a single slash. Without this, a
// `VITE_API_URL=/api` build emits `/apisystem/overview` (no separator) which
// nginx routes to the SPA and the dashboard hangs on "Loading…".
const rawBase = import.meta.env.VITE_API_URL ?? '/api/';
const base = rawBase.endsWith('/') ? rawBase : `${rawBase}/`;
const statusHTTP204 = 204;

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
};

async function request<T = unknown>(url: string, opts: RequestOptions = {}) {
  const { method, body, headers: extra } = opts;
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(extra || {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const serializedBody = body !== undefined ? JSON.stringify(body) : undefined;
  const res = await fetch(`${base}${url.replace(/^\//, '')}`, {
    method,
    headers,
    body: serializedBody,
  });

  if (!res.ok) {
    // Clear a stale/expired token so the app doesn't get stuck "logged in"
    // on a 401 — RequireAuth / AuthContext will re-evaluate and redirect.
    if (res.status === 401 && localStorage.getItem('token')) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    const text = await res.text().catch(() => '');
    throw new Error(text || `Request failed (${res.status})`);
  }
  if (res.status === statusHTTP204 || res.headers.get('content-length') === '0') return null as T;
  return res.json().catch(() => null) as Promise<T>;
}

export async function get<T = unknown>(url: string): Promise<T> {
  return request<T>(url);
}

// NOTE: request() JSON-encodes the body once. Do NOT pre-encode here, or the
// backend receives a double-encoded string and rejects it with 422.
export async function post<T = unknown>(url: string, body: unknown): Promise<T> {
  return request<T>(url, { method: 'POST', body });
}

export async function put<T = unknown>(url: string, body: unknown): Promise<T> {
  return request<T>(url, { method: 'PUT', body });
}

export async function patch<T = unknown>(url: string, body: unknown): Promise<T> {
  return request<T>(url, { method: 'PATCH', body });
}

export async function del<T = unknown>(url: string): Promise<T> {
  return request<T>(url, { method: 'DELETE' });
}

export async function postForm(url: string, form: FormData) {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${base}${url.replace(/^\//, '')}`, {
    method: 'POST',
    headers,
    body: form as any,
  });
  if (!res.ok) throw new Error('Request failed');
  return res.json().catch(() => null);
}
