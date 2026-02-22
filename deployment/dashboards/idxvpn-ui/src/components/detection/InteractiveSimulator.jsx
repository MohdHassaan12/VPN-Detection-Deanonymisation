import React, { useState } from 'react';
import { Activity, ShieldAlert, Cpu, CheckCircle } from 'lucide-react';

const InteractiveSimulator = () => {
    const [loading, setLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0);
    const [result, setResult] = useState(null);
    const [isVpn, setIsVpn] = useState(true);
    const [history, setHistory] = useState([]);

    const handleDetection = (e) => {
        e.preventDefault();
        if (loading) return; // Prevent double clicks

        setLoading(true);
        setLoadingStep(0);
        setResult(null);

        const steps = 5;
        let currentStep = 0;

        const interval = setInterval(() => {
            currentStep++;
            if (currentStep < steps) {
                setLoadingStep(currentStep);
            } else {
                clearInterval(interval);

                // Finalize result
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

                const newResult = {
                    id: Date.now().toString(),
                    time: new Date().toLocaleTimeString('en-US', { hour12: false }),
                    app,
                    conf,
                    action,
                    score,
                    isVpnVal: isVpn
                };

                setResult(newResult);
                setHistory(prev => [newResult, ...prev].slice(0, 5));
                setLoading(false);
            }
        }, 500); // 500ms per step
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
                <h3 className="text-xl font-bold text-default mb-6">Detection Results</h3>

                <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-black/5 dark:bg-white/5 border border-divider p-4 rounded-xl text-center shadow-sm">
                        <div className="text-xs text-muted mb-1 tracking-wider">{result.isVpnVal ? 'DEANONYMISED APP' : 'DETECTED APP'}</div>
                        <div className="text-xl font-bold text-[#4f8fff]">{result.app}</div>
                    </div>
                    <div className="bg-black/5 dark:bg-white/5 border border-divider p-4 rounded-xl text-center shadow-sm">
                        <div className="text-xs text-muted mb-1 tracking-wider">CNN CONFIDENCE</div>
                        <div className="text-xl font-bold text-[#4f8fff]">{result.conf}%</div>
                    </div>
                </div>

                <div className={`p-6 rounded-xl border-l-[4px] border-r border-t border-b flex gap-4 shadow-lg ${bgClass} ${borderClass}`}>
                    <div className={`mt-1 ${textClass}`}><Icon size={24} /></div>
                    <div>
                        <div className={`text-lg font-bold mb-1 ${textClass}`}>{result.action}</div>
                        <div className="text-sm text-default mb-3">{desc}</div>
                        <div className="inline-block px-3 py-1 bg-black/5 dark:bg-black/40 rounded-full border border-divider text-xs font-mono text-default font-medium">
                            Risk Score: {result.score}/100
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-6 animate-fade-in-up">
            <div className="space-y-1 border-b border-divider pb-6 mb-6">
                <h2 className="text-2xl font-bold text-default tracking-tight">Interactive Detection Tool</h2>
                <p className="text-muted">Simulate a packet capture flow and pass it through the active 4-Layer ML Pipeline.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Input Form */}
                <div className="glass-panel p-6 rounded-2xl border border-divider flex flex-col">
                    <h3 className="text-lg font-bold text-default mb-6 border-b border-divider pb-4">Flow Parameters</h3>
                    <form onSubmit={handleDetection} className="space-y-6 flex-1 flex flex-col">
                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-muted">Source IP</label>
                            <input type="text" defaultValue="192.168.1.100" className="bg-panel border border-divider rounded-xl p-3 text-default focus:outline-none focus:border-[#4f8fff] focus:ring-1 focus:ring-[#4f8fff] transition-all" />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-muted">Destination IP</label>
                            <input type="text" defaultValue="8.8.8.8" className="bg-panel border border-divider rounded-xl p-3 text-default focus:outline-none focus:border-[#4f8fff] focus:ring-1 focus:ring-[#4f8fff] transition-all" />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-sm font-medium text-muted">Destination Port</label>
                            <input type="text" defaultValue="443" className="bg-panel border border-divider rounded-xl p-3 text-default focus:outline-none focus:border-[#4f8fff] focus:ring-1 focus:ring-[#4f8fff] transition-all" />
                        </div>

                        <div className="flex items-center justify-between py-4 border-y border-divider my-4">
                            <div>
                                <div className="text-default font-bold">Encrypted Tunnel</div>
                                <div className="text-xs text-muted mt-1">Simulate traffic inside IPSec/OpenVPN.</div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setIsVpn(!isVpn)}
                                className={`w-14 h-7 rounded-full transition-colors relative focus:outline-none ${isVpn ? 'bg-[#4f8fff]' : 'bg-black/10 dark:bg-white/10'}`}
                            >
                                <div className={`w-5 h-5 bg-white rounded-full absolute top-1 transition-transform shadow-md ${isVpn ? 'translate-x-8' : 'translate-x-1'}`}></div>
                            </button>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={`w-full py-4 rounded-xl font-bold transition-all mt-auto relative overflow-hidden ${loading
                                ? 'bg-black/10 dark:bg-white/10 text-muted cursor-not-allowed border border-divider shadow-inner'
                                : 'bg-gradient-to-r from-[#4f8fff] to-[#2555ff] hover:shadow-[0_0_20px_rgba(79,143,255,0.4)] text-default hover:scale-[1.02] active:scale-[0.98]'
                                }`}
                        >
                            {loading ? (
                                <div className="flex items-center justify-center gap-3">
                                    <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                    Processing Flow...
                                </div>
                            ) : 'Run Pipeline Detection'}
                        </button>
                    </form>
                </div>

                {/* Results Panel */}
                <div className="glass-panel p-6 rounded-2xl border border-divider flex items-center justify-center min-h-[400px] relative overflow-hidden">
                    {/* Background glow when loaded */}
                    {result && !loading && (
                        <div className={`absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl -z-10 translate-x-1/2 -translate-y-1/2 opacity-20 ${result.action === 'ALLOW' ? 'bg-[#1bc553]' :
                                result.action === 'CHALLENGE' ? 'bg-[#ff9900]' : 'bg-[#ff5050]'
                            }`}></div>
                    )}

                    {!loading && !result && (
                        <div className="text-center text-muted flex flex-col items-center opacity-60">
                            <Cpu size={48} className="mb-4 text-[#4f8fff]" />
                            <p>Waiting for flow input...</p>
                            <p className="text-sm mt-2">Enter parameters and run detection.</p>
                        </div>
                    )}

                    {loading && (
                        <div className="w-full max-w-sm mx-auto animate-fade-in-up">
                            <div className="text-center text-[#4f8fff] flex flex-col items-center mb-8">
                                <div className="w-16 h-16 border-4 border-[#4f8fff]/20 border-t-[#4f8fff] rounded-full animate-spin mb-4 shadow-[0_0_15px_rgba(79,143,255,0.3)]"></div>
                                <p className="font-bold tracking-widest text-lg mb-2">PIPELINE ACTIVE</p>
                            </div>

                            <div className="space-y-3">
                                {['Packet Capture & Reassembly', 'Temporal Feature Extraction', 'Stage 1: CNN Classification', 'Stage 2: RF Intent Scoring', 'Policy Rule Evaluation'].map((step, idx) => (
                                    <div key={idx} className={`flex items-center gap-4 p-4 rounded-xl border transition-all duration-500 ${loadingStep > idx ? 'bg-[#1bc553]/10 border-[#1bc553]/30 text-[#1bc553]' : loadingStep === idx ? 'bg-[#4f8fff]/10 border-[#4f8fff]/30 text-[#4f8fff] shadow-[0_0_15px_rgba(79,143,255,0.1)]' : 'bg-black/5 dark:bg-white/5 border-divider text-muted opacity-50'}`}>
                                        <div className="shrink-0">
                                            {loadingStep > idx ? <CheckCircle size={20} /> : loadingStep === idx ? <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" /> : <div className="w-5 h-5 rounded-full border-2 border-current opacity-30" />}
                                        </div>
                                        <div className="font-medium text-sm">{step}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {result && !loading && renderResultCard()}
                </div>
            </div>

            {/* Simulation History */}
            {history.length > 0 && (
                <div className="glass-panel p-8 rounded-2xl border border-divider mt-8 animate-fade-in-up">
                    <h3 className="text-xl font-bold text-default mb-6 flex items-center gap-2">
                        <Activity size={24} className="text-[#4f8fff]" />
                        Recent Simulations
                    </h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr className="border-b border-divider">
                                    <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Time</th>
                                    <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Detected App</th>
                                    <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Confidence</th>
                                    <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Risk Score</th>
                                    <th className="py-3 px-4 font-medium text-muted uppercase tracking-wider text-xs">Action Taken</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-divider">
                                {history.map((item) => (
                                    <tr key={item.id} className="hover:bg-black/5 dark:hover:bg-white/5 transition-colors">
                                        <td className="py-4 px-4 font-mono text-muted">{item.time}</td>
                                        <td className="py-4 px-4">
                                            <div className="flex items-center gap-2">
                                                <span className="font-bold text-default">{item.app}</span>
                                                {item.isVpnVal && <span className="bg-[#4f8fff]/10 text-[#4f8fff] text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider border border-[#4f8fff]/20">Tunneled</span>}
                                            </div>
                                        </td>
                                        <td className="py-4 px-4 font-mono text-[#4f8fff] font-bold">{item.conf}%</td>
                                        <td className="py-4 px-4 font-mono">
                                            <div className="flex items-center gap-3">
                                                <div className="w-16 h-2 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden shrink-0">
                                                    <div className={`h-full rounded-full ${item.score < 20 ? 'bg-[#1bc553]' : item.score < 60 ? 'bg-[#ff9900]' : 'bg-[#ff5050]'}`} style={{ width: `${item.score}%` }}></div>
                                                </div>
                                                <span>{item.score}/100</span>
                                            </div>
                                        </td>
                                        <td className="py-4 px-4">
                                            <span className={`px-2 py-1 flex items-center gap-1.5 w-max rounded-md text-xs font-bold border ${item.action === 'ALLOW' ? 'bg-[#1bc553]/10 text-[#1bc553] border-[#1bc553]/20' :
                                                    item.action === 'CHALLENGE' ? 'bg-[#ff9900]/10 text-[#ff9900] border-[#ff9900]/20' :
                                                        'bg-[#ff5050]/10 text-[#ff5050] border-[#ff5050]/20'
                                                }`}>
                                                {item.action === 'ALLOW' && <CheckCircle size={12} />}
                                                {item.action === 'CHALLENGE' && <ShieldAlert size={12} />}
                                                {item.action === 'BLOCK' && <ShieldAlert size={12} />}
                                                {item.action}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default InteractiveSimulator;
