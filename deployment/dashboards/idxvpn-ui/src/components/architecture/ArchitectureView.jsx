import React from 'react';
import { Shield, LockOpen, Cpu, CheckCircle, Navigation, ArrowRight, Layers } from 'lucide-react';

const ArchitectureView = () => {
    return (
        <div className="space-y-6 animate-fade-in-up">
            <div
                className="p-6 rounded-2xl glass-panel relative overflow-hidden"
                style={{ border: '1px solid var(--border)' }}
            >
                <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent-blue)] opacity-5 rounded-full blur-3xl -z-10" />
                <h2 className="text-3xl font-bold tracking-tight pb-1 flex items-center gap-3" style={{ color: 'var(--text-primary)' }}>
                    <Layers className="text-[var(--accent-blue)]" size={32} />
                    Multi-Layer VPN Detection & Deanonymisation Architecture
                </h2>
                <p style={{ color: 'var(--text-secondary)' }} className="font-medium mt-2">
                    A comprehensive breakdown of the real-time AI classification pipeline.
                </p>
            </div>

            {/* Horizontal Flow Diagram */}
            <div className="flex flex-col md:flex-row items-center justify-between p-6 rounded-2xl glass-panel gap-4" style={{ border: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
                {['Edge Firewall', 'TLS Termination', 'ML Engine', 'Policy Engine'].map((step, i, arr) => (
                    <React.Fragment key={step}>
                        <div className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm shadow-sm" style={{ background: 'var(--bg-input)', color: 'var(--text-primary)', border: '1px solid var(--border)' }}>
                            {step}
                        </div>
                        {i < arr.length - 1 && <ArrowRight style={{ color: 'var(--text-muted)' }} />}
                    </React.Fragment>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                
                {/* Layer 1: Edge Firewall */}
                <div className="p-6 rounded-2xl glass-panel relative group" style={{ border: '1px solid var(--border)' }}>
                    <div className="absolute top-4 right-4 p-2 rounded-lg bg-[hsla(210,100%,60%,0.1)] text-[var(--accent-blue)]">
                        <Shield size={24} />
                    </div>
                    <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Layer 1 — Edge Firewall</h3>
                    <ul className="space-y-3">
                        {['IP Intelligence (IPQualityScore/IPinfo API)', 'MTU/MSS Fingerprinting (passive TCP analysis)', 'Fast filtering before ML pipeline', 'Latency: <10ms'].map((item, i) => (
                            <li key={i} className="flex items-start gap-3 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                                <div className="mt-1 w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] shadow-[0_0_8px_var(--accent-blue)]" />
                                {item}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Layer 2: TLS Termination */}
                <div className="p-6 rounded-2xl glass-panel relative group" style={{ border: '1px solid var(--border)' }}>
                    <div className="absolute top-4 right-4 p-2 rounded-lg bg-[hsla(280,100%,60%,0.1)] text-[var(--accent-purple)]">
                        <LockOpen size={24} />
                    </div>
                    <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Layer 2 — TLS Termination</h3>
                    <ul className="space-y-3">
                        {['Decrypt traffic at gateway', 'Extract headers + TLS fingerprints', 'Enables deep inspection of encrypted flows', 'Defeats ECH / TLS 1.3 obfuscation'].map((item, i) => (
                            <li key={i} className="flex items-start gap-3 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                                <div className="mt-1 w-1.5 h-1.5 rounded-full bg-[var(--accent-purple)] shadow-[0_0_8px_var(--accent-purple)]" />
                                {item}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Layer 3: ML Risk Scoring Engine */}
                <div className="lg:col-span-2 p-6 rounded-2xl glass-panel relative" style={{ border: '1px solid var(--border)' }}>
                    <div className="absolute top-4 right-4 p-2 rounded-lg bg-[hsla(152,70%,45%,0.1)] text-[var(--accent-green)]">
                        <Cpu size={24} />
                    </div>
                    <h3 className="text-xl font-bold mb-6" style={{ color: 'var(--text-primary)' }}>Layer 3 — ML Risk Scoring Engine</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-5 rounded-xl border" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
                            <h4 className="font-bold flex items-center gap-2 mb-3" style={{ color: 'var(--text-primary)' }}>
                                <Navigation size={16} className="text-[var(--accent-blue)]" />
                                Stage-1: CNN Application Classifier
                            </h4>
                            <div className="space-y-2 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Input:</span> 64×64×3 packet-block images</div>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Output:</span> 8 application classes</div>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Purpose:</span> classify traffic behavior</div>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Latency:</span> ~50ms</div>
                            </div>
                        </div>

                        <div className="p-5 rounded-xl border" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
                            <h4 className="font-bold flex items-center gap-2 mb-3" style={{ color: 'var(--text-primary)' }}>
                                <CheckCircle size={16} className="text-[var(--accent-green)]" />
                                Stage-2: XGBoost Intent Classifier
                            </h4>
                            <div className="space-y-2 text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Input:</span> 25-feature vector</div>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Output:</span> Risk score 0-99</div>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Purpose:</span> determine malicious intent</div>
                                <div className="flex justify-between"><span style={{ color: 'var(--text-muted)' }}>Latency:</span> ~50ms</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Layer 4: Policy Engine */}
                <div className="lg:col-span-2 p-6 rounded-2xl glass-panel relative" style={{ border: '1px solid var(--border)' }}>
                    <h3 className="text-xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>Layer 4 — Policy Engine</h3>
                    <div className="overflow-x-auto rounded-xl border" style={{ borderColor: 'var(--border)' }}>
                        <table className="w-full text-left text-sm whitespace-nowrap">
                            <thead style={{ background: 'var(--bg-surface-hover)', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                                <tr>
                                    <th className="p-4 font-semibold uppercase tracking-wider">Risk Score</th>
                                    <th className="p-4 font-semibold uppercase tracking-wider">Action</th>
                                    <th className="p-4 font-semibold uppercase tracking-wider">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                    <td className="p-4 font-mono font-bold" style={{ color: 'var(--text-primary)' }}>0-20</td>
                                    <td className="p-4">
                                        <span className="px-2 py-1 rounded text-xs font-bold" style={{ background: 'hsla(152,70%,45%,0.1)', color: 'var(--accent-green)', border: '1px solid hsla(152,70%,45%,0.3)' }}>ALLOW</span>
                                    </td>
                                    <td className="p-4 font-medium" style={{ color: 'var(--text-secondary)' }}>Low risk, legitimate traffic</td>
                                </tr>
                                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                                    <td className="p-4 font-mono font-bold" style={{ color: 'var(--text-primary)' }}>21-60</td>
                                    <td className="p-4">
                                        <span className="px-2 py-1 rounded text-xs font-bold" style={{ background: 'hsla(35,95%,58%,0.1)', color: 'var(--accent-orange)', border: '1px solid hsla(35,95%,58%,0.3)' }}>CHALLENGE</span>
                                    </td>
                                    <td className="p-4 font-medium" style={{ color: 'var(--text-secondary)' }}>MFA / CAPTCHA required</td>
                                </tr>
                                <tr>
                                    <td className="p-4 font-mono font-bold" style={{ color: 'var(--text-primary)' }}>61-99</td>
                                    <td className="p-4">
                                        <span className="px-2 py-1 rounded text-xs font-bold" style={{ background: 'hsla(350,75%,55%,0.1)', color: 'var(--accent-red)', border: '1px solid hsla(350,75%,55%,0.3)' }}>BLOCK</span>
                                    </td>
                                    <td className="p-4 font-medium" style={{ color: 'var(--text-secondary)' }}>High risk, suspicious activity</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default ArchitectureView;
