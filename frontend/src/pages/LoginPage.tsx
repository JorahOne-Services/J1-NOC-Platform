import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try { await login(form.username, form.password) }
    catch (err: any) { setError(err?.message || 'Invalid credentials') }
    finally { setLoading(false) }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h2>Sign in</h2>
        {error && <div className="error">{error}</div>}
        <label><span>Username</span><input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required /></label>
        <label><span>Password</span><input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required /></label>
        <button disabled={loading}>{loading ? 'Working…' : 'Sign in'}</button>
      </form>
    </div>
  );
}
