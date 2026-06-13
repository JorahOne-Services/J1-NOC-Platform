const base = import.meta.env.VITE_API_URL || '/api/';

export async function get(url: string) {
  const res = await fetch(`${base}${url.replace(/^\//, '')}`, {
    headers: { Authorization: localStorage.getItem('token') ? `Bearer ${localStorage.getItem('token')}` : '' },
  });
  if (!res.ok) throw new Error('Request failed');
  return res.json();
}

export async function post(url: string, body: unknown) {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${base}${url.replace(/^\//, '')}`, { method: 'POST', headers, body: JSON.stringify(body) });
  if (!res.ok) throw new Error('Request failed');
  return res.json();
}
