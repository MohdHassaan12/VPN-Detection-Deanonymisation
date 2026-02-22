import React from 'react';
import LiveMetricsCards from './LiveMetricsCards';
import LiveInferenceTable from './LiveInferenceTable';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useDashboardData } from '../../hooks/useDashboardData';

const DashboardView = () => {
    const { logs, chartData, metrics } = useDashboardData();

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center bg-[#151923]/80 p-6 rounded-2xl border border-[#ffffff1a] glass-panel">
                <div className="space-y-1">
                    <h2 className="text-2xl font-bold text-white tracking-tight">Real-Time VPN Classification</h2>
                    <p className="text-[#a0aabf]">Monitoring Stage 1 CNN and Stage 2 Random Forest inference limits.</p>
                </div>
                <div className="flex gap-4">
                    <div className="px-4 py-2 rounded-lg bg-[#1bc553]/10 text-[#1bc553] border border-[#1bc553]/20 flex items-center gap-2 font-medium">
                        <span className="w-2 h-2 rounded-full bg-[#1bc553] animate-pulse"></span>
                        Pipeline Active
                    </div>
                </div>
            </div>

            <LiveMetricsCards metrics={metrics} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-[#ffffff1a]">
                    <h3 className="text-[#a0aabf] font-medium tracking-wide mb-6">Live Traffic Volume</h3>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                                <XAxis dataKey="time" stroke="#a0aabf" axisLine={false} tickLine={false} />
                                <YAxis stroke="#a0aabf" axisLine={false} tickLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#151923', borderColor: '#ffffff1a', color: '#fff', borderRadius: '8px' }}
                                    itemStyle={{ color: '#e2e8f0' }}
                                />
                                <Line type="monotone" name="Normal Traffic" dataKey="normal" stroke="#4f8fff" strokeWidth={3} dot={false} activeDot={{ r: 8, fill: '#4f8fff' }} />
                                <Line type="monotone" name="VPN Traffic" dataKey="vpn" stroke="#ff9900" strokeWidth={3} dot={false} activeDot={{ r: 8, fill: '#ff9900' }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="lg:col-span-1 glass-panel p-6 rounded-2xl border border-[#ffffff1a]">
                    <h3 className="text-[#a0aabf] font-medium tracking-wide mb-6">Top Deanonymised Apps</h3>
                    <div className="space-y-6 mt-4">
                        {[
                            { name: 'Video Streaming', value: 45, color: 'bg-[#4f8fff]' },
                            { name: 'VoIP (Teams/Zoom)', value: 25, color: 'bg-[#ff9900]' },
                            { name: 'P2P File Transfer', value: 15, color: 'bg-[#ff5050]' },
                            { name: 'Chat (WhatsApp)', value: 10, color: 'bg-[#1bc553]' },
                            { name: 'Web Browsing', value: 5, color: 'bg-[#a0aabf]' },
                        ].map(app => (
                            <div key={app.name}>
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-white font-medium">{app.name}</span>
                                    <span className="font-mono text-[#a0aabf]">{app.value}%</span>
                                </div>
                                <div className="w-full h-2 bg-[#ffffff1a] rounded-full overflow-hidden">
                                    <div className={`h-full ${app.color} transition-all duration-1000 ease-out`} style={{ width: `${app.value}%` }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <LiveInferenceTable logs={logs} />
        </div>
    );
};

export default DashboardView;
