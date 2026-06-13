import { ReactNode } from 'react';

export default function Layout({ children }: { children?: ReactNode }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header
        style={{
          borderBottom: '1px solid #334155',
          padding: '14px 18px',
          display: 'flex',
          gap: 18,
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <strong style={{ letterSpacing: 1 }}>J1 NOC Platform</strong>
        <nav style={{ display: 'flex', gap: 12 }}>
          <a href="/">Overview</a>
          <a href="/ldap">LDAP</a>
          <a href="/snmp">SNMP</a>
          <a href="/chrony">Chrony</a>
          <a href="/tickets">Tickets</a>
          <a href="/dns">DNS</a>
          <a href="/admin">Admin</a>
          <a href="/ai">AI</a>
        </nav>
      </header>
      <main style={{ padding: 20, flex: 1 }}>{children}</main>
    </div>
  );
}
