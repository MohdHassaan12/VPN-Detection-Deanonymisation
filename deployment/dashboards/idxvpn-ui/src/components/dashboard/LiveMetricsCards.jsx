import React from 'react';
import { Network, Activity, ShieldAlert, Cpu, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const KPICard = ({ title, value, icon: Icon, trend, colorClass }) => (
    <div className="glass-panel p-6 rounded-2xl border border-[#ffffff1a] relative overflow-hidden group hover:bg-[#ffffff05] transition-colors cursor-pointer">
        <div className="flex justify-between items-start mb-4">
            <h3 className="text-[#a0aabf] font-medium tracking-wide">{title}</h3>
            <div className={`p-3 rounded-xl ${colorClass}`}>
                <Icon size={24} />
            </div>
        </div>
        <div className="text-4xl font-bold font-mono tracking-tight text-white mb-2">{value}</div>
        <div className={`text-sm flex items-center gap-1 mt-4 ${trend.positive ? 'text-[#1bc553]' : 'text-[#ff5050]'}`}>
            {trend.positive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
            <span className="font-medium">{trend.text}</span>
        </div>
    </div>
);

const LiveMetricsCards = ({ metrics }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <KPICard
                title="Deanonymised Flows"
                value={metrics?.deanonymisedFlows.toLocaleString() || "0"}
                icon={Network}
                colorClass="bg-[#2555ff]/10 text-[#4f8fff] shadow-[0_0_15px_rgba(79,143,255,0.2)]"
                trend={{ positive: true, text: '92% deanonymisation rate' }}
            />
            <KPICard
                title="Detected VPN Traffic"
                value={metrics?.detectedVpn.toLocaleString() || "0"}
                icon={ShieldAlert}
                colorClass="bg-[#ff9900]/10 text-[#ff9900] shadow-[0_0_15px_rgba(255,153,0,0.2)]"
                trend={{ positive: true, text: '12% increase from yesterday' }}
            />
            <KPICard
                title="Pipeline Latency (p95)"
                value="42ms"
                icon={Activity}
                colorClass="bg-[#ff5050]/10 text-[#ff5050] shadow-[0_0_15px_rgba(255,80,80,0.2)]"
                trend={{ positive: false, text: 'Optimal response time' }}
            />
            <KPICard
                title="Random Forest Accuracy"
                value="98.4%"
                icon={Cpu}
                colorClass="bg-[#1bc553]/10 text-[#1bc553] shadow-[0_0_15px_rgba(27,197,83,0.2)]"
                trend={{ positive: true, text: '0.2% improvement' }}
            />
        </div>
    );
};

export default LiveMetricsCards;
