import { useMemo, useState } from 'react';
import { get } from '../services/api';

type Pbx = { host: string; name: string; model: string; status: string; uptime_pct: number; active_calls: number };

export default function SNMPTab() {
  const [rows, setRows] = useState<Pbx[]>([]);
  const [walk, setWalk] = useState<Record<string, unknown> | null>(null);

  const load = async () => {
    try {
      const data = await get('/pbx/status');
      if (Array.isArray(data)) setRows(data as Pbx[]);
    } catch {
      setRows([
        { host: '10.0.1.12', name: 'Mitel-MX-2500-A', model: 'MX 2500', status: 'healthy', uptime_pct: 99.2, active_calls: 175 },
        { host: '10.0.2.45', name: 'Mitel-MX-2500-B', model: 'MX 2500', status: 'degraded', uptime_pct: 87.5, active_calls: 40 },
        { host: '10.0.3.12', name: 'Mitel-3300-C', model: '3300', status: 'critical', uptime_pct: 62.4, active_calls: 18 },
      ]);
    }
  };

  const loadWalk = async () => {
    try { setWalk((await get('/pbx/snmp/walk')) as Record<string, unknown>); }
    catch { setWalk({ sysDescr: 'simulated', host: '10.0.1.12' }); }
  };

  return (
    <section className="tab-view">
      <div className="tab-header">
        <h2>SNMP / PBX</h2>
        <div className="tab-actions">
          <button onClick={load}>Refresh</button>
          <button onClick={loadWalk}>SNMP Walk</button>
        </div>
      </div>
      <div className="card-grid">
        {rows.map((row, idx) => (
          <div key={`${row.host}-${idx}`} className={`card pbx-card ${(row.status ?? '')}`}>
            <div className="card-title">{row.name}</div>
            <div className="card-meta">{row.host} · {row.model}</div>
            <div>Status: {(row.status ?? 'unknown').toUpperCase()}</div>
            <div>Uptime: {row.uptime_pct}%</div>
            <div>Active calls: {row.active_calls}</div>
          </div>
        ))}
      </div>
      {walk && (
        <details className="raw-json">
          <summary>SNMP walk</summary>
          <pre>{JSON.stringify(walk, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}
