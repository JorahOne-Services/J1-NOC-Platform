import { useEffect, useState } from 'react';
import { get } from '../services/api';

type Pbx = { host: string; name: string; model: string; status: string; uptime_pct: number; active_calls: number };
type Snmp = Record<string, Record<string, unknown>>;

export default function SNMPTab() {
  const [pbxes, setPbxes] = useState<Pbx[]>([]);
  const [snmp, setSnmp] = useState<Snmp | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadPbx = async () => {
    setLoading(true);
    setErr(null);
    try {
      const rows: Pbx[] = await get('/pbx/status');
      setPbxes(rows);
      return rows;
    } catch (e: any) {
      setErr('PBX fetch failed. Sample data loaded.');
      setPbxes(samplePbx());
      return [] as Pbx[];
    } finally {
      setLoading(false);
    }
  };

  const loadSnmp = async () => {
    setLoading(true);
    try {
      const rows = await get('/pbx/snmp/walk');
      setSnmp(rows as Snmp);
    } catch {
      setSnmp(sampleSnmp() as Snmp);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPbx();
  }, []);

  const healthy = pbxes.filter((d) => d.status === 'healthy').length;
  const degraded = pbxes.filter((d) => d.status === 'degraded').length;
  const critical = pbxes.filter((d) => d.status === 'critical').length;

  return (
    <section className="panel">
      <div className="panel-header">
        <h1>📞 Mitel PBX / SNMP</h1>
        <div className="panel-actions">
          <button disabled={loading} onClick={loadPbx}>🔄 Refresh</button>
          <button disabled={loading} onClick={loadSnmp}>📡 SNMP Walk</button>
        </div>
      </div>
      {err && <div className="warn-banner">{err}</div>}
      <div className="stats-row">
        <Stat title="Total PBXs" value={pbxes.length} />
        <Stat title="Healthy" value={healthy} color="ok" />
        <Stat title="Degraded" value={degraded} color="warn" />
        <Stat title="Critical" value={critical} color="err" />
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Host</th>
              <th>Model</th>
              <th>Status</th>
              <th>Uptime %</th>
              <th>Active Calls</th>
            </tr>
          </thead>
          <tbody>
            {pbxes.map((row, idx) => (
              <tr key={`${row.host}-${idx}`}>
                <td>{row.name}</td>
                <td className="mono">{row.host}</td>
                <td>{row.model}</td>
                <td>
                  <StatusDot status={row.status} />
                </td>
                <td>{row.uptime_pct.toFixed(1)}%</td>
                <td>{row.active_calls}</td>
              </tr>
            ))}
            {!pbxes.length && (
              <tr>
                <td colSpan={6} className="empty">
                  No PBX data loaded.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {snmp && (
        <div className="snmp">
          <h2>📡 SNMP Walk — {Object.keys(snmp)[0]}</h2>
          <pre className="snmp-pre">{JSON.stringify(snmp, null, 2)}</pre>
        </div>
      )}
    </section>
  );
}

function StatusDot({ status }: { status: string }) {
  const color = status === 'healthy' ? 'var(--ok)' : status === 'degraded' ? 'var(--warn)' : status === 'critical' ? 'var(--err)' : 'var(--dim)';
  return <span style={{ color }}>{status.toUpperCase()}</span>;
}

function Stat({ title, value, color }: { title: string; value: number; color?: string }) {
  return (
    <div className={`stat ${color ? `stat-${color}` : ''}`}>
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function samplePbx(): Pbx[] {
  return [
    { host: '10.0.1.12', name: 'Mitel-MX-2500-A', model: 'MX 2500', status: 'healthy', uptime_pct: 99.2, active_calls: 175 },
    { host: '10.0.2.45', name: 'Mitel-MX-2500-B', model: 'MX 2500', status: 'degraded', uptime_pct: 87.5, active_calls: 40 },
    { host: '10.0.3.12', name: 'Mitel-3300-C', model: '3300', status: 'critical', uptime_pct: 62.4, active_calls: 18 },
  ];
}

function sampleSnmp(): Snmp {
  return {
    '10.0.1.12': {
      sysDescr: 'Mitel MX 2500',
      sysUpTime: 1234567,
      ifNumber: 6,
      ifDescr: ['eth0', 'eth1', 'ppp0', 'vlan10', 'vlan20', 'vlan99'],
      ifOperStatus: [1, 1, 2, 1, 1, 2],
      ifInOctets: [123456789, 987654321, 0, 456789123, 321654987, 0],
      ifOutOctets: [987654321, 123456789, 0, 321654987, 456789123, 0],
      ssosID: ['101', '102', '103', '104', '105', '106'],
      ssosActive: [45, 120, 0, 80, 210, 0],
      snmpInPkts: 54321,
      snmpOutPkts: 54319,
    },
  };
}
