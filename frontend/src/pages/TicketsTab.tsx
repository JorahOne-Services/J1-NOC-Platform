import { useEffect, useState } from 'react';
import { get } from '../services/api';

type Ticket = Record<string, unknown>;

export default function TicketsTab() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const rows: Ticket[] = await get('/helpdesk/tickets');
      setTickets(Array.isArray(rows) ? rows : sampleTickets());
    } catch {
      setErr('Failed to fetch tickets. Sample data loaded.');
      setTickets(sampleTickets());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const open = tickets.filter((t) => String(t.status) !== 'Closed').length;
  const high = tickets.filter((t) => ['High', 'Critical'].includes(String(t.priority))).length;

  return (
    <section className="panel">
      <div className="panel-header">
        <h1>🎫 osTicket / Helpdesk</h1>
        <div className="panel-actions">
          <button disabled={loading} onClick={load}>🔄 Refresh</button>
        </div>
      </div>
      {err && <div className="warn-banner">{err}</div>}
      <div className="stats-row">
        <Stat title="Open / In Progress" value={open} />
        <Stat title="High / Critical" value={high} color="warn" />
        <Stat title="Total Tickets" value={tickets.length} />
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Ticket#</th>
              <th>Name</th>
              <th>Email</th>
              <th>Subject</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={String(t.id)}>
                <td className="mono">{t.id}</td>
                <td>{t.name}</td>
                <td>{t.email ?? '-'}</td>
                <td>{t.subject}</td>
                <td>
                  <PriorityPill priority={String(t.priority)} />
                </td>
                <td>
                  <StatusPill status={String(t.status)} />
                </td>
                <td>{new Date(String(t.created)).toLocaleString()}</td>
              </tr>
            ))}
            {!tickets.length && (
              <tr>
                <td colSpan={7} className="empty">
                  No tickets loaded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PriorityPill({ priority }: { priority: string }) {
  const color = priority === 'Critical' ? 'var(--err)' : priority === 'High' ? 'var(--warn)' : 'var(--ok)';
  return <span className={`pill pill-${priority.toLowerCase()}`}>{priority}</span>;
}

function StatusPill({ status }: { status: string }) {
  const color = status === 'Closed' ? 'var(--dim)' : status === 'In Progress' ? 'var(--warn)' : 'var(--ok)';
  return <span className={`pill pill-${status.toLowerCase().replace(' ', '-')}`}>{status}</span>;
}

function Stat({ title, value, color }: { title: string; value: number; color?: string }) {
  return (
    <div className={`stat ${color ? `stat-${color}` : ''}`}>
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function sampleTickets(): Ticket[] {
  return [
    { id: '14554', name: 'John Smith', status: 'In Progress', priority: 'Low', subject: 'Firewall rule change', created: new Date(Date.now() - 2 * 3600e3).toISOString(), email: 'noc@vide.vi' },
    { id: '15953', name: 'Bob Johnson', status: 'In Progress', priority: 'Medium', subject: 'Mitel extension not working', created: new Date(Date.now() - 6 * 3600e3).toISOString(), email: 'user2@vide.vi' },
    { id: '9772', name: 'Bob Johnson', status: 'Open', priority: 'High', subject: 'Ticket escalation #4521', created: new Date(Date.now() - 12 * 3600e3).toISOString(), email: 'user1@vide.vi' },
    { id: '16953', name: 'John Smith', status: 'In Progress', priority: 'Critical', subject: 'Network switch port down Meraki', created: new Date(Date.now() - 18 * 3600e3).toISOString(), email: 'user2@vide.vi' },
    { id: '10087', name: 'Charlie Davis', status: 'Closed', priority: 'Medium', subject: 'VPN disconnect', created: new Date(Date.now() - 48 * 3600e3).toISOString(), email: 'noc@vide.vi' },
    { id: '9624', name: 'Eve Wilson', status: 'In Progress', priority: 'Critical', subject: 'SERVER-PATCH-MEM-02 alert', created: new Date(Date.now() - 53 * 3600e3).toISOString(), email: 'noc@vide.vi' },
  ];
}
