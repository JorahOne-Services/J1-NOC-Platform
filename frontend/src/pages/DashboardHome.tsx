import { useEffect, useState } from 'react';
import { get } from '../services/api';

export default function DashboardHome() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    get('dashboard/overview')
      .then((d) => setData(d))
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="loading">Loading overview…</div>;

  return (
    <section className="overview">
      <h1>Overview</h1>
      <div className="grid">
        <div className="card">
          <div className="card-title">Total Devices</div>
          <div className="card-value">{data.total_devices}</div>
        </div>
        <div className="card">
          <div className="card-title">Online Devices</div>
          <div className="card-value">{data.online_devices}</div>
        </div>
        <div className="card">
          <div className="card-title">Offline Devices</div>
          <div className="card-value">{data.offline_devices}</div>
        </div>
        <div className="card">
          <div className="card-title">Active Alerts</div>
          <div className="card-value">{data.active_alerts}</div>
        </div>
        <div className="card">
          <div className="card-title">Critical Alerts</div>
          <div className="card-value">{data.critical_alerts}</div>
        </div>
        <div className="card">
          <div className="card-title">Open Tickets</div>
          <div className="card-value">{data.open_tickets}</div>
        </div>
      </div>
    </section>
  );
}