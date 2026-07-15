import { useEffect, useState, useCallback } from 'react';
import { get } from '../services/api';

interface NTPClient {
  Address: string;
  Hostname: string;
  Status: string;
  NTPServer: string;
  Offset: number;
  NTPPkts: number;
  Drop: number;
  Interval: number;
  Reach: number;
  Last: string;
  LastMin: number;
  LastUnit: string;
  LastSeen: string;
}

interface NTPData {
  Clients: NTPClient[];
}

const STATUS_CFG: Record<string, { label: string; color: string; bg: string }> = {
  ok:       { label: 'OK',       color: '#34d399', bg: '#064e3b' },
  warning:  { label: 'Warning',  color: '#fbbf24', bg: '#78350f' },
  warn:     { label: 'Warning',  color: '#fbbf24', bg: '#78350f' },
  critical: { label: 'Critical', color: '#f87171', bg: '#7f1d1d' },
  crit:     { label: 'Critical', color: '#f87171', bg: '#7f1d1d' },
  unknown:  { label: 'Unknown', color: '#94a3b8', bg: '#1e293b' },
};

function StatusBadge({ status }: { status: string }) {
  const s = STATUS_CFG[status] ?? STATUS_CFG.unknown;
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 600,
      color: s.color,
      background: s.bg,
      border: `1px solid ${s.color}33`,
    }}>
      {s.label}
    </span>
  );
}

function formatLast(raw: string): string {
  if (!raw || raw === '-') return '—';
  return raw;
}

export default function ChronyTab() {
  const [data, setData] = useState<NTPData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchData = useCallback(() => {
    get<NTPData>('/ntp_status')
      .then((d) => {
        setData(d);
        setError(null);
        setLastRefresh(new Date());
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !data) {
    return (
      <section style={{ background: '#0b1220ee', border: '1px solid #38bdf833', borderRadius: 16, padding: 24 }}>
        <h2 style={{ fontSize: 20, color: '#e2e8f0', marginBottom: 16 }}>⏱ Chrony NTP Dashboard</h2>
        <div style={{ color: '#94a3b8', textAlign: 'center', padding: 40 }}>Loading live NTP data…</div>
      </section>
    );
  }

  if (error && !data) {
    return (
      <section style={{ background: '#0b1220ee', border: '1px solid #38bdf833', borderRadius: 16, padding: 24 }}>
        <h2 style={{ fontSize: 20, color: '#e2e8f0', marginBottom: 16 }}>⏱ Chrony NTP Dashboard</h2>
        <div style={{ color: '#f87171', textAlign: 'center', padding: 40 }}>Error: {error}</div>
      </section>
    );
  }

  const clients = data?.Clients ?? [];

  // Stats
  const stats = {
    total: clients.length,
    ok: clients.filter(c => c.Status === 'ok').length,
    warning: clients.filter(c => c.Status === 'warning' || c.Status === 'warn').length,
    critical: clients.filter(c => c.Status === 'critical' || c.Status === 'crit').length,
  };

  // Filter
  const filtered = clients.filter(c => {
    if (filter === 'critical') return c.Status === 'critical' || c.Status === 'crit';
    if (filter === 'warning') return c.Status === 'warning' || c.Status === 'warn';
    if (filter === 'ok') return c.Status === 'ok';
    return true;
  }).filter(c => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (c.Hostname ?? c.Address ?? '').toLowerCase().includes(q)
      || (c.Address ?? '').toLowerCase().includes(q);
  });

  return (
    <section style={{ background: '#0b1220ee', border: '1px solid #38bdf833', borderRadius: 16, padding: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ fontSize: 20, color: '#e2e8f0', margin: 0 }}>⏱ Chrony NTP Dashboard</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <span style={{ color: '#64748b', fontSize: 13 }}>
            Live data · Refreshed {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchData}
            style={{
              background: '#1e3a5f', color: '#38bdf8', border: '1px solid #38bdf844',
              borderRadius: 6, padding: '4px 12px', cursor: 'pointer', fontSize: 13,
            }}
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 20 }}>
        <div style={{ background: '#0f172a', borderRadius: 10, padding: '12px 16px', borderLeft: '3px solid #64748b' }}>
          <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>Total Clients</div>
          <div style={{ color: '#e2e8f0', fontSize: 24, fontWeight: 700 }}>{stats.total}</div>
        </div>
        <div style={{ background: '#0f172a', borderRadius: 10, padding: '12px 16px', borderLeft: '3px solid #34d399' }}>
          <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>Synced (OK)</div>
          <div style={{ color: '#34d399', fontSize: 24, fontWeight: 700 }}>{stats.ok}</div>
        </div>
        <div style={{ background: '#0f172a', borderRadius: 10, padding: '12px 16px', borderLeft: '3px solid #fbbf24' }}>
          <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>Warning</div>
          <div style={{ color: '#fbbf24', fontSize: 24, fontWeight: 700 }}>{stats.warning}</div>
        </div>
        <div style={{ background: '#0f172a', borderRadius: 10, padding: '12px 16px', borderLeft: '3px solid #f87171' }}>
          <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>Critical</div>
          <div style={{ color: '#f87171', fontSize: 24, fontWeight: 700 }}>{stats.critical}</div>
        </div>
      </div>

      {/* Filters + Search */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        {(['all', 'critical', 'warning', 'ok'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              background: filter === f ? '#1e3a5f' : '#0f172a',
              color: filter === f ? '#38bdf8' : '#64748b',
              border: `1px solid ${filter === f ? '#38bdf8' : '#1e293b'}`,
              borderRadius: 6,
              padding: '5px 14px',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: filter === f ? 600 : 400,
            }}
          >
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            {f === 'all' ? ` (${stats.total})` : f === 'critical' ? ` (${stats.critical})` : f === 'warning' ? ` (${stats.warning})` : ` (${stats.ok})`}
          </button>
        ))}
        <input
          type="text"
          placeholder="Search hostname or IP…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            background: '#0f172a',
            color: '#e2e8f0',
            border: '1px solid #1e293b',
            borderRadius: 6,
            padding: '5px 12px',
            fontSize: 13,
            width: 220,
            outline: 'none',
          }}
        />
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #1e293b' }}>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>Hostname</th>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>IP Address</th>
              <th style={{ textAlign: 'center', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>Status</th>
              <th style={{ textAlign: 'center', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>NTP Pkts</th>
              <th style={{ textAlign: 'center', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>Drop</th>
              <th style={{ textAlign: 'center', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>Interval</th>
              <th style={{ textAlign: 'center', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>Last Contact</th>
              <th style={{ textAlign: 'left', padding: '8px 10px', color: '#64748b', fontWeight: 600 }}>Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c, i) => {
              const isIP = (c.Hostname ?? c.Address) === c.Address;
              const displayName = c.Hostname || c.Address;
              return (
                <tr
                  key={`${c.Address}-${i}`}
                  style={{
                    borderBottom: '1px solid #1e293b22',
                    background: i % 2 === 0 ? 'transparent' : '#0f172a44',
                  }}
                >
                  <td style={{ padding: '6px 10px', color: '#e2e8f0', fontWeight: 500 }}>
                    {isIP ? (
                      <span style={{ color: '#94a3b8' }}>{displayName}</span>
                    ) : (
                      <span title={c.Address}>{displayName}</span>
                    )}
                  </td>
                  <td style={{ padding: '6px 10px', color: '#64748b', fontFamily: 'monospace', fontSize: 12 }}>
                    {isIP ? '—' : c.Address}
                  </td>
                  <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                    <StatusBadge status={c.Status} />
                  </td>
                  <td style={{ padding: '6px 10px', textAlign: 'center', color: '#94a3b8' }}>
                    {c.NTPPkts ?? '—'}
                  </td>
                  <td style={{ padding: '6px 10px', textAlign: 'center', color: c.Drop > 0 ? '#f87171' : '#94a3b8' }}>
                    {c.Drop}
                  </td>
                  <td style={{ padding: '6px 10px', textAlign: 'center', color: '#94a3b8' }}>
                    {c.Interval ? `${c.Interval}s` : '—'}
                  </td>
                  <td style={{ padding: '6px 10px', textAlign: 'center', color: '#e2e8f0' }}>
                    {formatLast(c.Last)}
                  </td>
                  <td style={{ padding: '6px 10px', color: '#64748b', fontSize: 11 }}>
                    {c.LastSeen ? new Date(c.LastSeen).toLocaleTimeString() : '—'}
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: 32, color: '#64748b' }}>
                  No matching clients
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 16, color: '#475569', fontSize: 12, textAlign: 'center' }}>
        Showing {filtered.length} of {stats.total} clients · Auto-refresh every 30s
      </div>
    </section>
  );
}