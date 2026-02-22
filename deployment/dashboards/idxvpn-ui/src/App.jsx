import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import DashboardView from './components/dashboard/DashboardView';
import AnalyticsView from './components/analytics/AnalyticsView';
import InteractiveSimulator from './components/detection/InteractiveSimulator';
import PoliciesView from './components/policies/PoliciesView';
import SettingsView from './components/settings/SettingsView';
import Login from './components/auth/Login';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { DashboardDataProvider } from './context/DashboardDataContext';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'analytics':
        return <AnalyticsView />;
      case 'policies':
        return <PoliciesView />;
      case 'detection':
        return <InteractiveSimulator />;
      case 'settings':
        return <SettingsView />;
      default:
        return <div>Unknown View</div>;
    }
  };

  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            {/* Protected Dashboard Layout */}
            <Route
              path="/"
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

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
