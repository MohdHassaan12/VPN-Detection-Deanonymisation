import React from 'react';
import { LayoutDashboard, BarChart2, Shield, Settings, Activity, LogOut, User, Globe, Fingerprint, Layers, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../../context/AuthContext';
import shieldLogo from '../../assets/idxvpn-shield-logo.png';

const navItems = [
    { id: 'dashboard', label: 'Dashboard',                   icon: LayoutDashboard },
    { id: 'command-center', label: 'Command Center',         icon: Globe },
    { id: 'identity-profiling', label: 'Deanonymisation Core', icon: Fingerprint },
    { id: 'analytics', label: 'Analytics', icon: BarChart2 },
    { id: 'policies',  label: 'Policies',                    icon: Shield },
    { id: 'detection', label: 'Interactive Detection',       icon: Activity },
    { id: 'architecture', label: 'Architecture',              icon: Layers },
    { id: 'reports',      label: 'Reports & Threats',         icon: FileText },
    { id: 'settings',  label: 'Settings',                    icon: Settings },
];

const Sidebar = ({ activeTab, setActiveTab }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    return (
        <div
            className="w-64 flex flex-col h-screen fixed left-0 top-0 z-40 transition-colors"
            style={{
                background: 'var(--bg-surface)',
                borderRight: '1px solid var(--border)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                boxShadow: 'var(--shadow-card)',
            }}
        >
            {/* ── Logo ── */}
            <div
                className="p-4 flex items-center gap-3 cursor-pointer group"
                style={{ borderBottom: '1px solid var(--border)' }}
                onClick={() => navigate('/welcome')}
                title="Go to Welcome Page"
            >
                {/* Shield logo image — cropped to just the shield center */}
                <div
                    className="w-10 h-10 rounded-xl overflow-hidden shrink-0 transition-transform group-hover:scale-105"
                    style={{
                        boxShadow: '0 0 16px rgba(79,143,255,0.45)',
                        border: '1px solid rgba(79,143,255,0.3)',
                    }}
                >
                    <img
                        src={shieldLogo}
                        alt="IDxVPN Logo"
                        className="w-full h-full object-cover"
                        style={{ objectPosition: '50% 40%', transform: 'scale(1.3)' }}
                    />
                </div>
                <div className="min-w-0">
                    <h1
                        className="text-base font-bold tracking-wide leading-tight transition-colors group-hover:text-[var(--accent-blue)]"
                        style={{ color: 'var(--text-primary)' }}
                    >
                        IDxVPN
                    </h1>
                    <p className="text-[10px] font-medium" style={{ color: 'var(--text-muted)' }}>VPN Detection Platform</p>
                </div>
            </div>

            {/* ── Nav ── */}
            <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
                {navItems.map((item) => {
                    const Icon     = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-200 text-left"
                            style={{
                                background:  isActive ? 'var(--accent-blue-glow)' : 'transparent',
                                color:       isActive ? 'var(--accent-blue)'       : 'var(--text-secondary)',
                                borderLeft:  isActive ? '2px solid var(--accent-blue)' : '2px solid transparent',
                                fontWeight:  isActive ? 600 : 400,
                            }}
                            onMouseEnter={e => {
                                if (!isActive) {
                                    e.currentTarget.style.background = 'var(--bg-surface-hover)';
                                    e.currentTarget.style.color      = 'var(--text-primary)';
                                    e.currentTarget.style.transform  = 'translateX(3px)';
                                }
                            }}
                            onMouseLeave={e => {
                                if (!isActive) {
                                    e.currentTarget.style.background = 'transparent';
                                    e.currentTarget.style.color      = 'var(--text-secondary)';
                                    e.currentTarget.style.transform  = 'translateX(0)';
                                }
                            }}
                        >
                            <Icon size={18} />
                            <span className="text-sm">{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            {/* ── Bottom section ── */}
            <div className="p-4 space-y-3" style={{ borderTop: '1px solid var(--border)' }}>
                {/* User card */}
                {user && (
                    <div
                        className="p-3 rounded-xl flex items-center justify-between gap-3"
                        style={{
                            background: 'var(--bg-surface-hover)',
                            border: '1px solid var(--border)',
                        }}
                    >
                        <div className="flex items-center gap-2.5 min-w-0">
                            <div
                                className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                                style={{ background: 'var(--accent-blue-glow)', border: '1px solid var(--border)' }}
                            >
                                <User size={14} style={{ color: 'var(--accent-blue)' }} />
                            </div>
                            <div className="min-w-0">
                                <div className="text-sm font-semibold capitalize truncate" style={{ color: 'var(--text-primary)' }}>
                                    {user.username}
                                </div>
                                <div className="text-xs capitalize" style={{ color: 'var(--text-muted)' }}>
                                    {user.role}
                                </div>
                            </div>
                        </div>
                        <button
                            onClick={logout}
                            className="p-1.5 rounded-lg transition-colors shrink-0"
                            style={{ color: 'var(--text-muted)' }}
                            title="Logout"
                            onMouseEnter={e => { e.currentTarget.style.color = 'var(--accent-red)'; e.currentTarget.style.background = 'hsla(350,75%,55%,0.10)'; }}
                            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent'; }}
                        >
                            <LogOut size={15} />
                        </button>
                    </div>
                )}

                {/* Theme toggle */}
                <ThemeToggle />

                {/* Status badge */}
                <div
                    className="p-3 rounded-xl flex items-center gap-3"
                    style={{ background: 'var(--bg-surface-hover)', border: '1px solid var(--border)' }}
                >
                    <div
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ background: 'var(--accent-green)', boxShadow: '0 0 8px var(--accent-green)' }}
                    />
                    <div className="min-w-0">
                        <div className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Model Training</div>
                        <div className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>DigitalOcean Node active</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
