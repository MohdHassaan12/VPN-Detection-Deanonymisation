import React, { useState } from 'react';
import Layout from './components/layout/Layout';
import DashboardView from './components/dashboard/DashboardView';
import AnalyticsView from './components/analytics/AnalyticsView';
import InteractiveSimulator from './components/detection/InteractiveSimulator';
import PoliciesView from './components/policies/PoliciesView';
import SettingsView from './components/settings/SettingsView';

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
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderContent()}
    </Layout>
  );
}

export default App;
