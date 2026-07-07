import { useEffect, useState } from 'react';
import { get } from '../services/api';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';

type Kpis = {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  active_alerts: number;
  critical_alerts: number;
  open_tickets: number;
};

type Service = { name: string; status: 'up' | 'down' };

type Overview = {
  kpis: Kpis;
  services: Service[];
  healthy: number;
  total_services: number;
};

const COLORS = ['#00ff9d', '#ff3860', '#00f3ff'];

export default function DashboardHome() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    get('system/overview')
      .then((d) => {
        if (!cancelled) setData(d as Overview);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (loading || !data) return <div className="loading">Loading operations overview…</div>;

  const { kpis, services, healthy, total_services } = data;
  const deviceData = [
    { name: 'Online', value: kpis.online_devices },
    { name: 'Offline', value: kpis.offline_devices },
    { name: 'Alerts', value: kpis.active_alerts },
  ];

  return (
    <section className="overview">
      <header className="overview-head">
        <h1>Operations Overview</h1>
        <span className={`ops-badge ${healthy === total_services ? 'ok' : 'warn'}`}>
          {healthy}/{total_services} services healthy
        </span>
      </header>

      <div className="kpi-grid">
        <Kpi label="Total Devices" value={kpis.total_devices} tone="primary" />
        <Kpi label="Online Devices" value={kpis.online_devices} tone="ok" />
        <Kpi label="Offline Devices" value={kpis.offline_devices} tone="err" />
        <Kpi label="Active Alerts" value={kpis.active_alerts} tone="warn" />
        <Kpi label="Critical Alerts" value={kpis.critical_alerts} tone="err" />
        <Kpi label="Open Tickets" value={kpis.open_tickets} tone="primary" />
      </div>

      <div className="overview-body">
        <div className="panel">
          <h2>Device Health</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={deviceData}
                dataKey="value"
                nameKey="name"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={2}
              >
                {deviceData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: '#0c0c28',
                  border: '1px solid rgba(0,243,255,0.18)',
                  color: '#e0e0ff',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h2>Service Status</h2>
          <ul className="svc-list">
            {services.map((s) => (
              <li key={s.name} className="svc-row">
                <span className="svc-name">{s.name}</span>
                <span className={`svc-dot ${s.status}`} />
                <span className={`svc-status ${s.status}`}>{s.status.toUpperCase()}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

function Kpi({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: 'primary' | 'ok' | 'err' | 'warn';
}) {
  return (
    <div className={`kpi kpi-${tone}`}>
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}
