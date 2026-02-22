import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import AppConfusionMatrix from './AppConfusionMatrix';

const accuracyData = [
    { name: 'BROWSING', precision: 96 },
    { name: 'VIDEO', precision: 94 },
    { name: 'CHAT', precision: 92 },
    { name: 'P2P', precision: 88 },
    { name: 'VOIP', precision: 89 },
    { name: 'GAMING', precision: 97 },
];

const AnalyticsView = () => {
    return (
        <div className="space-y-6 animate-fade-in-up">
            <div className="space-y-1 border-b border-[#ffffff1a] pb-6 mb-6">
                <h2 className="text-2xl font-bold text-white tracking-tight">Live Analytics Center</h2>
                <p className="text-[#a0aabf]">Monitoring global VPN traffic and real-time model inferences.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl border border-[#ffffff1a] flex flex-col">
                    <h3 className="text-xl font-bold text-white tracking-tight mb-6">Stage 1 Pipeline: CNN Accuracy</h3>

                    <div className="grid grid-cols-3 gap-4 mb-8">
                        <div className="p-4 rounded-xl bg-[#ffffff05] border border-[#ffffff0d] text-center">
                            <div className="text-xs text-[#a0aabf] uppercase tracking-wider mb-1">Precision</div>
                            <div className="text-2xl font-bold text-[#4f8fff]">94.2%</div>
                        </div>
                        <div className="p-4 rounded-xl bg-[#ffffff05] border border-[#ffffff0d] text-center">
                            <div className="text-xs text-[#a0aabf] uppercase tracking-wider mb-1">Recall</div>
                            <div className="text-2xl font-bold text-[#4f8fff]">93.8%</div>
                        </div>
                        <div className="p-4 rounded-xl bg-[#ffffff05] border border-[#ffffff0d] text-center">
                            <div className="text-xs text-[#a0aabf] uppercase tracking-wider mb-1">F1-Score</div>
                            <div className="text-2xl font-bold text-[#4f8fff]">94.0%</div>
                        </div>
                    </div>

                    <div className="flex-1 min-h-[300px] w-full mt-auto">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={accuracyData} margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                                <XAxis dataKey="name" stroke="#a0aabf" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#a0aabf' }} dy={10} />
                                <YAxis stroke="#a0aabf" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} domain={[0, 100]} />
                                <Tooltip
                                    cursor={{ fill: '#ffffff0a' }}
                                    contentStyle={{ backgroundColor: '#151923', borderColor: '#ffffff1a', color: '#fff', borderRadius: '8px' }}
                                />
                                <Bar dataKey="precision" name="Precision %" radius={[4, 4, 0, 0]}>
                                    {accuracyData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill="#1bc553" fillOpacity={0.85} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <AppConfusionMatrix />
            </div>
        </div>
    );
};

export default AnalyticsView;
