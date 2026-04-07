import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/layout/Layout';
import DashboardView from './components/dashboard/DashboardView';
import CommandCenter from './components/detection/CommandCenter';
import IdentityProfiling from './components/detection/IdentityProfiling';
import AnalyticsView from './components/analytics/AnalyticsView';
import InteractiveSimulator from './components/detection/InteractiveSimulator';
import ArchitectureView from './components/architecture/ArchitectureView';
import ReportsView from './components/reports/ReportsView';
import PoliciesView from './components/policies/PoliciesView';
import SettingsView from './components/settings/SettingsView';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { DashboardDataProvider } from './context/DashboardDataContext';
import Welcome from './components/welcome/Welcome';

/* Inner component — must live inside BrowserRouter to use useLocation */
function DashboardApp() {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState(location.state?.tab || 'dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':         return <DashboardView />;
      case 'command-center':   return <CommandCenter />;
      case 'identity-profiling': return <IdentityProfiling />;
      case 'analytics':        return <AnalyticsView />;
      case 'policies':         return <PoliciesView />;
      case 'detection':        return <InteractiveSimulator />;
      case 'architecture':     return <ArchitectureView />;
      case 'reports':          return <ReportsView />;
      case 'settings':         return <SettingsView />;
      default:                 return <div>Unknown View</div>;
    }
  };

  return (
    <Routes>
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/welcome"
        element={
          <ProtectedRoute>
            <Welcome />
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardDataProvider>
              <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
                {renderContent()}
              </Layout>
            </DashboardDataProvider>
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/welcome" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter basename="/VPN-Detection-Deanonymisation/">
          <DashboardApp />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
