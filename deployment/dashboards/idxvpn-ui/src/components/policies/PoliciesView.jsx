import React, { useState } from 'react';
import { Activity, ShieldAlert, CheckCircle, Shield, Power } from 'lucide-react';

const recentActions = [
    { id: 'ACT-092', time: '10:42:05', ip: '192.168.1.104', app: 'GAMING', action: 'ALLOW', score: 12 },
    { id: 'ACT-091', time: '10:41:22', ip: '10.0.0.52', app: 'CHAT', action: 'CHALLENGE', score: 45 },
    { id: 'ACT-090', time: '10:39:15', ip: '172.16.0.8', app: 'P2P', action: 'BLOCK', score: 88 },
    { id: 'ACT-089', time: '10:35:50', ip: '192.168.1.200', app: 'VIDEO', action: 'ALLOW', score: 5 },
];

const PoliciesView = () => {
    const [autoEnforce, setAutoEnforce] = useState(true);

    return (
        <div className="space-y-8 animate-fade-in-up">
            {/* Header Section */}
            <div className="border-b border-divider pb-6 flex items-start justify-between flex-wrap gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-default tracking-tight flex items-center gap-3">
                        <Shield className="text-[#4f8fff]" size={28} />
                        Policies & Health
                    </h2>
                    <p className="text-muted mt-2">Manage gateway reactions and monitor inference engine health.</p>
                </div>

                <div className="flex items-center gap-4 bg-black/5 dark:bg-white/5 px-5 py-3 rounded-2xl border border-divider shadow-sm">
                    <div className="flex flex-col items-end">
                        <span className="text-sm font-bold text-default">Auto-Enforce</span>
                        <span className="text-xs text-muted">{autoEnforce ? 'Active Mitigation' : 'Observation Mode'}</span>
                    </div>
                    <button
                        onClick={() => setAutoEnforce(!autoEnforce)}
                        className={`relative inline-flex h-8 w-16 items-center rounded-full transition-colors focus:outline-none ${autoEnforce ? 'bg-[#1bc553]' : 'bg-black/20 dark:bg-white/10'}`}
                    >
                        <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform shadow-md ${autoEnforce ? 'translate-x-9' : 'translate-x-1'}`} />
                    </button>
                </div>
            </div>

            {/* Health Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl border border-divider flex items-center justify-between">
                    <div>
                        <div className="text-muted text-sm uppercase tracking-wider mb-1 font-medium">VPN IDX Service</div>
                        <div className="text-2xl font-bold text-default flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-[#1bc553] shadow-[0_0_10px_#1bc553] animate-pulse"></span>
                            Healthy
                        </div>
                    </div>
                    <Activity size={32} className="text-[#1bc553]" />
                </div>

                <div className="glass-panel p-6 rounded-2xl border border-divider flex items-center justify-between">
                    <div>
                        <div className="text-muted text-sm uppercase tracking-wider mb-1 font-medium">Pipeline Latency</div>
                        <div className="text-2xl font-bold text-[#4f8fff] font-mono">~45ms</div>
                    </div>
                    <Activity size={32} className="text-[#4f8fff]" />
                </div>
            </div>

            {/* Risk-Based Policy Rules */}
            <div className="glass-panel p-8 rounded-2xl border border-divider">
                <h3 className="text-xl font-bold text-default mb-2">Risk-Based Policy Rules</h3>
                <p className="text-muted mb-8">Manage how the gateway reacts to the Stage 2 Intent Classifier's inferred risk scores.</p>

                <div className="space-y-6">
                    {/* ALLOW Rule */}
                    <div className="border border-[#1bc553]/20 bg-[#1bc553]/5 rounded-xl p-6 flex items-start gap-4 transition-all hover:bg-[#1bc553]/10">
                        <div className="p-3 bg-[#1bc553]/10 rounded-lg text-[#1bc553]">
                            <CheckCircle size={24} />
                        </div>
                        <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="text-lg font-bold text-[#1bc553]">ALLOW <span className="text-sm font-normal text-muted ml-2">(Low Risk)</span></h4>
                                <div className="px-3 py-1 bg-black/5 dark:bg-black/40 rounded-full text-xs font-mono text-default border border-divider">
                                    Score: 0 - 20
                                </div>
                            </div>
                            <p className="text-default">Legitimate traffic. User browsing normal sites securely.</p>
                        </div>
                    </div>

                    {/* CHALLENGE Rule */}
                    <div className="border border-[#ff9900]/20 bg-[#ff9900]/5 rounded-xl p-6 flex items-start gap-4 transition-all hover:bg-[#ff9900]/10">
                        <div className="p-3 bg-[#ff9900]/10 rounded-lg text-[#ff9900]">
                            <ShieldAlert size={24} />
                        </div>
                        <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="text-lg font-bold text-[#ff9900]">CHALLENGE <span className="text-sm font-normal text-muted ml-2">(Medium Risk)</span></h4>
                                <div className="px-3 py-1 bg-black/5 dark:bg-black/40 rounded-full text-xs font-mono text-default border border-divider">
                                    Score: 21 - 60
                                </div>
                            </div>
                            <p className="text-default">Unusual patterns. Force MFA/CAPTCHA before proceeding.</p>
                        </div>
                    </div>

                    {/* BLOCK Rule */}
                    <div className="border border-[#ff5050]/20 bg-[#ff5050]/5 rounded-xl p-6 flex items-start gap-4 transition-all hover:bg-[#ff5050]/10">
                        <div className="p-3 bg-[#ff5050]/10 rounded-lg text-[#ff5050]">
                            <ShieldAlert size={24} />
                        </div>
                        <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="text-lg font-bold text-[#ff5050]">BLOCK <span className="text-sm font-normal text-muted ml-2">(High Risk)</span></h4>
                                <div className="px-3 py-1 bg-black/5 dark:bg-black/40 rounded-full text-xs font-mono text-default border border-divider">
                                    Score: 61 - 99
                                </div>
                            </div>
                            <p className="text-default">Malicious intent detected. Immediate drop & log.</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Policy Actions */}
            <div className="glass-panel p-8 rounded-2xl border border-divider">
                <h3 className="text-xl font-bold text-default mb-6">Recent Policy Actions</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-sm">
                        <thead>
                            <tr className="border-b border-divider">
                                <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Time</th>
                                <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Source IP</th>
                                <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">App Category</th>
                                <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Risk Score</th>
                                <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Action Taken</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-divider">
                            {recentActions.map((action) => (
                                <tr key={action.id} className="hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                                    <td className="py-4 px-4 font-mono text-muted">{action.time}</td>
                                    <td className="py-4 px-4 font-mono text-default">{action.ip}</td>
                                    <td className="py-4 px-4">
                                        <span className="bg-black/5 dark:bg-white/5 border border-divider px-2 py-1 rounded-md text-xs font-bold text-[#4f8fff]">
                                            {action.app}
                                        </span>
                                    </td>
                                    <td className="py-4 px-4 font-mono">{action.score}/100</td>
                                    <td className="py-4 px-4">
                                        <span className={`px-2 py-1 flex items-center gap-1.5 w-max rounded-md text-xs font-bold border ${action.action === 'ALLOW' ? 'bg-[#1bc553]/10 text-[#1bc553] border-[#1bc553]/20' :
                                                action.action === 'CHALLENGE' ? 'bg-[#ff9900]/10 text-[#ff9900] border-[#ff9900]/20' :
                                                    'bg-[#ff5050]/10 text-[#ff5050] border-[#ff5050]/20'
                                            }`}>
                                            {action.action === 'ALLOW' && <CheckCircle size={12} />}
                                            {action.action === 'CHALLENGE' && <ShieldAlert size={12} />}
                                            {action.action === 'BLOCK' && <ShieldAlert size={12} />}
                                            {action.action}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default PoliciesView;
