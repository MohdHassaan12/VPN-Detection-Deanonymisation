import React from 'react';
import { Activity, ShieldAlert, CheckCircle, Shield } from 'lucide-react';

const PoliciesView = () => {
    return (
        <div className="space-y-8 animate-fade-in-up">
            {/* Header Section */}
            <div className="border-b border-[#ffffff1a] pb-6">
                <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                    <Shield className="text-[#4f8fff]" size={28} />
                    Policies & Health
                </h2>
                <p className="text-[#a0aabf] mt-2">Manage gateway reactions and monitor inference engine health.</p>
            </div>

            {/* Health Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl border border-[#ffffff1a] flex items-center justify-between">
                    <div>
                        <div className="text-[#a0aabf] text-sm uppercase tracking-wider mb-1 font-medium">VPN IDX Service</div>
                        <div className="text-2xl font-bold text-white flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-[#1bc553] shadow-[0_0_10px_#1bc553] animate-pulse"></span>
                            Healthy
                        </div>
                    </div>
                    <Activity size={32} className="text-[#1bc553]" />
                </div>

                <div className="glass-panel p-6 rounded-2xl border border-[#ffffff1a] flex items-center justify-between">
                    <div>
                        <div className="text-[#a0aabf] text-sm uppercase tracking-wider mb-1 font-medium">Pipeline Latency</div>
                        <div className="text-2xl font-bold text-[#4f8fff] font-mono">~45ms</div>
                    </div>
                    <Activity size={32} className="text-[#4f8fff]" />
                </div>
            </div>

            {/* Risk-Based Policy Rules */}
            <div className="glass-panel p-8 rounded-2xl border border-[#ffffff1a]">
                <h3 className="text-xl font-bold text-white mb-2">Risk-Based Policy Rules</h3>
                <p className="text-[#a0aabf] mb-8">Manage how the gateway reacts to the Stage 2 Intent Classifier's inferred risk scores.</p>

                <div className="space-y-6">
                    {/* ALLOW Rule */}
                    <div className="border border-[#1bc553]/20 bg-[#1bc553]/5 rounded-xl p-6 flex items-start gap-4 transition-all hover:bg-[#1bc553]/10">
                        <div className="p-3 bg-[#1bc553]/10 rounded-lg text-[#1bc553]">
                            <CheckCircle size={24} />
                        </div>
                        <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="text-lg font-bold text-[#1bc553]">ALLOW <span className="text-sm font-normal text-[#a0aabf] ml-2">(Low Risk)</span></h4>
                                <div className="px-3 py-1 bg-[#00000040] rounded-full text-xs font-mono text-white border border-[#ffffff0d]">
                                    Score: 0 - 20
                                </div>
                            </div>
                            <p className="text-[#e2e8f0]">Legitimate traffic. User browsing normal sites securely.</p>
                        </div>
                    </div>

                    {/* CHALLENGE Rule */}
                    <div className="border border-[#ff9900]/20 bg-[#ff9900]/5 rounded-xl p-6 flex items-start gap-4 transition-all hover:bg-[#ff9900]/10">
                        <div className="p-3 bg-[#ff9900]/10 rounded-lg text-[#ff9900]">
                            <ShieldAlert size={24} />
                        </div>
                        <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="text-lg font-bold text-[#ff9900]">CHALLENGE <span className="text-sm font-normal text-[#a0aabf] ml-2">(Medium Risk)</span></h4>
                                <div className="px-3 py-1 bg-[#00000040] rounded-full text-xs font-mono text-white border border-[#ffffff0d]">
                                    Score: 21 - 60
                                </div>
                            </div>
                            <p className="text-[#e2e8f0]">Unusual patterns. Force MFA/CAPTCHA before proceeding.</p>
                        </div>
                    </div>

                    {/* BLOCK Rule */}
                    <div className="border border-[#ff5050]/20 bg-[#ff5050]/5 rounded-xl p-6 flex items-start gap-4 transition-all hover:bg-[#ff5050]/10">
                        <div className="p-3 bg-[#ff5050]/10 rounded-lg text-[#ff5050]">
                            <ShieldAlert size={24} />
                        </div>
                        <div className="flex-1">
                            <div className="flex justify-between items-start mb-2">
                                <h4 className="text-lg font-bold text-[#ff5050]">BLOCK <span className="text-sm font-normal text-[#a0aabf] ml-2">(High Risk)</span></h4>
                                <div className="px-3 py-1 bg-[#00000040] rounded-full text-xs font-mono text-white border border-[#ffffff0d]">
                                    Score: 61 - 99
                                </div>
                            </div>
                            <p className="text-[#e2e8f0]">Malicious intent detected. Immediate drop & log.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PoliciesView;
