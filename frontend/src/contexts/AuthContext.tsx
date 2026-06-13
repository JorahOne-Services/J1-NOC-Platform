import { createContext, useContext, useEffect, useState } from 'react';
import { get } from '../services/api';

type AuthState = {
  token: string | null;
  user: { username: string; role: string } | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token') ?? null);
  const [user, setUser] = useState<{ username: string; role: string } | null>(() => {
    if (typeof window === 'undefined') return null;
    try { return JSON.parse(localStorage.getItem('user') as string) ?? null }
    catch { return null }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      if (token) {
        try {
          const me = await get('/auth/me');
          if (!cancelled) setUser({ username: me.username, role: me.role?.slug || me.role || 'reader' });
        } catch {
          if (!cancelled) { setToken(null); setUser(null) }
        }
      }
      if (!cancelled) setLoading(false);
    }
    init();
    return () => { cancelled = true };
  }, [token]);

  useEffect(() => {
    localStorage.setItem('token', token ?? '');
    if (token) localStorage.setItem('user', JSON.stringify(user ?? null));
    else localStorage.removeItem('user');
  }, [token, user]);

  const login = async (username: string, password: string) => {
    setLoading(true);
    const base = import.meta.env.VITE_API_URL || '/api';
    const res = await fetch(`${base}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error((await res.text()) || 'Invalid credentials');
    const data = await res.json();
    setToken(data.access_token);
    setUser({ username, role: data.role || user?.role || 'reader' });
    setLoading(false);
  };

  const logout = () => { setToken(null); setUser(null); };

  return <AuthContext.Provider value={{ token, user, login, logout, loading }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
