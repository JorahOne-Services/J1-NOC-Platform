import { useEffect, useState } from 'react';
import { get } from '../services/api';

type Overview = {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  active_alerts: number;
  critical_alerts: number;
  open_tickets: number;
};

export default function DashboardHome() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    get('dashboard/overview')
      .then(d => { if (!cancelled) setData(d) })
      .catch(e => { if (!cancelled) setError(e.message) });
    return () => { cancelled = true };
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="loading">Loading overview…</div>;

  return (
    <section className="overview">
      <h1>Overview</h1>
      <div className="grid">
        <Card title="Total Devices" value={data.total_devices} />
        <Card title="Online Devices" value={data.online_devices} />
        <Card title="Offline Devices" value={data.offline_devices} />
        <Card title="Active Alerts" value={data.active_alerts} />
        <Card title="Critical Alerts" value={data.critical_alerts} />
        <Card title="Open Tickets" value={data.open_tickets} />
      </div>
    </section>
  );
}

function Card({ title, value }: { title: string; value: number }) {
  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="card-value">{value}</div>
    </div>
  );
}
