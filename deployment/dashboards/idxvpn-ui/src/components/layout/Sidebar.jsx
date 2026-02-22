import React from 'react';
import { LayoutDashboard, BarChart2, Shield, Settings, Activity, LogOut, User } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../../context/AuthContext';

const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'analytics', label: 'Analytics & Deanonymisation', icon: BarChart2 },
    { id: 'policies', label: 'Policies', icon: Shield },
    { id: 'detection', label: 'Interactive Detection', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings }
];

const Sidebar = ({ activeTab, setActiveTab }) => {
    const { user, logout } = useAuth();
    return (
        <div className="w-64 glass-panel border-r border-divider flex flex-col h-screen fixed left-0 top-0 z-40 bg-panel backdrop-blur-xl transition-colors">
            <div className="p-6 border-b border-divider flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#4f8fff] to-[#2555ff] flex items-center justify-center font-bold text-default shadow-[0_0_15px_rgba(79,143,255,0.4)]">
                    ID
                </div>
                <h1 className="text-xl font-bold tracking-wide text-default">IDxVPN</h1>
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
                                ? 'bg-black/10 dark:bg-white/10 dark:bg-black/10 dark:bg-white/10 bg-black/5 text-default shadow-[inset_2px_0_0_#4f8fff]'
                                : 'text-muted hover:bg-black/5 dark:hover:bg-black/10 dark:bg-white/10 hover:text-default hover:translate-x-1'
                                }`}
                        >
                            <Icon size={20} className={isActive ? 'text-[#4f8fff]' : ''} />
                            <span className="font-medium text-sm text-left">{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            <div className="p-4 border-t border-divider space-y-4">
                {user && (
                    <div className="p-3 rounded-xl bg-black/5 dark:bg-black/40 border border-divider flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-[var(--bg-primary)] border border-divider flex items-center justify-center">
                                <User size={16} className="text-default" />
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-default capitalize">{user.username}</div>
                                <div className="text-xs text-muted capitalize">{user.role}</div>
                            </div>
                        </div>
                        <button onClick={logout} className="p-2 text-muted hover:text-[var(--accent-red)] hover:bg-red-500/10 rounded-lg transition-colors" title="Logout">
                            <LogOut size={16} />
                        </button>
                    </div>
                )}

                <ThemeToggle />

                <div className="p-3 rounded-xl bg-black/5 dark:bg-black/40 border border-divider flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-[#1bc553] shadow-[0_0_8px_#1bc553]"></div>
                    <div>
                        <div className="text-sm font-semibold text-default">Model Training</div>
                        <div className="text-xs text-muted">DigitalOcean Node active</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
