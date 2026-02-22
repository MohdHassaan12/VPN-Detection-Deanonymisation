import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import AppConfusionMatrix from './AppConfusionMatrix';

const accuracyData = [
    { name: 'BROWSING', precision: 96 },
    { name: 'VIDEO', precision: 94 },
    { name: 'CHAT', precision: 92 },
    { name: 'P2P', precision: 88 },
    { name: 'VOIP', precision: 89 },
    { name: 'GAMING', precision: 97 },
];

const distributionData = [
    { name: 'BROWSING', value: 45 },
    { name: 'VIDEO', value: 25 },
    { name: 'CHAT', value: 15 },
    { name: 'P2P', value: 10 },
    { name: 'GAMING', value: 5 },
];

const COLORS = ['#4f8fff', '#1bc553', '#ff9900', '#ff5050', '#a0aabf'];

const AnimatedCounter = ({ value, suffix = "%" }) => {
    const [count, setCount] = useState(0);

    useEffect(() => {
        let start = 0;
        const duration = 1500;
        const increment = value / (duration / 16); // 60fps

        const timer = setInterval(() => {
            start += increment;
            if (start >= value) {
                setCount(value);
                clearInterval(timer);
            } else {
                setCount(start);
            }
        }, 16);

        return () => clearInterval(timer);
    }, [value]);

    return <span>{count.toFixed(1)}{suffix}</span>;
};

const AnalyticsView = () => {
    return (
        <div className="space-y-6 animate-fade-in-up">
            <div className="space-y-1 border-b border-divider pb-6 mb-6">
                <h2 className="text-2xl font-bold text-default tracking-tight">Live Analytics Center</h2>
                <p className="text-muted">Monitoring global VPN traffic and real-time model inferences.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl border border-divider flex flex-col relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-[#4f8fff]/5 rounded-full blur-3xl -z-10 translate-x-1/2 -translate-y-1/2"></div>
                    <h3 className="text-xl font-bold text-default tracking-tight mb-6">Stage 1 Pipeline: CNN Accuracy</h3>

                    <div className="grid grid-cols-3 gap-4 mb-8">
                        <div className="p-4 rounded-xl bg-black/5 dark:bg-white/5 border border-divider/50 backdrop-blur-md text-center shadow-[0_4px_20px_rgba(0,0,0,0.05)] transition-transform hover:-translate-y-1">
                            <div className="text-xs text-muted uppercase tracking-wider mb-1">Precision</div>
                            <div className="text-2xl font-bold text-[#4f8fff] drop-shadow-[0_0_10px_rgba(79,143,255,0.3)]">
                                <AnimatedCounter value={94.2} />
                            </div>
                        </div>
                        <div className="p-4 rounded-xl bg-black/5 dark:bg-white/5 border border-divider/50 backdrop-blur-md text-center shadow-[0_4px_20px_rgba(0,0,0,0.05)] transition-transform hover:-translate-y-1">
                            <div className="text-xs text-muted uppercase tracking-wider mb-1">Recall</div>
                            <div className="text-2xl font-bold text-[#4f8fff] drop-shadow-[0_0_10px_rgba(79,143,255,0.3)]">
                                <AnimatedCounter value={93.8} />
                            </div>
                        </div>
                        <div className="p-4 rounded-xl bg-black/5 dark:bg-white/5 border border-divider/50 backdrop-blur-md text-center shadow-[0_4px_20px_rgba(0,0,0,0.05)] transition-transform hover:-translate-y-1">
                            <div className="text-xs text-muted uppercase tracking-wider mb-1">F1-Score</div>
                            <div className="text-2xl font-bold text-[#4f8fff] drop-shadow-[0_0_10px_rgba(79,143,255,0.3)]">
                                <AnimatedCounter value={94.0} />
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 min-h-[300px] w-full mt-auto">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={accuracyData} margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                                <XAxis dataKey="name" stroke="#a0aabf" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} dy={10} />
                                <YAxis stroke="#a0aabf" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} domain={[0, 100]} />
                                <Tooltip
                                    cursor={{ fill: '#ffffff0a' }}
                                    contentStyle={{ backgroundColor: 'var(--color-panel-bg)', backdropFilter: 'blur(10px)', borderColor: 'var(--color-border)', color: 'var(--color-text)', borderRadius: '8px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}
                                />
                                <Bar dataKey="precision" name="Precision %" radius={[4, 4, 0, 0]}>
                                    {accuracyData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill="#1bc553" fillOpacity={0.85} className="transition-opacity hover:opacity-100" />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <AppConfusionMatrix />
            </div>

            {/* Top Apps Distribution Section */}
            <div className="glass-panel p-6 rounded-2xl border border-divider relative overflow-hidden">
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#1bc553]/5 rounded-full blur-3xl -z-10 -translate-x-1/2 translate-y-1/2"></div>
                <h3 className="text-xl font-bold text-default tracking-tight mb-6">Global App Distribution</h3>
                <div className="flex flex-col md:flex-row items-center gap-8">
                    <div className="h-[300px] w-full md:w-1/2">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={distributionData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={70}
                                    outerRadius={110}
                                    paddingAngle={5}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {distributionData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} className="drop-shadow-lg transition-transform hover:scale-105 origin-center" />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'var(--color-panel-bg)', backdropFilter: 'blur(10px)', borderColor: 'var(--color-border)', color: 'var(--color-text)', borderRadius: '8px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}
                                    itemStyle={{ color: 'var(--color-text)', fontWeight: 'bold' }}
                                    formatter={(value) => [`${value}%`, 'Volume']}
                                />
                                <Legend
                                    verticalAlign="bottom"
                                    height={36}
                                    iconType="circle"
                                    wrapperStyle={{ fontSize: '12px', color: 'var(--color-text-muted)' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="w-full md:w-1/2 space-y-4">
                        <p className="text-muted leading-relaxed">
                            This chart visualizes the real-time distribution of application traffic currently being routed through the gateway.
                            The CNN automatically categorizes packets into these top-level classes based on feature extraction.
                        </p>

                        <div className="space-y-3 mt-6">
                            {distributionData.map((item, i) => (
                                <div key={item.name} className="flex items-center justify-between p-3 rounded-lg bg-black/5 dark:bg-white/5 border border-divider">
                                    <div className="flex items-center gap-3">
                                        <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: COLORS[i] }}></div>
                                        <span className="font-medium text-default">{item.name}</span>
                                    </div>
                                    <span className="font-mono font-bold text-default">{item.value}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsView;
