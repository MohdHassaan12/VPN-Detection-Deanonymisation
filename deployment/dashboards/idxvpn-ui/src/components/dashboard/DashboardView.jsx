import React from 'react';
import LiveMetricsCards from './LiveMetricsCards';
import LiveInferenceTable from './LiveInferenceTable';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import ReactECharts from 'echarts-for-react';
import { useDashboardData } from '../../context/DashboardDataContext';

const DashboardView = () => {
    const { logs, chartData, metrics } = useDashboardData();

    const nightingaleOption = {
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c}%',
            backgroundColor: 'rgba(21, 25, 35, 0.95)',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            textStyle: { color: '#e2e8f0', fontSize: 13, fontWeight: 500 },
            padding: 12,
            extraCssText: 'border-radius: 12px; backdrop-filter: blur(10px); box-shadow: 0 8px 32px rgba(0,0,0,0.5);'
        },
        legend: {
            bottom: '0%',
            left: 'center',
            itemWidth: 10,
            itemHeight: 10,
            textStyle: { color: '#a0aabf', fontSize: 11 },
            icon: 'circle'
        },
        series: [
            {
                name: 'Top Deanonymised Apps',
                type: 'pie',
                radius: ['20%', '80%'],
                center: ['50%', '45%'],
                roseType: 'area', // Nightingale Rose mode
                itemStyle: {
                    borderRadius: 6,
                    borderColor: '#151923',
                    borderWidth: 2
                },
                label: {
                    show: false
                },
                data: [
                    { value: 45, name: 'Streaming', itemStyle: { color: '#4f8fff' } },
                    { value: 25, name: 'VoIP (Teams)', itemStyle: { color: '#ff9900' } },
                    { value: 15, name: 'P2P Files', itemStyle: { color: '#ff5050' } },
                    { value: 10, name: 'WhatsApp', itemStyle: { color: '#1bc553' } },
                    { value: 5, name: 'Web Browsing', itemStyle: { color: '#a0aabf' } }
                ]
            }
        ]
    };

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
                <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-[#ffffff1a] relative overflow-hidden group">
                    {/* Decorative glow */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-[#4f8fff] opacity-5 rounded-full blur-3xl -z-10 group-hover:opacity-10 transition-opacity duration-700"></div>
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-[#ff9900] opacity-5 rounded-full blur-3xl -z-10 group-hover:opacity-10 transition-opacity duration-700"></div>

                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-[#a0aabf] font-medium tracking-wide">Live Traffic Volume</h3>
                        <div className="flex items-center gap-4 text-xs font-medium">
                            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#4f8fff] shadow-[0_0_8px_#4f8fff]"></div> Normal</span>
                            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-[#ff9900] shadow-[0_0_8px_#ff9900]"></div> VPN</span>
                        </div>
                    </div>

                    <div className="h-[300px] w-full mt-2">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 5, left: -20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
                                <XAxis
                                    dataKey="time"
                                    stroke="#5a6a85"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#5a6a85', fontSize: 11, fontWeight: 500 }}
                                    minTickGap={30}
                                    dy={10}
                                />
                                <YAxis
                                    stroke="#5a6a85"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#5a6a85', fontSize: 11, fontWeight: 500 }}
                                    domain={[0, 100]}
                                    ticks={[0, 25, 50, 75, 100]}
                                    dx={-10}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(21, 25, 35, 0.95)',
                                        backdropFilter: 'blur(10px)',
                                        borderColor: 'rgba(255, 255, 255, 0.1)',
                                        borderRadius: '12px',
                                        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                                        padding: '12px'
                                    }}
                                    itemStyle={{ color: '#e2e8f0', fontWeight: 500, fontSize: '13px' }}
                                    labelStyle={{ color: '#a0aabf', fontSize: '12px', marginBottom: '8px' }}
                                    cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, strokeDasharray: '4 4' }}
                                />
                                <Line
                                    type="monotone"
                                    name="Normal Traffic"
                                    dataKey="normal"
                                    stroke="#4f8fff"
                                    strokeWidth={3}
                                    dot={false}
                                    activeDot={{ r: 6, fill: '#4f8fff', stroke: '#151923', strokeWidth: 2 }}
                                    animationDuration={300}
                                />
                                <Line
                                    type="monotone"
                                    name="VPN Traffic"
                                    dataKey="vpn"
                                    stroke="#ff9900"
                                    strokeWidth={3}
                                    dot={false}
                                    activeDot={{ r: 6, fill: '#ff9900', stroke: '#151923', strokeWidth: 2 }}
                                    animationDuration={300}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="lg:col-span-1 glass-panel p-6 rounded-2xl border border-[#ffffff1a] flex flex-col relative overflow-hidden group">
                    {/* Decorative glow */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-[#4f8fff] opacity-5 rounded-full blur-3xl -z-10 group-hover:opacity-10 transition-opacity duration-700"></div>

                    <h3 className="text-[#a0aabf] font-medium tracking-wide mb-2">Top Deanonymised Apps</h3>
                    <div className="flex-grow w-full h-[300px] mt-2 flex items-center justify-center">
                        <ReactECharts option={nightingaleOption} style={{ height: '100%', width: '100%' }} />
                    </div>
                </div>
            </div>

            <LiveInferenceTable logs={logs} />
        </div>
    );
};

export default DashboardView;
