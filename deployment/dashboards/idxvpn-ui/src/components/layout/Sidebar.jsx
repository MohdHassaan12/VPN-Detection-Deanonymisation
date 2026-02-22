import React from 'react';
import { LayoutDashboard, BarChart2, Shield, Settings, Activity } from 'lucide-react';

const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'analytics', label: 'Analytics & Deanonymisation', icon: BarChart2 },
    { id: 'policies', label: 'Policies', icon: Shield },
    { id: 'detection', label: 'Interactive Detection', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings }
];

const Sidebar = ({ activeTab, setActiveTab }) => {
    return (
        <div className="w-64 glass-panel border-r border-[#ffffff1a] flex flex-col h-screen fixed left-0 top-0 z-40 bg-[#151923]/80 backdrop-blur-xl">
            <div className="p-6 border-b border-[#ffffff1a] flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#4f8fff] to-[#2555ff] flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(79,143,255,0.4)]">
                    ID
                </div>
                <h1 className="text-xl font-bold tracking-wide text-white">IDxVPN</h1>
            </div>

            <nav className="flex-1 px-4 py-8 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${isActive
                                    ? 'bg-[#ffffff1a] text-white shadow-[inset_2px_0_0_#4f8fff]'
                                    : 'text-[#a0aabf] hover:bg-[#ffffff0d] hover:text-white hover:translate-x-1'
                                }`}
                        >
                            <Icon size={20} className={isActive ? 'text-[#4f8fff]' : ''} />
                            <span className="font-medium text-sm text-left">{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-[#ffffff1a]">
                <div className="p-3 rounded-xl bg-[#00000040] border border-[#ffffff0d] flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-[#1bc553] shadow-[0_0_8px_#1bc553]"></div>
                    <div>
                        <div className="text-sm font-semibold text-white">Model Training</div>
                        <div className="text-xs text-[#a0aabf]">DigitalOcean Node active</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
