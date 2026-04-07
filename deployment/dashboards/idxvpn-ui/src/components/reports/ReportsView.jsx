import React, { useMemo, useState, useCallback } from 'react';
import {
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import {
    FileText, AlertTriangle, ShieldOff, CheckCircle2, TrendingUp,
    Wifi, Lock, Activity, ExternalLink, Download, RefreshCw
} from 'lucide-react';
import { useDashboardData } from '../../context/DashboardDataContext';
import jsPDF from 'jspdf';

/* ── Style helpers ───────────────────────────────────────────────── */
const BADGE = {
    ALLOW:     { bg: 'hsla(152,70%,45%,0.10)', color: 'var(--accent-green)',  border: 'hsla(152,70%,45%,0.30)' },
    CHALLENGE: { bg: 'hsla(35,95%,58%,0.10)',  color: 'var(--accent-orange)', border: 'hsla(35,95%,58%,0.30)' },
    BLOCK:     { bg: 'hsla(350,75%,55%,0.10)', color: 'var(--accent-red)',    border: 'hsla(350,75%,55%,0.30)' },
};
const SEV = {
    CRITICAL: { color: 'var(--accent-red)',    bg: 'hsla(350,75%,55%,0.10)', border: 'hsla(350,75%,55%,0.30)' },
    HIGH:     { color: 'var(--accent-orange)', bg: 'hsla(35,95%,58%,0.10)',  border: 'hsla(35,95%,58%,0.30)' },
    MEDIUM:   { color: '#f5c518',              bg: 'hsla(48,96%,54%,0.10)',  border: 'hsla(48,96%,54%,0.30)' },
    LOW:      { color: 'var(--accent-green)',  bg: 'hsla(152,70%,45%,0.10)', border: 'hsla(152,70%,45%,0.30)' },
};

const StatCard = ({ icon: Icon, label, value, sub, color }) => (
    <div className="p-5 rounded-2xl glass-panel flex flex-col gap-3 relative overflow-hidden"
         style={{ border: '1px solid var(--border)' }}>
        <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl -z-10"
             style={{ background: color, opacity: 0.06 }} />
        <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{label}</span>
            <Icon size={18} style={{ color }} />
        </div>
        <div className="text-3xl font-bold font-mono" style={{ color: 'var(--text-primary)' }}>{value}</div>
        {sub && <div className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{sub}</div>}
    </div>
);

const SectionTitle = ({ children, sub }) => (
    <div className="mb-4">
        <h3 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{children}</h3>
        {sub && <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{sub}</p>}
    </div>
);

/* ── Static fixtures ─────────────────────────────────────────────── */
const STATIC_THREATS = [
    { id: 1, time: '06:38:12', ip: '185.220.101.45', type: 'Tor Exit Node',     severity: 'CRITICAL', action: 'BLOCK',     country: 'Germany',     port: 9001  },
    { id: 2, time: '06:37:55', ip: '91.108.56.130',  type: 'OpenVPN Tunnel',    severity: 'HIGH',     action: 'BLOCK',     country: 'Netherlands', port: 1194  },
    { id: 3, time: '06:37:22', ip: '104.21.44.9',    type: 'HTTPS Tunnel',      severity: 'MEDIUM',   action: 'CHALLENGE', country: 'USA',         port: 443   },
    { id: 4, time: '06:36:50', ip: '192.168.1.105',  type: 'Internal Subnet',   severity: 'LOW',      action: 'ALLOW',     country: 'Local',       port: 0     },
    { id: 5, time: '06:36:18', ip: '45.79.99.100',   type: 'WireGuard Segment', severity: 'HIGH',     action: 'BLOCK',     country: 'USA',         port: 51820 },
    { id: 6, time: '06:35:44', ip: '198.41.0.4',     type: 'P2P Seed Node',     severity: 'MEDIUM',   action: 'CHALLENGE', country: 'Sweden',      port: 6881  },
];

const ANOMALIES = [
    { id: 'A1', time: '06:37:03', message: 'Spike: 4× normal packet rate on en0 — possible DDoS probe',        severity: 'CRITICAL' },
    { id: 'A2', time: '06:36:27', message: 'Encrypted payload entropy > 7.9 bits/byte — tunnel obfuscation',   severity: 'HIGH'     },
    { id: 'A3', time: '06:35:51', message: 'Destination port 443 hit from 22 unique IPs in <30 s',             severity: 'MEDIUM'   },
    { id: 'A4', time: '06:35:10', message: 'IAT std deviation below 0.1 ms — bot-like regularity detected',    severity: 'HIGH'     },
    { id: 'A5', time: '06:34:29', message: 'Payload size variance collapsed — likely fixed-size VPN padding',  severity: 'MEDIUM'   },
];

const RECS = [
    { priority: 'HIGH',   icon: Lock,          text: 'Block Tor exit nodes at perimeter — 3 active nodes detected this session.' },
    { priority: 'HIGH',   icon: ShieldOff,     text: 'Rate-limit WireGuard handshakes on public interface (quota exceeded ×5).' },
    { priority: 'MEDIUM', icon: AlertTriangle, text: 'Enforce MFA for all flows with CNN confidence < 70% on port 443.' },
    { priority: 'LOW',    icon: Wifi,          text: 'Monitor P2P flows on uplink: bandwidth share is 12% above baseline.' },
];

/* ── PDF Generator ───────────────────────────────────────────────── */
const generatePDF = ({ metrics, stats, logs }) => {
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const now = new Date();
    const W   = doc.internal.pageSize.getWidth();
    const pageH = doc.internal.pageSize.getHeight();
    let y = 0;

    const ensurePage = (needed = 12) => {
        if (y + needed > pageH - 15) { doc.addPage(); y = 20; }
    };

    /* ── Cover header ── */
    doc.setFillColor(15, 20, 36);
    doc.rect(0, 0, W, 38, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.text('IDxVPN — Network Security Report', 14, 18);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(160, 170, 191);
    doc.text(`Generated: ${now.toLocaleString()}   |   Multi-Layer VPN Detection & Deanonymisation Platform`, 14, 28);
    doc.text(`Session ID: IDX-${Date.now().toString(36).toUpperCase()}`, 14, 34);
    y = 48;

    /* ── Section helper ── */
    const sectionHeader = (title, r = 79, g = 143, b = 255) => {
        ensurePage(14);
        doc.setFillColor(r, g, b);
        doc.roundedRect(14, y, W - 28, 8, 2, 2, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(title, 18, y + 5.5);
        y += 13;
        doc.setTextColor(30, 35, 50);
    };

    const row = (label, value, indent = 14) => {
        ensurePage(8);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor(90, 106, 133);
        doc.text(label + ':', indent, y);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(20, 25, 40);
        doc.text(String(value), indent + 55, y);
        y += 7;
    };

    const divider = () => {
        ensurePage(5);
        doc.setDrawColor(230, 232, 240);
        doc.line(14, y, W - 14, y);
        y += 5;
    };

    /* ─ 1. Executive Summary ─ */
    sectionHeader('1.  Executive Summary');
    row('Report Period',           now.toLocaleDateString());
    row('Total Packets Scanned',   metrics.totalScanned.toLocaleString());
    row('ALLOW (legitimate)',       `${stats.allowed} packets (${stats.allowPct}%)`);
    row('CHALLENGE (suspicious)',   `${stats.warned} packets (${stats.warnPct}%)`);
    row('BLOCK (high-risk)',        `${stats.blocked} packets (${stats.blockPct}%)`);
    row('VPN Flows Detected',       stats.vpn);
    row('Identities Deanonymised',  metrics.deanonymisedFlows.toLocaleString());
    row('High-Risk Blocks',         metrics.highRiskBlocks.toLocaleString());
    divider();

    /* ─ 2. KPI Overview ─ */
    sectionHeader('2.  Key Performance Indicators', 27, 197, 83);
    const kpis = [
        ['Block Rate',            `${stats.blockPct}%`],
        ['Challenge Rate',        `${stats.warnPct}%`],
        ['Allow Rate',            `${stats.allowPct}%`],
        ['Deanonymisation Rate',  metrics.deanonymisedFlows > 0 ? ((metrics.deanonymisedFlows / Math.max(stats.vpn,1)) * 100).toFixed(1) + '%' : 'N/A'],
    ];
    kpis.forEach(([l, v]) => row(l, v));
    divider();

    /* ─ 3. Threat Intelligence ─ */
    sectionHeader('3.  Threat Intelligence Feed', 255, 80, 80);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(90, 106, 133);
    const TH = ['Time', 'IP Address', 'Threat Type', 'Country', 'Port', 'Severity', 'Action'];
    const CW  = [20, 36, 38, 26, 16, 22, 22];
    let tx = 14;
    TH.forEach((h, i) => { doc.text(h, tx, y); tx += CW[i]; });
    y += 2;
    doc.setDrawColor(200, 205, 215);
    doc.line(14, y, W - 14, y);
    y += 4;

    STATIC_THREATS.forEach(t => {
        ensurePage(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(20, 25, 40);
        const cells = [t.time, t.ip, t.type, t.country, String(t.port || '—'), t.severity, t.action];
        let cx = 14;
        cells.forEach((c, i) => { doc.text(c, cx, y); cx += CW[i]; });
        y += 6;
    });
    divider();

    /* ─ 4. Anomaly Detection ─ */
    sectionHeader('4.  Anomaly Detection Log', 245, 158, 11);
    ANOMALIES.forEach(a => {
        ensurePage(12);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8.5);
        doc.setTextColor(a.severity === 'CRITICAL' ? 220 : a.severity === 'HIGH' ? 200 : 150,
                         a.severity === 'CRITICAL' ? 50  : a.severity === 'HIGH' ? 80  : 130, 50);
        doc.text(`[${a.severity}]  ${a.time}`, 14, y);
        y += 5;
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(40, 45, 65);
        doc.setFontSize(8);
        const lines = doc.splitTextToSize(a.message, W - 32);
        doc.text(lines, 20, y);
        y += lines.length * 5 + 3;
    });
    divider();

    /* ─ 5. Recent Packet Log ─ */
    sectionHeader('5.  Recent Packet Log (Latest 20)', 100, 100, 220);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(90, 106, 133);
    const PH = ['Time', 'Source', 'Destination', 'Flow Type', 'Action', 'Conf.'];
    const PW  = [20, 42, 42, 32, 22, 16];
    let px = 14;
    PH.forEach((h, i) => { doc.text(h, px, y); px += PW[i]; });
    y += 2;
    doc.line(14, y, W - 14, y);
    y += 4;

    logs.slice(0, 20).forEach(l => {
        ensurePage(7);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(20, 25, 40);
        const srcIp  = l.src.split(':')[0];
        const dstIp  = (l.dst || '—').split(':')[0];
        const cells  = [l.time, srcIp, dstIp, l.flowType || '—', l.action, `${(l.confidence || 0).toFixed(0)}%`];
        let cx2 = 14;
        cells.forEach((c, i) => { doc.text(String(c), cx2, y); cx2 += PW[i]; });
        y += 6;
    });
    divider();

    /* ─ 6. Recommendations ─ */
    sectionHeader('6.  Security Recommendations', 150, 100, 250);
    RECS.forEach((r, i) => {
        ensurePage(14);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(r.priority === 'HIGH' ? 220 : r.priority === 'MEDIUM' ? 180 : 80,
                         r.priority === 'HIGH' ? 90  : r.priority === 'MEDIUM' ? 140 : 180, 60);
        doc.text(`${i + 1}. [${r.priority}]`, 14, y);
        y += 5;
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(40, 45, 65);
        doc.setFontSize(8.5);
        const lines = doc.splitTextToSize(r.text, W - 32);
        doc.text(lines, 20, y);
        y += lines.length * 5 + 4;
    });

    /* ── Footer on every page ── */
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(7.5);
        doc.setTextColor(160, 170, 191);
        doc.text(`IDxVPN Security Report  |  Page ${i} of ${pageCount}  |  Confidential`, 14, pageH - 8);
        doc.text(now.toLocaleString(), W - 14, pageH - 8, { align: 'right' });
    }

    doc.save(`IDxVPN_Security_Report_${now.toLocaleDateString('en-GB').replace(/\//g, '-')}.pdf`);
};

/* ── Main Component ─────────────────────────────────────────────── */
const ReportsView = () => {
    const { logs, metrics }   = useDashboardData();
    const [activeTab, setActiveTab] = useState('overview');
    const [refreshKey, setRefreshKey] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isExporting, setIsExporting]   = useState(false);

    /* ─ Refresh handler ─ */
    const handleRefresh = useCallback(() => {
        setIsRefreshing(true);
        setTimeout(() => { setRefreshKey(k => k + 1); setIsRefreshing(false); }, 600);
    }, []);

    /* ─ PDF handler ─ */
    const handleExport = useCallback(async () => {
        setIsExporting(true);
        await new Promise(r => setTimeout(r, 300)); // let UI update
        generatePDF({ metrics, stats, logs });
        setIsExporting(false);
    }, [metrics, logs]); // stats captured below via closure

    /* ─ Derived stats ─ */
    const stats = useMemo(() => {
        const total    = logs.length || 1;
        const blocked  = logs.filter(l => l.action === 'BLOCK').length;
        const warned   = logs.filter(l => l.action === 'CHALLENGE').length;
        const allowed  = logs.filter(l => l.action === 'ALLOW').length;
        const vpn      = logs.filter(l => l.isVpn).length;
        return {
            total, blocked, warned, allowed, vpn,
            blockPct: ((blocked / total) * 100).toFixed(1),
            warnPct:  ((warned  / total) * 100).toFixed(1),
            allowPct: ((allowed / total) * 100).toFixed(1),
        };
    }, [logs, refreshKey]);

    /* ─ Pie data ─ */
    const pieData = useMemo(() => [
        { name: 'ALLOW',     value: Math.max(stats.allowed,  1), color: '#1bc553' },
        { name: 'CHALLENGE', value: Math.max(stats.warned,   1), color: '#ff9900' },
        { name: 'BLOCK',     value: Math.max(stats.blocked,  1), color: '#ff5050' },
    ], [stats]);

    /* ─ Bar data ─ */
    const flowTypeData = useMemo(() => {
        const map = {};
        logs.forEach(l => { map[l.flowType] = (map[l.flowType] || 0) + 1; });
        return Object.entries(map).map(([name, count]) => ({ name, count }))
                     .sort((a, b) => b.count - a.count).slice(0, 8);
    }, [logs, refreshKey]);

    /* ─ Timeline: bucket logs into 5-second windows, count allowed/warned/blocked per window ─ */
    const timelineData = useMemo(() => {
        if (!logs.length) return [];
        // Group by HH:MM:SS but snap seconds to 5-second buckets
        const buckets = {};
        [...logs].reverse().forEach(l => {
            const parts = l.time.split(':');
            if (parts.length < 3) return;
            const snapped = Math.floor(parseInt(parts[2]) / 5) * 5;
            const key = `${parts[0]}:${parts[1]}:${String(snapped).padStart(2, '0')}`;
            if (!buckets[key]) buckets[key] = { t: key, allowed: 0, warned: 0, blocked: 0 };
            if (l.action === 'ALLOW')     buckets[key].allowed++;
            else if (l.action === 'CHALLENGE') buckets[key].warned++;
            else if (l.action === 'BLOCK')     buckets[key].blocked++;
        });
        return Object.values(buckets).slice(-15); // last 15 windows
    }, [logs, refreshKey]);

    const TABS = ['overview', 'threats', 'anomalies', 'network', 'recommendations'];

    const tooltipStyle = {
        backgroundColor: 'rgba(12,16,28,0.97)',
        borderColor: 'rgba(255,255,255,0.08)',
        borderRadius: '10px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
        fontSize: '12px',
        color: '#e2e8f0',
        padding: '10px 14px',
    };

    return (
        <div className="space-y-6 animate-fade-in-up" key={refreshKey}>

            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl glass-panel relative overflow-hidden"
                 style={{ border: '1px solid var(--border)' }}>
                <div className="absolute top-0 right-0 w-72 h-48 bg-[var(--accent-blue)] opacity-5 rounded-full blur-3xl -z-10" />
                <div>
                    <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3" style={{ color: 'var(--text-primary)' }}>
                        <FileText className="text-[var(--accent-blue)]" size={30} />
                        Network Security Reports
                    </h2>
                    <p className="mt-1 font-medium" style={{ color: 'var(--text-secondary)' }}>
                        Live anomaly, threat, and network health overview for your infrastructure.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all active:scale-95"
                        style={{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text-secondary)', opacity: isRefreshing ? 0.7 : 1 }}>
                        <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
                        {isRefreshing ? 'Refreshing…' : 'Refresh'}
                    </button>
                    <button
                        onClick={handleExport}
                        disabled={isExporting}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all active:scale-95"
                        style={{ background: 'hsla(210,100%,60%,0.12)', border: '1px solid var(--accent-blue)', color: 'var(--accent-blue)', opacity: isExporting ? 0.7 : 1 }}>
                        <Download size={14} className={isExporting ? 'animate-bounce' : ''} />
                        {isExporting ? 'Generating…' : 'Export PDF'}
                    </button>
                </div>
            </div>

            {/* Tab Bar */}
            <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}>
                {TABS.map(t => (
                    <button key={t} onClick={() => setActiveTab(t)}
                            className="flex-1 py-2 rounded-lg text-xs sm:text-sm font-semibold capitalize transition-all"
                            style={{
                                background: activeTab === t ? 'var(--accent-blue-glow)' : 'transparent',
                                color:      activeTab === t ? 'var(--accent-blue)'       : 'var(--text-secondary)',
                                border:     activeTab === t ? '1px solid var(--accent-blue)' : '1px solid transparent',
                            }}>
                        {t}
                    </button>
                ))}
            </div>

            {/* ══ OVERVIEW ══ */}
            {activeTab === 'overview' && (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard icon={Activity}      label="Total Scanned"  value={metrics.totalScanned.toLocaleString()} sub="Packets this session"          color="var(--accent-blue)"   />
                        <StatCard icon={CheckCircle2}  label="Allowed"        value={stats.allowed.toLocaleString()}        sub={`${stats.allowPct}% of traffic`} color="var(--accent-green)"  />
                        <StatCard icon={AlertTriangle} label="Challenged"     value={stats.warned.toLocaleString()}         sub={`${stats.warnPct}% flagged`}    color="var(--accent-orange)" />
                        <StatCard icon={ShieldOff}     label="Blocked"        value={stats.blocked.toLocaleString()}        sub={`${stats.blockPct}% threats`}   color="var(--accent-red)"    />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Timeline area chart — properly bucketed */}
                        <div className="lg:col-span-2 p-6 rounded-2xl glass-panel" style={{ border: '1px solid var(--border)' }}>
                            <SectionTitle sub="Packets per 5-second window — allow, challenge & block counts">Packet Action Timeline</SectionTitle>
                            <div className="h-[280px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={timelineData} margin={{ top: 10, right: 10, bottom: 0, left: -10 }}>
                                        <defs>
                                            <linearGradient id="gA" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%"  stopColor="#1bc553" stopOpacity={0.35}/>
                                                <stop offset="95%" stopColor="#1bc553" stopOpacity={0}/>
                                            </linearGradient>
                                            <linearGradient id="gW" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%"  stopColor="#ff9900" stopOpacity={0.35}/>
                                                <stop offset="95%" stopColor="#ff9900" stopOpacity={0}/>
                                            </linearGradient>
                                            <linearGradient id="gB" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%"  stopColor="#ff5050" stopOpacity={0.35}/>
                                                <stop offset="95%" stopColor="#ff5050" stopOpacity={0}/>
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff14" vertical={false} />
                                        <XAxis
                                            dataKey="t"
                                            tick={{ fill: '#5a6a85', fontSize: 9 }}
                                            axisLine={false} tickLine={false}
                                            tickFormatter={v => v.slice(3)} // show MM:SS only
                                            interval="preserveStartEnd"
                                        />
                                        <YAxis
                                            tick={{ fill: '#5a6a85', fontSize: 10 }}
                                            axisLine={false} tickLine={false}
                                            allowDecimals={false}
                                            width={28}
                                        />
                                        <Tooltip
                                            contentStyle={tooltipStyle}
                                            labelFormatter={v => `Window: ${v}`}
                                            formatter={(val, name) => [`${val} pkts`, name]}
                                        />
                                        <Area type="monotone" dataKey="allowed" name="ALLOW"     stroke="#1bc553" strokeWidth={2.5} fill="url(#gA)" dot={false} activeDot={{ r: 5 }} />
                                        <Area type="monotone" dataKey="warned"  name="CHALLENGE" stroke="#ff9900" strokeWidth={2.5} fill="url(#gW)" dot={false} activeDot={{ r: 5 }} />
                                        <Area type="monotone" dataKey="blocked" name="BLOCK"     stroke="#ff5050" strokeWidth={2.5} fill="url(#gB)" dot={false} activeDot={{ r: 5 }} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Donut */}
                        <div className="p-6 rounded-2xl glass-panel flex flex-col" style={{ border: '1px solid var(--border)' }}>
                            <SectionTitle sub="Distribution by policy action">Traffic Split</SectionTitle>
                            <div className="flex-1 min-h-[240px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie data={pieData} cx="50%" cy="45%" innerRadius={58} outerRadius={88} paddingAngle={4} dataKey="value" stroke="none">
                                            {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
                                        </Pie>
                                        <Tooltip contentStyle={tooltipStyle} formatter={(v, n) => [`${v} packets`, n]} />
                                        <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', color: '#a0aabf' }} />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Recent log */}
                    <div className="rounded-2xl glass-panel overflow-hidden" style={{ border: '1px solid var(--border)' }}>
                        <div className="p-5 flex justify-between items-center" style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
                            <h3 className="font-bold" style={{ color: 'var(--text-primary)' }}>Recent Packet Log</h3>
                            <span className="text-xs px-2 py-1 rounded-full" style={{ background: 'var(--bg-input)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>Last {logs.length} packets</span>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm whitespace-nowrap">
                                <thead>
                                    <tr style={{ background: 'var(--bg-surface-hover)' }}>
                                        {['Time', 'Source → Dest', 'Flow Type', 'Action', 'Confidence'].map(h => (
                                            <th key={h} className="p-3 text-left text-xs uppercase tracking-wider font-semibold"
                                                style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.slice(0, 15).map(l => (
                                        <tr key={l.id} style={{ borderBottom: '1px solid var(--border)' }}
                                            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-surface-hover)'}
                                            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                                            <td className="p-3 font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{l.time}</td>
                                            <td className="p-3 font-mono text-xs">
                                                <div style={{ color: 'var(--text-primary)' }}>{l.src}</div>
                                                <div style={{ color: 'var(--text-muted)' }}>→ {l.dst}</div>
                                            </td>
                                            <td className="p-3 text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{l.flowType}</td>
                                            <td className="p-3">
                                                <span className="px-2 py-0.5 rounded text-xs font-bold"
                                                      style={{ background: BADGE[l.action]?.bg, color: BADGE[l.action]?.color, border: `1px solid ${BADGE[l.action]?.border}` }}>
                                                    {l.action}
                                                </span>
                                            </td>
                                            <td className="p-3 text-xs font-mono" style={{ color: 'var(--text-primary)' }}>{l.confidence?.toFixed(1)}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* ══ THREATS ══ */}
            {activeTab === 'threats' && (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard icon={ShieldOff}     label="Blocked Threats"  value={metrics.highRiskBlocks.toLocaleString()}    sub="Policy engine decisions"  color="var(--accent-red)"    />
                        <StatCard icon={AlertTriangle} label="Active VPN Nodes" value={stats.vpn.toLocaleString()}                  sub="Detected this session"    color="var(--accent-orange)" />
                        <StatCard icon={TrendingUp}    label="Block Rate"        value={`${stats.blockPct}%`}                       sub="Of all intercepted flows" color="var(--accent-purple)" />
                        <StatCard icon={Lock}          label="Deanonymised"      value={metrics.deanonymisedFlows.toLocaleString()} sub="Identities resolved"      color="var(--accent-blue)"   />
                    </div>
                    <div className="rounded-2xl glass-panel overflow-hidden" style={{ border: '1px solid var(--border)' }}>
                        <div className="p-5 flex justify-between items-center" style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
                            <h3 className="font-bold" style={{ color: 'var(--text-primary)' }}>Threat Intelligence Feed</h3>
                            <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: 'var(--accent-red)' }}>
                                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" /> LIVE
                            </span>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm whitespace-nowrap">
                                <thead>
                                    <tr style={{ background: 'var(--bg-surface-hover)' }}>
                                        {['Time', 'IP Address', 'Threat Type', 'Country', 'Port', 'Severity', 'Action'].map(h => (
                                            <th key={h} className="p-3 text-left text-xs uppercase tracking-wider font-semibold"
                                                style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {STATIC_THREATS.map(t => (
                                        <tr key={t.id} style={{ borderBottom: '1px solid var(--border)' }}
                                            onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-surface-hover)'}
                                            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                                            <td className="p-3 font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{t.time}</td>
                                            <td className="p-3 font-mono text-xs font-bold" style={{ color: 'var(--accent-blue)' }}>{t.ip}</td>
                                            <td className="p-3 text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{t.type}</td>
                                            <td className="p-3 text-xs" style={{ color: 'var(--text-secondary)' }}>{t.country}</td>
                                            <td className="p-3 font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{t.port || '—'}</td>
                                            <td className="p-3">
                                                <span className="px-2 py-0.5 rounded text-xs font-bold"
                                                      style={{ background: SEV[t.severity]?.bg, color: SEV[t.severity]?.color, border: `1px solid ${SEV[t.severity]?.border}` }}>
                                                    {t.severity}
                                                </span>
                                            </td>
                                            <td className="p-3">
                                                <span className="px-2 py-0.5 rounded text-xs font-bold"
                                                      style={{ background: BADGE[t.action]?.bg, color: BADGE[t.action]?.color, border: `1px solid ${BADGE[t.action]?.border}` }}>
                                                    {t.action}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* ══ ANOMALIES ══ */}
            {activeTab === 'anomalies' && (
                <div className="space-y-4">
                    <div className="p-5 rounded-2xl glass-panel" style={{ border: '1px solid var(--border)', background: 'hsla(350,75%,55%,0.05)' }}>
                        <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                            ⚠️ IDxVPN detected <strong style={{ color: 'var(--accent-red)' }}>{ANOMALIES.filter(a => a.severity === 'CRITICAL').length} critical</strong> and <strong style={{ color: 'var(--accent-orange)' }}>{ANOMALIES.filter(a => a.severity === 'HIGH').length} high-severity</strong> anomalies in the last scan window. Immediate review recommended.
                        </p>
                    </div>
                    {ANOMALIES.map(a => (
                        <div key={a.id} className="p-4 rounded-2xl glass-panel flex items-start gap-4"
                             style={{ border: `1px solid ${SEV[a.severity]?.border}` }}>
                            <div className="mt-1 w-2.5 h-2.5 rounded-full shrink-0"
                                 style={{ background: SEV[a.severity]?.color, boxShadow: `0 0 8px ${SEV[a.severity]?.color}` }} />
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-1">
                                    <span className="px-2 py-0.5 rounded text-xs font-bold"
                                          style={{ background: SEV[a.severity]?.bg, color: SEV[a.severity]?.color, border: `1px solid ${SEV[a.severity]?.border}` }}>{a.severity}</span>
                                    <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{a.time}</span>
                                </div>
                                <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{a.message}</p>
                            </div>
                            <ExternalLink size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} className="mt-1 cursor-pointer" />
                        </div>
                    ))}
                </div>
            )}

            {/* ══ NETWORK ══ */}
            {activeTab === 'network' && (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="p-6 rounded-2xl glass-panel" style={{ border: '1px solid var(--border)' }}>
                            <SectionTitle sub="Top intercepted flow types by packet volume">Flow Type Distribution</SectionTitle>
                            <div className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={flowTypeData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff14" horizontal={false} />
                                        <XAxis type="number" tick={{ fill: '#5a6a85', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                                        <YAxis type="category" dataKey="name" tick={{ fill: '#a0aabf', fontSize: 10 }} axisLine={false} tickLine={false} width={90} />
                                        <Tooltip contentStyle={tooltipStyle} />
                                        <Bar dataKey="count" name="Packets" radius={[0, 4, 4, 0]} fill="var(--accent-blue)" fillOpacity={0.8} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                        <div className="p-6 rounded-2xl glass-panel" style={{ border: '1px solid var(--border)' }}>
                            <SectionTitle sub="Interface and protocol health status">Network Interface Status</SectionTitle>
                            <div className="space-y-3 mt-2">
                                {[
                                    { name: 'en0 (Wi-Fi)',      status: 'ACTIVE',     packets: '14.2k', load: 72, color: 'var(--accent-green)'  },
                                    { name: 'en1 (Ethernet)',   status: 'IDLE',       packets: '0.0k',  load: 0,  color: 'var(--text-muted)'    },
                                    { name: 'utun0 (Loopback)', status: 'MONITORING', packets: '1.8k',  load: 18, color: 'var(--accent-blue)'   },
                                    { name: 'pflog0 (PF log)',  status: 'BLOCKED',    packets: '0.3k',  load: 3,  color: 'var(--accent-orange)' },
                                ].map(iface => (
                                    <div key={iface.name} className="p-3 rounded-xl" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}>
                                        <div className="flex justify-between items-center mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full" style={{ background: iface.color, boxShadow: `0 0 6px ${iface.color}` }} />
                                                <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{iface.name}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{iface.packets} pkts</span>
                                                <span className="text-xs font-bold px-2 py-0.5 rounded"
                                                      style={{ color: iface.color, background: `${iface.color}18`, border: `1px solid ${iface.color}44` }}>{iface.status}</span>
                                            </div>
                                        </div>
                                        <div className="h-1.5 rounded-full" style={{ background: 'var(--border)' }}>
                                            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${iface.load}%`, background: iface.color }} />
                                        </div>
                                        <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{iface.load}% load</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    <div className="p-6 rounded-2xl glass-panel" style={{ border: '1px solid var(--border)' }}>
                        <SectionTitle sub="Packets grouped by transport protocol">Protocol Summary</SectionTitle>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            {[
                                { proto: 'TCP',   share: 68, color: 'var(--accent-blue)'   },
                                { proto: 'UDP',   share: 24, color: 'var(--accent-purple)'  },
                                { proto: 'ICMP',  share: 5,  color: 'var(--accent-orange)'  },
                                { proto: 'Other', share: 3,  color: 'var(--text-muted)'     },
                            ].map(p => (
                                <div key={p.proto} className="p-4 rounded-xl text-center" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}>
                                    <div className="text-3xl font-bold font-mono mb-1" style={{ color: p.color }}>{p.share}%</div>
                                    <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{p.proto}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* ══ RECOMMENDATIONS ══ */}
            {activeTab === 'recommendations' && (
                <div className="space-y-4">
                    <div className="p-5 rounded-2xl glass-panel" style={{ border: '1px solid var(--border)', background: 'hsla(210,100%,60%,0.04)' }}>
                        <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                            💡 The following recommendations are generated by IDxVPN based on live traffic analysis this session. Prioritise <strong style={{ color: 'var(--accent-red)' }}>HIGH</strong> items immediately.
                        </p>
                    </div>
                    {RECS.map((r, i) => {
                        const Icon = r.icon;
                        return (
                            <div key={i} className="p-5 rounded-2xl glass-panel flex items-start gap-4"
                                 style={{ border: `1px solid ${SEV[r.priority]?.border}` }}>
                                <div className="p-2 rounded-lg shrink-0" style={{ background: SEV[r.priority]?.bg, color: SEV[r.priority]?.color }}>
                                    <Icon size={18} />
                                </div>
                                <div className="flex-1">
                                    <span className="px-2 py-0.5 rounded text-xs font-bold mr-2"
                                          style={{ background: SEV[r.priority]?.bg, color: SEV[r.priority]?.color, border: `1px solid ${SEV[r.priority]?.border}` }}>
                                        {r.priority}
                                    </span>
                                    <p className="mt-2 text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{r.text}</p>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default ReportsView;
