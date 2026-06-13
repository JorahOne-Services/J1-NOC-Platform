import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function RequireAuth({ children }: { children: React.ReactElement }) {
  const { token, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div className="loading">Loading…</div>;
  if (!token) return <Navigate to="/login" state={{ from: loc }} replace />;
  return children;
}
