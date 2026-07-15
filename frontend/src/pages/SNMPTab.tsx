import { useEffect, useState, useCallback } from 'react';
import { get } from '../services/api';

/* ── Types ─────────────────────────────────────────────────────────────── */

interface Iface {
  index: string; name: string; operStatus: string; adminStatus: string;
  speed: string; speed_human: string; inOctets: string; outOctets: string;
}

interface StorageEntry {
  type: string; name: string; index: string;
  size_gb?: number; used_gb?: number; used_pct: number;
  total_mb?: number; used_mb?: number;
  size_blocks?: number; used_blocks?: number; units?: number;
}

interface CpuCore { core: string; load_pct: number | string; }

interface MitelAlarms { active: number; major: number; minor: number; info: number; }

interface Device {
  host: string; hostname: string; name: string; role: string; status: string;
  sysDescr: string | null; model: string | null; hardware: string | null;
  software_version: string | null; agent_version: string | null;
  mcd_version: string | null; platform: string | null;
  sysUpTime: { raw: number | null; days: number; hours: number; minutes: number; seconds: number; human: string } | null;
  sysContact: string | null; sysLocation: string | null; sysServices: string | null;
  processes: number; cpu_cores: CpuCore[]; cpu_avg: number;
  memory: { total_mb: number; used_mb: number; used_pct: number };
  storage: StorageEntry[];
  interfaceCount: number; ipAddresses: { address: string; mask: string }[];
  interfaces: Iface[];
  tcp_connections: number; tcp_active_opens: number;
  tcp_in_segs: number; tcp_out_segs: number; tcp_retrans_segs: number;
  tcp_ports: number[]; udp_ports: number[];
  mitel_alarms: MitelAlarms; mitel_version: string | null;
  mitel_slots_total: string | null; mitel_slots_available: string | null;
  mitel_processes: { pid: string; name: string }[];
  collected_at: string;
}

type Filter = 'all' | 'healthy' | 'snmp_timeout' | 'down';

/* ── Helpers ────────────────────────────────────────────────────────────── */

const STATUS_CFG: Record<string, { bg: string; text: string; label: string }> = {
  healthy:      { bg: '#059669', text: '#fff', label: 'Healthy' },
  degraded:     { bg: '#d97706', text: '#fff', label: 'Degraded' },
  snmp_timeout: { bg: '#b45309', text: '#fff', label: 'SNMP Timeout' },
  down:         { bg: '#dc2626', text: '#fff', label: 'Down' },
};

function Badge({ status }: { status: string }) {
  const cfg = STATUS_CFG[status] ?? STATUS_CFG.down;
  return <span style={{ background: cfg.bg, color: cfg.text, padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>{cfg.label}</span>;
}

function fmtOctets(o: string | undefined): string {
  if (!o || o === '0') return '0 B';
  const n = parseInt(o, 10); if (isNaN(n)) return o;
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)} GB`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} MB`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)} KB`;
  return `${n} B`;
}

function pctBar(pct: number, color: string) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
      <div style={{ flex: 1, background: '#334155', borderRadius: 3, height: 8, overflow: 'hidden' }}>
        <div style={{ width: `${Math.min(pct, 100)}%`, background: color, height: '100%', borderRadius: 3 }} />
      </div>
      <span style={{ color: '#94a3b8', fontSize: 11, minWidth: 36 }}>{pct}%</span>
    </div>
  );
}

/* ── Component ──────────────────────────────────────────────────────────── */

export default function SNMPTab() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [filter, setFilter] = useState<Filter>('all');
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const load = useCallback(async () => {
    try { const data = await get('/pbx/status'); if (Array.isArray(data)) setDevices(data as Device[]); } catch {}
    setLastRefresh(new Date());
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { const id = setInterval(load, 30000); return () => clearInterval(id); }, [load]);

  const filtered = devices.filter(d => {
    if (filter !== 'all' && d.status !== filter) return false;
    if (search) {
      const q = search.toLowerCase();
      return d.host.includes(q) || (d.hostname || '').toLowerCase().includes(q) ||
             (d.name || '').toLowerCase().includes(q) || (d.model || '').toLowerCase().includes(q);
    }
    return true;
  });

  const counts = {
    total: devices.length,
    healthy: devices.filter(d => d.status === 'healthy').length,
    snmp_timeout: devices.filter(d => d.status === 'snmp_timeout').length,
    down: devices.filter(d => d.status === 'down').length,
  };

  const filterBtns: { key: Filter; label: string; color: string }[] = [
    { key: 'all', label: `All (${counts.total})`, color: '#475569' },
    { key: 'healthy', label: `Healthy (${counts.healthy})`, color: '#059669' },
    { key: 'snmp_timeout', label: `Timeout (${counts.snmp_timeout})`, color: '#b45309' },
    { key: 'down', label: `Down (${counts.down})`, color: '#dc2626' },
  ];

  return (
    <section className="tab-view">
      <div className="tab-header">
        <h2>SNMP / PBX</h2>
        <div className="tab-actions">
          <span style={{ fontSize: 13, color: '#94a3b8', marginRight: 8 }}>{lastRefresh.toLocaleTimeString()}</span>
          <button onClick={load}>Refresh</button>
        </div>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 16 }}>
        {[
          { label: 'Total Devices', value: counts.total, color: '#3b82f6' },
          { label: 'Healthy', value: counts.healthy, color: '#059669' },
          { label: 'Timeout', value: counts.snmp_timeout, color: '#b45309' },
          { label: 'Down', value: counts.down, color: '#dc2626' },
        ].map(c => (
          <div key={c.label} style={{ background: '#1e293b', borderRadius: 8, padding: 14, borderLeft: `4px solid ${c.color}` }}>
            <div style={{ color: '#94a3b8', fontSize: 11 }}>{c.label}</div>
            <div style={{ color: '#f1f5f9', fontSize: 26, fontWeight: 700 }}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* Filter / Search */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        {filterBtns.map(b => (
          <button key={b.key} onClick={() => setFilter(b.key)} style={{
            padding: '4px 12px', borderRadius: 14, fontSize: 13, fontWeight: 600,
            border: filter === b.key ? `2px solid ${b.color}` : '1px solid #334155',
            background: filter === b.key ? b.color : '#1e293b',
            color: filter === b.key ? '#fff' : '#94a3b8', cursor: 'pointer',
          }}>{b.label}</button>
        ))}
        <input placeholder="Search host / name / model…" value={search} onChange={e => setSearch(e.target.value)} style={{
          marginLeft: 'auto', padding: '4px 10px', borderRadius: 6, background: '#1e293b',
          border: '1px solid #334155', color: '#f1f5f9', fontSize: 13, width: 220,
        }} />
      </div>

      {filtered.length === 0 && <div style={{ color: '#94a3b8', padding: 32, textAlign: 'center' }}>No devices found</div>}

      {filtered.map(d => {
        const isExpanded = expanded === d.host;
        const ut = d.sysUpTime;
        const mem = d.memory;
        const disks = (d.storage || []).filter(s => s.type === 'disk');
        const memEntries = (d.storage || []).filter(s => s.type === 'memory');
        const alarmInfo = d.mitel_alarms;

        return (
          <div key={d.host} style={{
            background: '#1e293b', borderRadius: 8, marginBottom: 8, overflow: 'hidden',
            border: `1px solid ${d.status === 'healthy' ? '#05966933' : d.status === 'down' ? '#dc262633' : '#b4530933'}`,
          }}>
            {/* ── Card header ── */}
            <div style={{ display: 'flex', alignItems: 'center', padding: '10px 14px', cursor: 'pointer', gap: 12 }}
              onClick={() => setExpanded(isExpanded ? null : d.host)}>
              <Badge status={d.status} />
              <div style={{ flex: 1 }}>
                <span style={{ color: '#f1f5f9', fontWeight: 600 }}>{d.name || d.hostname || d.host}</span>
                <span style={{ color: '#64748b', fontSize: 12, marginLeft: 8 }}>{d.host}</span>
                {d.model && <span style={{ color: '#94a3b8', fontSize: 12, marginLeft: 8 }}>{d.model}</span>}
                <span style={{ color: '#475569', fontSize: 11, marginLeft: 8 }}>{d.role}</span>
              </div>
              {ut && ut.human && <span style={{ color: '#94a3b8', fontSize: 12 }}>⏱ {ut.human}</span>}
              {mem && <span style={{ color: mem.used_pct > 90 ? '#dc2626' : '#94a3b8', fontSize: 12 }}>💾 {mem.used_pct}%</span>}
              {d.cpu_avg !== undefined && <span style={{ color: d.cpu_avg > 80 ? '#dc2626' : '#94a3b8', fontSize: 12 }}>⚡ {d.cpu_avg}%</span>}
              {d.processes > 0 && <span style={{ color: '#64748b', fontSize: 12 }}>🔤 {d.processes}</span>}
              {d.tcp_connections > 0 && <span style={{ color: '#64748b', fontSize: 12 }}>🔗 {d.tcp_connections}</span>}
              <span style={{ color: '#64748b', fontSize: 11 }}>▼</span>
            </div>

            {/* ── Expanded detail ── */}
            {isExpanded && (
              <div style={{ padding: '0 14px 14px', borderTop: '1px solid #334155' }}>

                {/* Mitel Alarms */}
                {alarmInfo && (alarmInfo.active > 0 || alarmInfo.major > 0) && (
                  <div style={{ background: '#0f172a', borderRadius: 6, padding: 10, marginBottom: 10, borderLeft: '3px solid #dc2626' }}>
                    <span style={{ color: '#f1f5f9', fontWeight: 600, fontSize: 13 }}>⚠ Mitel Alarms: </span>
                    <span style={{ color: alarmInfo.active > 0 ? '#f87171' : '#94a3b8', fontSize: 13 }}>{alarmInfo.active} active</span>
                    <span style={{ color: '#94a3b8', fontSize: 12, marginLeft: 8 }}>| {alarmInfo.major} major | {alarmInfo.minor} minor | {alarmInfo.info} info</span>
                  </div>
                )}

                {/* System Info grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 24px', fontSize: 13, marginBottom: 10 }}>
                  {d.hardware && <><span style={{ color: '#64748b' }}>Hardware:</span><span style={{ color: '#e2e8f0' }}>{d.hardware}</span></>}
                  {d.software_version && <><span style={{ color: '#64748b' }}>Software:</span><span style={{ color: '#e2e8f0' }}>{d.software_version}</span></>}
                  {d.agent_version && <><span style={{ color: '#64748b' }}>Agent:</span><span style={{ color: '#e2e8f0' }}>{d.agent_version}</span></>}
                  {d.mcd_version && <><span style={{ color: '#64748b' }}>MCD:</span><span style={{ color: '#e2e8f0' }}>{d.mcd_version}</span></>}
                  {d.sysContact && <><span style={{ color: '#64748b' }}>Contact:</span><span style={{ color: '#e2e8f0' }}>{d.sysContact}</span></>}
                  {d.sysLocation && <><span style={{ color: '#64748b' }}>Location:</span><span style={{ color: '#e2e8f0' }}>{d.sysLocation}</span></>}
                  {d.mitel_version && <><span style={{ color: '#64748b' }}>Slots:</span><span style={{ color: '#e2e8f0' }}>{d.mitel_slots_available ?? '?'} / {d.mitel_slots_total ?? '?'}</span></>}
                  {d.mitel_version && <><span style={{ color: '#64748b' }}>Mitel Ver:</span><span style={{ color: '#e2e8f0' }}>{d.mitel_version}</span></>}
                </div>

                {/* CPU Cores */}
                {d.cpu_cores && d.cpu_cores.length > 0 && (
                  <div style={{ marginBottom: 10 }}>
                    <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>CPU ({d.cpu_cores.length} core{d.cpu_cores.length > 1 ? 's' : ''}, avg {d.cpu_avg}%)</span>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                      {d.cpu_cores.map((c, i) => {
                        const load = typeof c.load_pct === 'number' ? c.load_pct : parseInt(String(c.load_pct)) || 0;
                        const color = load > 80 ? '#dc2626' : load > 50 ? '#d97706' : '#059669';
                        return <span key={i} style={{ background: '#0f172a', padding: '3px 8px', borderRadius: 4, fontSize: 11, color }}>Core {i}: {load}%</span>;
                      })}
                    </div>
                  </div>
                )}

                {/* Memory */}
                {mem && (
                  <div style={{ marginBottom: 10 }}>
                    <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>
                      Memory: {mem.used_mb?.toFixed(0)} / {mem.total_mb?.toFixed(0)} MB
                    </span>
                    <div style={{ marginTop: 4 }}>{pctBar(mem.used_pct, mem.used_pct > 90 ? '#dc2626' : mem.used_pct > 70 ? '#d97706' : '#059669')}</div>
                  </div>
                )}

                {/* Disks */}
                {disks.length > 0 && (
                  <div style={{ marginBottom: 10 }}>
                    <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>Disks</span>
                    <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse', marginTop: 4 }}>
                      <thead><tr style={{ color: '#64748b', borderBottom: '1px solid #334155' }}>
                        <th style={{ textAlign: 'left', padding: '2px 6px' }}>Mount</th>
                        <th style={{ textAlign: 'right', padding: '2px 6px' }}>Used</th>
                        <th style={{ textAlign: 'right', padding: '2px 6px' }}>Size</th>
                        <th style={{ padding: '2px 6px', width: '40%' }}>Usage</th>
                      </tr></thead>
                      <tbody>{disks.map(s => (
                        <tr key={s.index} style={{ borderBottom: '1px solid #1e293b' }}>
                          <td style={{ padding: '2px 6px', color: '#e2e8f0' }}>{s.name}</td>
                          <td style={{ padding: '2px 6px', textAlign: 'right', color: '#94a3b8' }}>{s.used_gb?.toFixed(1)} GB</td>
                          <td style={{ padding: '2px 6px', textAlign: 'right', color: '#94a3b8' }}>{s.size_gb?.toFixed(1)} GB</td>
                          <td style={{ padding: '2px 6px' }}>{pctBar(s.used_pct, s.used_pct > 90 ? '#dc2626' : s.used_pct > 70 ? '#d97706' : '#059669')}</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                )}

                {/* IP Addresses */}
                {d.ipAddresses && d.ipAddresses.length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>IP Addresses: </span>
                    {d.ipAddresses.map((ip, i) => (
                      <span key={i} style={{ color: '#e2e8f0', fontSize: 12, marginRight: 12 }}>{ip.address}/{ip.mask}</span>
                    ))}
                  </div>
                )}

                {/* Interfaces */}
                {d.interfaces && d.interfaces.length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>Interfaces</span>
                    <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse', marginTop: 4 }}>
                      <thead><tr style={{ color: '#64748b', borderBottom: '1px solid #334155' }}>
                        <th style={{ textAlign: 'left', padding: '2px 6px' }}>Name</th>
                        <th style={{ padding: '2px 6px' }}>Status</th>
                        <th style={{ padding: '2px 6px' }}>Speed</th>
                        <th style={{ textAlign: 'right', padding: '2px 6px' }}>In</th>
                        <th style={{ textAlign: 'right', padding: '2px 6px' }}>Out</th>
                      </tr></thead>
                      <tbody>{d.interfaces.filter(i => i.name !== 'lo').map(i => (
                        <tr key={i.index} style={{ borderBottom: '1px solid #1e293b' }}>
                          <td style={{ padding: '2px 6px', color: '#e2e8f0' }}>{i.name}</td>
                          <td style={{ padding: '2px 6px' }}><span style={{ color: i.operStatus === 'up' ? '#059669' : '#dc2626', fontWeight: 600 }}>{i.operStatus}</span></td>
                          <td style={{ padding: '2px 6px', color: '#94a3b8' }}>{i.speed_human}</td>
                          <td style={{ padding: '2px 6px', textAlign: 'right', color: '#94a3b8' }}>{fmtOctets(i.inOctets)}</td>
                          <td style={{ padding: '2px 6px', textAlign: 'right', color: '#94a3b8' }}>{fmtOctets(i.outOctets)}</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>
                )}

                {/* TCP/UDP */}
                {d.tcp_connections > 0 && (
                  <div style={{ marginBottom: 8, fontSize: 12, color: '#94a3b8' }}>
                    <span style={{ fontWeight: 600 }}>TCP:</span> {d.tcp_connections} established
                    {d.tcp_in_segs !== undefined && <> · {fmtOctets(String(d.tcp_in_segs))} in / {fmtOctets(String(d.tcp_out_segs))} out</>}
                    {d.tcp_ports && d.tcp_ports.length > 0 && (
                      <div style={{ marginTop: 2, color: '#64748b' }}>
                        Listening: [{d.tcp_ports.filter(p => p < 1024).join(', ')}]
                        {d.tcp_ports.filter(p => p >= 1024).length > 0 && <> +{d.tcp_ports.filter(p => p >= 1024).length} more</>}
                      </div>
                    )}
                  </div>
                )}

                {/* Mitel processes */}
                {d.mitel_processes && d.mitel_processes.length > 0 && (
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>Mitel Processes: </span>
                    {d.mitel_processes.map((p, i) => (
                      <span key={i} style={{ background: '#0f172a', padding: '2px 8px', borderRadius: 4, fontSize: 11, color: '#e2e8f0', marginRight: 4 }}>
                        {p.name} <span style={{ color: '#64748b' }}>(PID {p.pid})</span>
                      </span>
                    ))}
                  </div>
                )}

                {d.collected_at && (
                  <div style={{ color: '#475569', fontSize: 11, marginTop: 6 }}>
                    Collected: {new Date(d.collected_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </section>
  );
}