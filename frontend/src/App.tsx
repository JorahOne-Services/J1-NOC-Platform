import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import RequireAuth from './components/RequireAuth';
import Layout from './components/Layout';
import DashboardHome from './pages/DashboardHome';
import ChronyTab from './pages/ChronyTab';
import TicketsTab from './pages/TicketsTab';
import DnsTab from './pages/DnsTab';
import AdminPanel from './pages/AdminPanel';
import AIAssistant from './pages/AIAssistant';
import LDAPTab from './pages/LDAPTab';
import SNMPTab from './pages/SNMPTab';
import LoginPage from './pages/LoginPage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth><Layout /></RequireAuth>}>
          <Route path="/" element={<DashboardHome />} />
          <Route path="/ldap" element={<LDAPTab />} />
          <Route path="/snmp" element={<SNMPTab />} />
          <Route path="/chrony" element={<ChronyTab />} />
          <Route path="/tickets" element={<TicketsTab />} />
          <Route path="/dns" element={<DnsTab />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/ai" element={<AIAssistant />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}
