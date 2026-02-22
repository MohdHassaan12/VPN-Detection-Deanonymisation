import React, { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';

const LiveInferenceTable = ({ logs }) => {
    const getActionBadge = (action) => {
        switch (action) {
            case 'ALLOW': return <span className="bg-[#1bc553]/10 text-[#1bc553] px-3 py-1 rounded-full text-xs font-bold border border-[#1bc553]/20">ALLOW</span>;
            case 'CHALLENGE': return <span className="bg-[#ff9900]/10 text-[#ff9900] px-3 py-1 rounded-full text-xs font-bold border border-[#ff9900]/20">CHALLENGE</span>;
            case 'BLOCK': return <span className="bg-[#ff5050]/10 text-[#ff5050] px-3 py-1 rounded-full text-xs font-bold border border-[#ff5050]/20">BLOCK</span>;
            default: return null;
        }
    };

    return (
        <div className="glass-panel rounded-2xl border border-divider overflow-hidden">
            <div className="p-6 border-b border-divider flex justify-between items-center bg-panel">
                <h3 className="text-lg font-bold flex items-center gap-2">
                    <Activity size={20} className="text-[#4f8fff]" />
                    Live Inference Stream
                </h3>
                <span className="text-xs text-muted font-mono bg-black/5 dark:bg-black/40 px-3 py-1 rounded-full border border-divider">
                    Last updated: {new Date().toLocaleTimeString()}
                </span>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse whitespace-nowrap">
                    <thead>
                        <tr className="bg-black/5 dark:bg-white/5 text-muted text-xs uppercase tracking-wider">
                            <th className="p-4 border-b border-divider font-medium">Time</th>
                            <th className="p-4 border-b border-divider font-medium">Source / Dest</th>
                            <th className="p-4 border-b border-divider font-medium">Flow Type</th>
                            <th className="p-4 border-b border-divider font-medium text-center">Is VPN?</th>
                            <th className="p-4 border-b border-divider font-medium text-center">Deanonymised?</th>
                            <th className="p-4 border-b border-divider font-medium">CNN Conf.</th>
                            <th className="p-4 border-b border-divider font-medium text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="font-mono text-sm max-h-[300px] overflow-y-auto w-full">
                        {logs && logs.map((log) => (
                            <tr key={log.id} className="border-b border-divider hover:bg-black/5 dark:bg-white/5 transition-colors animate-fade-in-up">
                                <td className="p-4 text-muted text-xs">{log.time}</td>
                                <td className="p-4">
                                    <div className="flex flex-col">
                                        <span className="text-default">{log.src}</span>
                                        <span className="text-muted text-xs">→ {log.dst}</span>
                                    </div>
                                </td>
                                <td className="p-4 font-bold text-default tracking-wide">{log.flowType}</td>
                                <td className="p-4 text-center">
                                    {log.isVpn ? (
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#ff9900]/10 text-[#ff9900] border border-[#ff9900]/20">YES</span>
                                    ) : (
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-black/5 dark:bg-white/5 text-muted border border-divider">NO</span>
                                    )}
                                </td>
                                <td className="p-4 text-center">
                                    {log.isVpn && log.deanonymised ? (
                                        <div className="flex flex-col items-center">
                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#1bc553]/10 text-[#1bc553] border border-[#1bc553]/20 mb-1">YES</span>
                                            <span className="text-xs text-[#4f8fff] font-bold">{log.trueApp}</span>
                                        </div>
                                    ) : log.isVpn && !log.deanonymised ? (
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#ff5050]/10 text-[#ff5050] border border-[#ff5050]/20">FAILED</span>
                                    ) : (
                                        <span className="text-muted text-xs">-</span>
                                    )}
                                </td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-12 h-1.5 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden hidden sm:block">
                                            <div
                                                className="h-full bg-gradient-to-r from-[#2555ff] to-[#4f8fff]"
                                                style={{ width: `${log.confidence}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-xs">{log.confidence}%</span>
                                    </div>
                                </td>
                                <td className="p-4 text-right">
                                    {getActionBadge(log.action)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default LiveInferenceTable;
