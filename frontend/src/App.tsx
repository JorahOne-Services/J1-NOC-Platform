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
import WazuhSIEM from './pages/WazuhSIEM';
import LoginPage from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/setup" element={<OnboardingPage />} />

        {/* Public dashboard (no auth required) */}
        <Route path="/" element={<DashboardHome />} />

        {/* Protected area: admin + operator tabs */}
        <Route element={<RequireAuth><Layout /></RequireAuth>}>
          <Route path="/ldap" element={<LDAPTab />} />
          <Route path="/snmp" element={<SNMPTab />} />
          <Route path="/chrony" element={<ChronyTab />} />
          <Route path="/tickets" element={<TicketsTab />} />
          <Route path="/dns" element={<DnsTab />} />
          <Route path="/admin/*" element={<AdminPanel />} />
          <Route path="/ai" element={<AIAssistant />} />
          <Route path="/wazuh" element={<WazuhSIEM />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
