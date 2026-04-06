import React, { useState, useEffect } from 'react';
import { Activity, Wifi } from 'lucide-react';

const LiveInferenceTable = ({ logs }) => {
    // Tick the "last updated" timestamp every second
    const [now, setNow] = useState(new Date());
    useEffect(() => {
        const t = setInterval(() => setNow(new Date()), 1000);
        return () => clearInterval(t);
    }, []);

    const getActionBadge = (action) => {
        const styles = {
            ALLOW:     { bg: 'hsla(152,70%,45%,0.10)', color: 'var(--accent-green)',  border: 'hsla(152,70%,45%,0.30)' },
            CHALLENGE: { bg: 'hsla(35,95%,58%,0.10)',  color: 'var(--accent-orange)', border: 'hsla(35,95%,58%,0.30)' },
            BLOCK:     { bg: 'hsla(350,75%,55%,0.10)', color: 'var(--accent-red)',    border: 'hsla(350,75%,55%,0.30)' },
        };
        const s = styles[action];
        if (!s) return null;
        return (
            <span
                className="px-3 py-1 rounded-full text-xs font-bold"
                style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}` }}
            >
                {action}
            </span>
        );
    };

    return (
        <div
            className="glass-panel rounded-2xl overflow-hidden"
            style={{ border: '1px solid var(--border)' }}
        >
            {/* Header */}
            <div
                className="p-5 flex justify-between items-center"
                style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}
            >
                <h3 className="text-lg font-bold flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                    <Activity size={20} style={{ color: 'var(--accent-blue)' }} />
                    Live Inference Stream
                    {/* live pulse dot */}
                    <span
                        className="w-2 h-2 rounded-full animate-pulse ml-1"
                        style={{ background: 'var(--accent-green)', boxShadow: '0 0 6px var(--accent-green)' }}
                    />
                </h3>
                <span
                    className="text-xs font-mono px-3 py-1 rounded-full"
                    style={{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
                >
                    Last updated: {now.toLocaleTimeString('en-US', { hour12: false })}
                </span>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse whitespace-nowrap">
                    <thead>
                        <tr style={{ background: 'var(--bg-surface-hover)' }}>
                            {['Time', 'Source / Dest', 'Flow Type', 'Is VPN?', 'Deanonymised?', 'CNN Conf.', 'Action'].map((h, i) => (
                                <th
                                    key={h}
                                    className="p-4 text-xs uppercase tracking-wider font-semibold"
                                    style={{
                                        borderBottom: '1px solid var(--border)',
                                        color: 'var(--text-muted)',
                                        textAlign: i >= 5 ? 'right' : i === 3 || i === 4 ? 'center' : 'left',
                                    }}
                                >
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {(!logs || logs.length === 0) ? (
                            <tr>
                                <td colSpan={7} className="text-center py-16">
                                    <div className="flex flex-col items-center gap-3">
                                        <Wifi size={28} style={{ color: 'var(--text-muted)' }} className="animate-pulse" />
                                        <span style={{ color: 'var(--text-muted)' }} className="text-sm">
                                            Connecting to packet stream…
                                        </span>
                                    </div>
                                </td>
                            </tr>
                        ) : logs.map((log) => (
                            <tr
                                key={log.id}
                                className="transition-colors animate-fade-in-up"
                                style={{ borderBottom: '1px solid var(--border)' }}
                                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-surface-hover)'}
                                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                            >
                                {/* Time */}
                                <td className="p-4 text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                                    {log.time}
                                </td>

                                {/* Source / Dest */}
                                <td className="p-4 font-mono text-xs">
                                    <div style={{ color: 'var(--text-primary)' }}>{log.src}</div>
                                    <div style={{ color: 'var(--text-muted)' }}>→ {log.dst}</div>
                                </td>

                                {/* Flow Type */}
                                <td className="p-4 text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                                    {log.flowType}
                                </td>

                                {/* Is VPN? */}
                                <td className="p-4 text-center">
                                    {log.isVpn ? (
                                        <span
                                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                                            style={{ background: 'hsla(35,95%,58%,0.10)', color: 'var(--accent-orange)', border: '1px solid hsla(35,95%,58%,0.25)' }}
                                        >
                                            YES
                                        </span>
                                    ) : (
                                        <span
                                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                                            style={{ background: 'var(--bg-input)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
                                        >
                                            NO
                                        </span>
                                    )}
                                </td>

                                {/* Deanonymised? */}
                                <td className="p-4 text-center">
                                    {log.isVpn && log.deanonymised ? (
                                        <div className="flex flex-col items-center gap-0.5">
                                            <span
                                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                                                style={{ background: 'hsla(152,70%,45%,0.10)', color: 'var(--accent-green)', border: '1px solid hsla(152,70%,45%,0.25)' }}
                                            >
                                                YES
                                            </span>
                                            <span className="text-xs font-bold" style={{ color: 'var(--accent-blue)' }}>
                                                {log.trueApp}
                                            </span>
                                        </div>
                                    ) : log.isVpn && !log.deanonymised ? (
                                        <span
                                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                                            style={{ background: 'hsla(350,75%,55%,0.10)', color: 'var(--accent-red)', border: '1px solid hsla(350,75%,55%,0.25)' }}
                                        >
                                            FAILED
                                        </span>
                                    ) : (
                                        <span style={{ color: 'var(--text-muted)' }} className="text-xs">—</span>
                                    )}
                                </td>

                                {/* CNN Conf */}
                                <td className="p-4 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        <div
                                            className="w-12 h-1.5 rounded-full overflow-hidden hidden sm:block"
                                            style={{ background: 'var(--border)' }}
                                        >
                                            <div
                                                className="h-full rounded-full"
                                                style={{
                                                    width: `${log.confidence}%`,
                                                    background: log.confidence > 85
                                                        ? 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))'
                                                        : 'linear-gradient(90deg, var(--accent-orange), var(--accent-red))',
                                                }}
                                            />
                                        </div>
                                        <span className="text-xs font-mono" style={{ color: 'var(--text-primary)' }}>
                                            {log.confidence}%
                                        </span>
                                    </div>
                                </td>

                                {/* Action */}
                                <td className="p-4 text-right">{getActionBadge(log.action)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default LiveInferenceTable;
