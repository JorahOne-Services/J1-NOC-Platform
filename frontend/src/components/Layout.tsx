import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const tabs = [
  { to: '/', label: 'Home' },
  { to: '/ldap', label: 'LDAP' },
  { to: '/snmp', label: 'SNMP / PBX' },
  { to: '/tickets', label: 'Helpdesk' },
  { to: '/dns', label: 'DNS' },
  { to: '/chrony', label: 'Chrony' },
  { to: '/admin', label: 'Admin' },
  { to: '/ai', label: 'AI' },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  return (
    <div className="layout">
      <header className="app-header">
        <div className="brand">J1 NOC Platform<span className="badge">v5</span></div>
        <div className="user">
          <span>{user?.username ? `${user.username} (${user.role})` : ''}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </header>
      <nav className="side-tabs">
        {tabs.map((tab) => (
          <Link key={tab.to} to={tab.to} className={`side-tab ${pathname === tab.to ? 'active' : ''}`}>
            {tab.label}
          </Link>
        ))}
      </nav>
      <main className="app-main"><Outlet /></main>
      <footer className="app-footer">Operations Dashboard</footer>
    </div>
  );
}
