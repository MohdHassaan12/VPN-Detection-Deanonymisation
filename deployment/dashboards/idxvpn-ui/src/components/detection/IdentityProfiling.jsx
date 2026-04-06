import React, { useState } from 'react';
import { Fingerprint, UserCheck, ShieldAlert, Cpu, Globe2, Activity, Download, Ban } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

const mockSuspects = [
    {
        id: '1',
        ip: '185.107.80.3',
        status: 'High Risk',
        score: 94,
        os: 'Windows 10',
        browser: 'Chrome 120.0 (Custom Fingerprint)',
        device: 'Desktop Workstation',
        app: 'BitTorrent (over WireGuard)',
        location: 'Routing through Romania (Mullvad)',
        time: 'Active for 4h 12m',
        radarFields: [
            { subject: 'TTL Anomalies', A: 120, fullMark: 150 },
            { subject: 'Byte Entropy', A: 98, fullMark: 150 },
            { subject: 'Flow Timing', A: 86, fullMark: 150 },
            { subject: 'TLS Handshake', A: 99, fullMark: 150 },
            { subject: 'Port Patterns', A: 85, fullMark: 150 },
            { subject: 'Cert Matching', A: 65, fullMark: 150 },
        ],
        traffic: [
            { time: '10:00', load: 400 },
            { time: '10:10', load: 300 },
            { time: '10:20', load: 800 },
            { time: '10:30', load: 200 },
            { time: '10:40', load: 600 },
        ]
    },
    {
        id: '2',
        ip: '45.133.1.25',
        status: 'Medium Risk',
        score: 72,
        os: 'macOS 14.2',
        browser: 'Safari (WebKit)',
        device: 'MacBook Pro',
        app: 'Netflix Video Stream (over OpenVPN)',
        location: 'Routing through UK (NordVPN)',
        time: 'Active for 1h 4m',
        radarFields: [
            { subject: 'TTL Anomalies', A: 60, fullMark: 150 },
            { subject: 'Byte Entropy', A: 80, fullMark: 150 },
            { subject: 'Flow Timing', A: 130, fullMark: 150 },
            { subject: 'TLS Handshake', A: 40, fullMark: 150 },
            { subject: 'Port Patterns', A: 50, fullMark: 150 },
            { subject: 'Cert Matching', A: 30, fullMark: 150 },
        ],
        traffic: [
            { time: '10:00', load: 1200 },
            { time: '10:10', load: 1100 },
            { time: '10:20', load: 1150 },
            { time: '10:30', load: 1300 },
            { time: '10:40', load: 1250 },
        ]
    }
];

const IdentityProfiling = () => {
    const [selected, setSelected] = useState(mockSuspects[0]);

    return (
        <div className="flex h-full gap-6">
            {/* Left Sidebar: Suspect List */}
            <div className="w-80 flex flex-col gap-4">
                <div className="flex items-center gap-2 mb-2">
                    <Fingerprint className="text-[var(--accent-blue)]" />
                    <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Suspect Catalog</h2>
                </div>
                
                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                    {mockSuspects.map(s => (
                        <div 
                            key={s.id}
                            onClick={() => setSelected(s)}
                            className="p-4 rounded-xl cursor-pointer transition-all border"
                            style={{ 
                                background: selected.id === s.id ? 'var(--bg-surface-hover)' : 'var(--bg-surface)',
                                borderColor: selected.id === s.id ? 'var(--accent-blue)' : 'var(--border)',
                                transform: selected.id === s.id ? 'translateX(4px)' : 'none'
                            }}
                        >
                            <div className="flex justify-between items-center mb-2">
                                <span className="font-mono text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{s.ip}</span>
                                <span className={`text-xs px-2 py-0.5 rounded-full ${s.score > 85 ? 'bg-red-500/10 text-red-500' : 'bg-orange-500/10 text-orange-500'}`}>
                                    {s.status}
                                </span>
                            </div>
                            <div className="text-xs space-y-1" style={{ color: 'var(--text-secondary)' }}>
                                <div className="flex justify-between"><span>Deanonymisation:</span> <span style={{ color: 'var(--text-primary)' }}>{s.score}% Match</span></div>
                                <div className="flex justify-between"><span>App:</span> <span className="truncate w-32 text-right" style={{ color: 'var(--text-primary)' }}>{s.app.split(' ')[0]}</span></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Content: Dossier */}
            <div className="flex-1 flex flex-col gap-6">
                {/* Dossier Header */}
                <div className="p-6 rounded-xl border flex justify-between items-center" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)', boxShadow: 'var(--shadow-card)' }}>
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h3 className="text-2xl font-bold font-mono" style={{ color: 'var(--text-primary)' }}>{selected.ip}</h3>
                            <span className="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider" style={{ background: 'var(--accent-blue-glow)', color: 'var(--accent-blue)' }}>
                                Identity Locked
                            </span>
                        </div>
                        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Automated ML Dossier generated at {new Date().toLocaleTimeString()}</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all" style={{ background: 'var(--bg-base)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
                            <Download size={16} /> Export Profile
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all text-white bg-red-600 hover:bg-red-700">
                            <Ban size={16} /> Quarantine IP
                        </button>
                    </div>
                </div>

                {/* Profile Data Grid */}
                <div className="grid grid-cols-3 gap-6">
                    {/* Basic Inferences */}
                    <div className="col-span-1 space-y-4">
                        <div className="rounded-xl border p-5" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
                            <h4 className="text-sm font-semibold mb-4 uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Inferred Footprint</h4>
                            
                            <div className="space-y-4">
                                <div className="flex items-start gap-3">
                                    <Cpu size={18} className="mt-0.5" style={{ color: 'var(--accent-blue)' }} />
                                    <div>
                                        <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{selected.os}</div>
                                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{selected.device}</div>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3">
                                    <Globe2 size={18} className="mt-0.5" style={{ color: 'var(--accent-purple)' }} />
                                    <div>
                                        <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{selected.browser}</div>
                                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Extracted via TLS Header Math</div>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3">
                                    <Activity size={18} className="mt-0.5" style={{ color: 'var(--accent-green)' }} />
                                    <div>
                                        <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{selected.app}</div>
                                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>Traffic Behavior Match</div>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3">
                                    <UserCheck size={18} className="mt-0.5" style={{ color: 'var(--text-muted)' }} />
                                    <div>
                                        <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{selected.location}</div>
                                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{selected.time}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {/* Traffic Volume */}
                        <div className="rounded-xl border p-5 h-48 flex flex-col" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
                            <h4 className="text-sm font-semibold mb-2 uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Encrypted Payload Volume</h4>
                            <div className="flex-1 -ml-6 mt-2">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={selected.traffic}>
                                        <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={10} tickLine={false} axisLine={false} />
                                        <Tooltip 
                                            cursor={{ fill: 'var(--bg-surface-hover)' }}
                                            contentStyle={{ backgroundColor: 'var(--bg-base)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--text-primary)' }}
                                        />
                                        <Bar dataKey="load" fill="var(--accent-blue)" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Radar Chart Analysis */}
                    <div className="col-span-2 rounded-xl border p-6 flex flex-col items-center justify-center relative" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
                        <div className="absolute top-6 left-6">
                            <h4 className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Heuristic Breakdown (ML Vector)</h4>
                            <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>Feature extraction anomalies triggering the deanonymisation rule engine.</p>
                        </div>
                        
                        <div className="w-full h-80 mt-8">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={selected.radarFields}>
                                    <PolarGrid stroke="var(--border)" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 150]} stroke="var(--text-muted)" />
                                    <Radar name="Anomaly Score" dataKey="A" stroke="var(--accent-blue)" fill="var(--accent-blue)" fillOpacity={0.4} />
                                    <Tooltip 
                                        contentStyle={{ backgroundColor: 'var(--bg-base)', borderColor: 'var(--border)', borderRadius: '8px', color: 'var(--text-primary)' }}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Overall Score Badge */}
                        <div className="absolute bottom-6 right-6 flex items-center gap-3 bg-[var(--bg-base)] border border-[var(--border)] px-4 py-2 rounded-xl">
                            <div className="text-right">
                                <div className="text-xs uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Confidence Score</div>
                                <div className="text-xl font-bold" style={{ color: 'var(--accent-blue)' }}>{selected.score}% Match</div>
                            </div>
                            <ShieldAlert size={32} className={selected.score > 85 ? "text-red-500 animate-pulse" : "text-orange-500"} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default IdentityProfiling;
