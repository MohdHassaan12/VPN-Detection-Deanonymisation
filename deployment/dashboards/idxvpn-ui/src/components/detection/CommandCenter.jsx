import React, { useState, useEffect } from 'react';
import { ComposableMap, Geographies, Geography, Marker, Line } from 'react-simple-maps';
import { ShieldAlert, Activity, Globe } from 'lucide-react';

const geoUrl = "https://unpkg.com/world-atlas@2.0.2/countries-110m.json";

// SOC HQ location (e.g., New York)
const hqCoord = [-74.006, 40.7128];

const generateRandomThreat = () => {
    return {
        id: Math.random().toString(36).substr(2, 9),
        // Random coords, mostly avoiding oceans for realism, but perfectly random [lng, lat]
        coord: [ (Math.random() * 360) - 180, (Math.random() * 140) - 70 ],
        type: Math.random() > 0.5 ? 'VPN Node' : 'Tor Exit Router',
        ip: `${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}`,
        timestamp: new Date().toLocaleTimeString(),
        confidence: Math.floor(Math.random() * 20) + 80 // 80 to 100
    };
};

const CommandCenter = () => {
    const [threats, setThreats] = useState(() => Array.from({ length: 3 }, generateRandomThreat));

    useEffect(() => {
        const interval = setInterval(() => {
            setThreats(prev => {
                const updated = [...prev, generateRandomThreat()];
                if (updated.length > 8) updated.shift(); // Keep max 8 active routes
                return updated;
            });
        }, 3000); // New threat every 3 seconds
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col h-full gap-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                        <Globe className="text-[var(--accent-blue)]" />
                        Live Geo-IP Tracking
                    </h2>
                    <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                        Global encrypted traffic intercepts and deanonymisation nodes.
                    </p>
                </div>
                <div className="flex gap-4">
                    <div className="px-4 py-2 rounded-lg flex items-center gap-2" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}>
                        <div className="w-2 h-2 rounded-full animate-pulse bg-red-500" />
                        <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Active Threats: {threats.length}</span>
                    </div>
                </div>
            </div>

            {/* Map Container */}
            <div className="flex-1 rounded-xl relative overflow-hidden" 
                 style={{ 
                     background: 'radial-gradient(ellipse at center, var(--bg-surface) 0%, var(--bg-base) 100%)', 
                     border: '1px solid var(--border)' 
                 }}>
                
                {/* Overlay UI inside Map */}
                <div className="absolute top-4 left-4 z-10 w-72 rounded-xl backdrop-blur-md p-4"
                     style={{ background: 'var(--bg-surface-hover)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-card)' }}>
                    <div className="flex items-center gap-2 mb-4" style={{ color: 'var(--text-primary)' }}>
                        <Activity size={18} />
                        <h3 className="font-semibold text-sm">Real-Time Intercepts</h3>
                    </div>
                    <div className="space-y-3">
                        {threats.slice().reverse().slice(0, 4).map(t => (
                            <div key={t.id} className="text-xs p-2 rounded bg-black/20 border border-[var(--border)]">
                                <div className="flex justify-between mb-1">
                                    <span style={{ color: 'var(--accent-blue)' }} className="font-mono">{t.ip}</span>
                                    <span style={{ color: 'var(--text-muted)' }}>{t.timestamp}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span style={{ color: 'var(--text-secondary)' }}>{t.type}</span>
                                    <span style={{ color: 'var(--accent-red)' }}>{t.confidence}% Risk</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <ComposableMap
                    projectionConfig={{ scale: 180, center: [0, 20] }}
                    className="w-full h-full object-cover"
                >
                    <Geographies geography={geoUrl}>
                        {({ geographies }) =>
                            geographies.map((geo) => (
                                <Geography
                                    key={geo.rsmKey}
                                    geography={geo}
                                    fill="var(--bg-surface)"
                                    stroke="var(--border)"
                                    strokeWidth={0.5}
                                    style={{
                                        default: { outline: "none" },
                                        hover: { fill: "var(--accent-blue-glow)", outline: "none" },
                                        pressed: { outline: "none" },
                                    }}
                                />
                            ))
                        }
                    </Geographies>

                    {/* Threat Links */}
                    {threats.map((t, index) => (
                        <Line
                            key={t.id}
                            from={t.coord}
                            to={hqCoord}
                            stroke="url(#gradient)"
                            strokeWidth={1.5}
                            strokeLinecap="round"
                            className="transition-all duration-1000"
                            style={{ opacity: 0.6 + (index * 0.05) }}
                        />
                    ))}

                    {/* HQ Marker */}
                    <Marker coordinates={hqCoord}>
                        <circle r={6} fill="var(--accent-blue)" />
                        <circle r={12} fill="var(--accent-blue)" opacity={0.3} className="animate-ping" />
                    </Marker>

                    {/* Threat Markers */}
                    {threats.map((t) => (
                        <Marker key={t.id} coordinates={t.coord}>
                            <circle r={4} fill="var(--accent-red)" />
                            <circle r={8} fill="currentColor" opacity={0.2} style={{ color: 'var(--accent-red)' }} className="animate-ping" />
                        </Marker>
                    ))}

                    <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="var(--accent-red)" stopOpacity="1" />
                            <stop offset="100%" stopColor="var(--accent-blue)" stopOpacity="0.1" />
                        </linearGradient>
                    </defs>
                </ComposableMap>
            </div>
        </div>
    );
};

export default CommandCenter;
