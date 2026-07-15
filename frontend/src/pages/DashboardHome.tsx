import { useEffect, useState } from 'react';
import { get } from '../services/api';

interface DCInfo {
  DCName: string;
  Hostname: string;
  IPAddress: string;
  Site: string;
  Status: string;
  LastReplication: string;
  ResponseTime: number;
}

interface NTPClient {
  Address: string;
  Hostname: string;
  Status: string;
  NTPServer: string;
  Offset: number;
  NTPPkts?: number;
  Drop: number;
  Interval: number;
  Reach: number;
  Last: string;
  LastMin?: number;
  LastUnit?: string;
  LastSeen: string;
}

interface OverviewData {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  active_alerts: number;
  critical_alerts: number;
  open_tickets: number;
  dcs?: DCInfo[];
  ntp_clients?: NTPClient[];
}

function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase() ?? '';
  let color = '#94a3b8', bg = '#1e293b', label = status ?? 'Unknown';
  if (s === 'ok' || s === 'online' || s === 'healthy') { color = '#34d399'; bg = '#064e3b'; label = 'OK'; }
  else if (s === 'error' || s === 'critical' || s === 'crit' || s === 'offline') { color = '#f87171'; bg = '#7f1d1d'; label = s === 'crit' ? 'Critical' : s.charAt(0).toUpperCase() + s.slice(1); }
  else if (s === 'warning' || s === 'warn') { color = '#fbbf24'; bg = '#78350f'; label = 'Warning'; }
  return (
    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600, color, background: bg, border: `1px solid ${color}33` }}>{label}</span>
  );
}

export default function DashboardHome() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    get<OverviewData>('dashboard/overview')
      .then((d) => setData(d))
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="loading">Loading overview…</div>;

  const dcs = data.dcs ?? [];
  const ntpClients = (data.ntp_clients ?? []).slice(0, 10); // Top 10 most relevant

  return (
    <section className="overview">
      <h1 style={{ fontSize: 22, color: '#e2e8f0', marginBottom: 20 }}>Dashboard Overview</h1>

      {/* Summary Cards */}
      <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 24 }}>
        {[
          { label: 'Total Devices', value: data.total_devices, color: '#38bdf8' },
          { label: 'Online', value: data.online_devices, color: '#34d399' },
          { label: 'Offline', value: data.offline_devices, color: '#f87171' },
          { label: 'Active Alerts', value: data.active_alerts, color: '#fbbf24' },
          { label: 'Critical', value: data.critical_alerts, color: '#f87171' },
          { label: 'Open Tickets', value: data.open_tickets, color: '#a78bfa' },
        ].map(card => (
          <div key={card.label} className="card" style={{ background: '#0f172a', borderRadius: 12, padding: '16px 20px', borderLeft: `3px solid ${card.color}` }}>
            <div className="card-title" style={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>{card.label}</div>
            <div className="card-value" style={{ color: card.color, fontSize: 28, fontWeight: 700 }}>{card.value}</div>
          </div>
        ))}
      </div>

      {/* Domain Controllers */}
      {dcs.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, color: '#e2e8f0', marginBottom: 12 }}>Domain Controllers</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e293b' }}>
                  <th style={{ textAlign: 'left', padding: '6px 10px', color: '#64748b' }}>Name</th>
                  <th style={{ textAlign: 'left', padding: '6px 10px', color: '#64748b' }}>Hostname</th>
                  <th style={{ textAlign: 'left', padding: '6px 10px', color: '#64748b' }}>IP</th>
                  <th style={{ textAlign: 'left', padding: '6px 10px', color: '#64748b' }}>Site</th>
                  <th style={{ textAlign: 'center', padding: '6px 10px', color: '#64748b' }}>Status</th>
                  <th style={{ textAlign: 'left', padding: '6px 10px', color: '#64748b' }}>Last Repl</th>
                  <th style={{ textAlign: 'center', padding: '6px 10px', color: '#64748b' }}>RT (ms)</th>
                </tr>
              </thead>
              <tbody>
                {dcs.map((dc, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1e293b22', background: i % 2 ? '#0f172a44' : 'transparent' }}>
                    <td style={{ padding: '6px 10px', color: '#e2e8f0' }}>{dc.DCName}</td>
                    <td style={{ padding: '6px 10px', color: '#38bdf8', fontSize: 12 }}>{dc.Hostname || '—'}</td>
                    <td style={{ padding: '6px 10px', color: '#64748b', fontFamily: 'monospace', fontSize: 12 }}>{dc.IPAddress}</td>
                    <td style={{ padding: '6px 10px', color: '#94a3b8' }}>{dc.Site}</td>
                    <td style={{ padding: '6px 10px', textAlign: 'center' }}><StatusBadge status={dc.Status} /></td>
                    <td style={{ padding: '6px 10px', color: '#94a3b8', fontSize: 12 }}>{dc.LastReplication}</td>
                    <td style={{ padding: '6px 10px', textAlign: 'center', color: dc.ResponseTime > 10 ? '#fbbf24' : '#94a3b8' }}>{dc.ResponseTime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* NTP Top Clients */}
      {ntpClients.length > 0 && (
        <div>
          <h2 style={{ fontSize: 16, color: '#e2e8f0', marginBottom: 12 }}>NTP Clients (top issues)</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1e293b' }}>
                  <th style={{ textAlign: 'left', padding: '6px 10px', color: '#64748b' }}>Hostname</th>
                  <th style={{ textAlign: 'left', padding: '6px 10px', color: '#64748b' }}>IP</th>
                  <th style={{ textAlign: 'center', padding: '6px 10px', color: '#64748b' }}>Status</th>
                  <th style={{ textAlign: 'center', padding: '6px 10px', color: '#64748b' }}>Last</th>
                </tr>
              </thead>
              <tbody>
                {ntpClients.map((c, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1e293b22', background: i % 2 ? '#0f172a44' : 'transparent' }}>
                    <td style={{ padding: '6px 10px', color: '#e2e8f0' }}>
                      {c.Hostname && c.Hostname !== c.Address ? c.Hostname : <span style={{ color: '#94a3b8' }}>{c.Address}</span>}
                    </td>
                    <td style={{ padding: '6px 10px', color: '#64748b', fontFamily: 'monospace', fontSize: 12 }}>
                      {c.Hostname && c.Hostname !== c.Address ? c.Address : '—'}
                    </td>
                    <td style={{ padding: '6px 10px', textAlign: 'center' }}><StatusBadge status={c.Status} /></td>
                    <td style={{ padding: '6px 10px', textAlign: 'center', color: '#e2e8f0' }}>{c.Last ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: 8, color: '#475569', fontSize: 12, textAlign: 'center' }}>
            Showing top {ntpClients.length} — <a href="/chrony" style={{ color: '#38bdf8' }}>View all NTP clients →</a>
          </div>
        </div>
      )}
    </section>
  );
}