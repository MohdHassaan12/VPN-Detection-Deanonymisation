import React, { useState } from 'react';
import { Activity, ShieldAlert, Cpu, CheckCircle } from 'lucide-react';

const InteractiveSimulator = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [isVpn, setIsVpn] = useState(true);

    const handleDetection = (e) => {
        e.preventDefault();
        if (loading) return; // Prevent double clicks

        setLoading(true);
        setResult(null);

        // Simulate pipeline latency (longer for realism)
        setTimeout(() => {
            const apps = ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'GAMING'];
            const app = apps[Math.floor(Math.random() * apps.length)];
            const conf = (Math.random() * 10 + 89).toFixed(1);

            const isMalicious = isVpn && Math.random() > 0.6;
            let score = Math.floor(Math.random() * 20);
            let action = 'ALLOW';

            if (isMalicious) {
                action = 'BLOCK';
                score = Math.floor(Math.random() * 20) + 80;
            } else if (isVpn) {
                action = 'CHALLENGE';
                score = Math.floor(Math.random() * 40) + 30;
            }

            setResult({ app, conf, action, score, isVpnVal: isVpn });
            setLoading(false);
        }, 2000); // 2 second delay for realism
    };

    const renderResultCard = () => {
        if (!result) return null;

        let borderClass = 'border-[#1bc553]/30';
        let bgClass = 'bg-[#1bc553]/10';
        let textClass = 'text-[#1bc553]';
        let desc = 'Flow looks benign. Allowing traffic.';
        let Icon = CheckCircle;

        if (result.action === 'CHALLENGE') {
            borderClass = 'border-[#ff9900]/50';
            bgClass = 'bg-[#ff9900]/10';
            textClass = 'text-[#ff9900]';
            desc = 'Anomalous flow characteristics observed inside tunnel.';
            Icon = ShieldAlert;
        } else if (result.action === 'BLOCK') {
            borderClass = 'border-[#ff5050]/50';
            bgClass = 'bg-[#ff5050]/10';
            textClass = 'text-[#ff5050]';
            desc = 'High confidence malicious behavior / policy violation.';
            Icon = ShieldAlert;
        }

        return (
            <div className="w-full animate-fade-in-up">
                <h3 className="text-xl font-bold text-white mb-6">Detection Results</h3>

                <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-[#ffffff05] border border-[#ffffff0d] p-4 rounded-xl text-center">
                        <div className="text-xs text-[#a0aabf] mb-1 tracking-wider">{result.isVpnVal ? 'DEANONYMISED APP' : 'DETECTED APP'}</div>
                        <div className="text-xl font-bold text-[#4f8fff]">{result.app}</div>
                    </div>
                    <div className="bg-[#ffffff05] border border-[#ffffff0d] p-4 rounded-xl text-center">
                        <div className="text-xs text-[#a0aabf] mb-1 tracking-wider">CNN CONFIDENCE</div>
                        <div className="text-xl font-bold text-[#4f8fff]">{result.conf}%</div>
                    </div>
                </div>

                <div className={`p-6 rounded-xl border-l-[4px] border-r border-t border-b flex gap-4 ${bgClass} ${borderClass}`}>
                    <div className={`mt-1 ${textClass}`}><Icon size={24} /></div>
                    <div>
                        <div className={`text-lg font-bold mb-1 ${textClass}`}>{result.action}</div>
                        <div className="text-sm text-[#a0aabf] mb-3">{desc}</div>
                        <div className="inline-block px-3 py-1 bg-[#00000040] rounded-full border border-[#ffffff0d] text-xs font-mono text-white">
                            Risk Score: {result.score}/100
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-6 animate-fade-in-up">
            <div className="space-y-1 border-b border-[#ffffff1a] pb-6 mb-6">
                <h2 className="text-2xl font-bold text-white tracking-tight">Interactive Detection Tool</h2>
                <p className="text-[#a0aabf]">Simulate a packet capture flow and pass it through the active 4-Layer ML Pipeline.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Input Form */}
                <div className="glass-panel p-6 rounded-2xl border border-[#ffffff1a]">
                    <h3 className="text-lg font-bold text-white mb-6 border-b border-[#ffffff1a] pb-4">Flow Parameters</h3>
                    <form onSubmit={handleDetection} className="space-y-6">
                        <div className="flex flex-col gap-2">
                            <label className="text-sm text-[#a0aabf]">Source IP</label>
                            <input type="text" defaultValue="192.168.1.100" className="bg-[#151923] border border-[#ffffff1a] rounded-lg p-3 text-white focus:outline-none focus:border-[#4f8fff] transition-colors" />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-sm text-[#a0aabf]">Destination IP</label>
                            <input type="text" defaultValue="8.8.8.8" className="bg-[#151923] border border-[#ffffff1a] rounded-lg p-3 text-white focus:outline-none focus:border-[#4f8fff] transition-colors" />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-sm text-[#a0aabf]">Destination Port</label>
                            <input type="text" defaultValue="443" className="bg-[#151923] border border-[#ffffff1a] rounded-lg p-3 text-white focus:outline-none focus:border-[#4f8fff] transition-colors" />
                        </div>

                        <div className="flex items-center justify-between py-2 border-t border-[#ffffff1a] mt-4 pt-4">
                            <div>
                                <div className="text-white font-medium">Is Encrypted / Tunneled?</div>
                                <div className="text-xs text-[#a0aabf]">Simulate traffic inside an IPSec or OpenVPN tunnel.</div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setIsVpn(!isVpn)}
                                className={`w-12 h-6 rounded-full p-1 transition-colors ${isVpn ? 'bg-[#4f8fff]' : 'bg-[#ffffff1a]'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white shadow-md transform transition-transform ${isVpn ? 'translate-x-6' : 'translate-x-0'}`}></div>
                            </button>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={`w-full py-4 rounded-xl font-bold transition-all relative overflow-hidden ${loading
                                    ? 'bg-[#ffffff1a] text-[#a0aabf] cursor-not-allowed'
                                    : 'bg-gradient-to-r from-[#4f8fff] to-[#2555ff] hover:shadow-[0_0_20px_rgba(79,143,255,0.4)] text-white hover:scale-[1.02] active:scale-[0.98]'
                                }`}
                        >
                            {loading ? (
                                <div className="flex items-center justify-center gap-3">
                                    <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                    Analyzing Inference Engine...
                                </div>
                            ) : 'Run Pipeline Detection'}
                        </button>
                    </form>
                </div>

                {/* Results Panel */}
                <div className="glass-panel p-6 rounded-2xl border border-[#ffffff1a] flex items-center justify-center min-h-[400px]">
                    {!loading && !result && (
                        <div className="text-center text-[#a0aabf] flex flex-col items-center opacity-60">
                            <Cpu size={48} className="mb-4 text-[#4f8fff]" />
                            <p>Waiting for flow input...</p>
                            <p className="text-sm mt-2">Enter parameters and run detection.</p>
                        </div>
                    )}

                    {loading && (
                        <div className="text-center text-[#4f8fff] flex flex-col items-center animate-fade-in-up">
                            <div className="w-16 h-16 border-4 border-[#4f8fff]/20 border-t-[#4f8fff] rounded-full animate-spin mb-6"></div>
                            <p className="font-bold tracking-widest text-lg">ANALYZING PACKETS...</p>
                            <p className="text-sm text-[#a0aabf] mt-2 font-mono bg-[#ffffff05] px-4 py-2 rounded-lg border border-[#ffffff0d]">Passing through CNN + RF Layers</p>
                        </div>
                    )}

                    {result && !loading && renderResultCard()}
                </div>
            </div>
        </div>
    );
};

export default InteractiveSimulator;
