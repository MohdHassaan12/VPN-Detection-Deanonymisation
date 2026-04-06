import React from 'react';
import { Network, Activity, ShieldAlert, Cpu, ArrowUpRight, ArrowDownRight } from 'lucide-react';

const KPICard = ({ title, value, icon: Icon, trend, colorClass, gradientClass }) => (
        <div className={`glass-panel p-6 rounded-2xl relative overflow-hidden group hover:-translate-y-1 transition-all duration-300 cursor-pointer ${gradientClass}`}
             style={{ border: '1px solid var(--border)' }}
        >
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" style={{ background: 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 100%)' }}></div>
        <div className="flex justify-between items-start mb-4 relative z-10">
            <h3 className="text-muted font-medium tracking-wide font-outfit uppercase text-xs">{title}</h3>
            <div className={`p-3 rounded-xl backdrop-blur-md ${colorClass} group-hover:scale-110 transition-transform duration-300`}>
                <Icon size={22} className="drop-shadow-lg" />
            </div>
        </div>
        <div className="text-4xl font-bold font-mono tracking-tight mb-2 relative z-10" style={{ color: 'var(--text-primary)' }}>{value}</div>
        <div className={`text-sm flex items-center gap-1 mt-4 relative z-10 font-medium ${trend.positive ? 'text-[#1bc553] drop-shadow-[0_0_5px_rgba(27,197,83,0.4)]' : 'text-[#ff5050] drop-shadow-[0_0_5px_rgba(255,80,80,0.4)]'}`}>
            {trend.positive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
            <span>{trend.text}</span>
        </div>
    </div>
);

const LiveMetricsCards = ({ metrics }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <KPICard
                title="Total Scanned"
                value={metrics?.totalScanned.toLocaleString() || "0"}
                icon={Activity}
                colorClass="bg-gradient-to-br from-[#2555ff]/20 to-[#4f8fff]/5 text-[#639cff] shadow-[0_0_20px_rgba(79,143,255,0.15)] border-[#2555ff]/20"
                gradientClass="hover:border-[#2555ff]/40"
                trend={{ positive: true, text: '+14.5% from last hour' }}
            />
            <KPICard
                title="VPN Detected"
                value={metrics?.detectedVpn.toLocaleString() || "0"}
                icon={ShieldAlert}
                colorClass="bg-gradient-to-br from-[#ff9900]/20 to-[#ffb84d]/5 text-[#ffb84d] shadow-[0_0_20px_rgba(255,153,0,0.15)] border-[#ff9900]/20"
                gradientClass="hover:border-[#ff9900]/40"
                trend={{ positive: true, text: '25% of total traffic' }}
            />
            <KPICard
                title="Deanonymised Flows"
                value={metrics?.deanonymisedFlows.toLocaleString() || "0"}
                icon={Network}
                colorClass="bg-gradient-to-br from-[#1bc553]/20 to-[#35e871]/5 text-[#35e871] shadow-[0_0_20px_rgba(27,197,83,0.15)] border-[#1bc553]/20"
                gradientClass="hover:border-[#1bc553]/40"
                trend={{ positive: true, text: '92% deanonymisation rate' }}
            />
            <KPICard
                title="High-Risk Blocks"
                value={metrics?.highRiskBlocks.toLocaleString() || "0"}
                icon={Cpu}
                colorClass="bg-gradient-to-br from-[#ff5050]/20 to-[#ff7a7a]/5 text-[#ff7a7a] shadow-[0_0_20px_rgba(255,80,80,0.15)] border-[#ff5050]/20"
                gradientClass="hover:border-[#ff5050]/40"
                trend={{ positive: false, text: '+2.3% suspicious intent' }}
            />
        </div>
    );
};

export default LiveMetricsCards;
