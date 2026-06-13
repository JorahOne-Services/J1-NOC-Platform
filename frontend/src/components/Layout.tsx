import { Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="layout">
      <header className="app-header">
        <div className="brand">J1 NOC Platform<span className="badge">v5</span></div>
        <div className="user">
          <span>{user?.username ? `${user.username} (${user.role})` : ''}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>
      <main className="app-main"><Outlet /></main>
      <footer className="app-footer">Operations Dashboard</footer>
    </div>
  );
}
