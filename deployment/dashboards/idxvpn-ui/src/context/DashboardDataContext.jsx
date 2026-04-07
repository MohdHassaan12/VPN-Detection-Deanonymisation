import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

const DashboardDataContext = createContext(null);

/* ─── Synthetic data helpers ──────────────────────────────────── */
const FLOW_TYPES    = ['Streaming','VoIP (Teams)','P2P Files','WhatsApp','Web Browsing','HTTPS Tunnel','SSH','OpenVPN','WireGuard'];
const TRUE_APPS     = ['Netflix','YouTube','Teams','WhatsApp','BitTorrent','Discord','Zoom','Skype'];
const ACTIONS       = ['ALLOW','CHALLENGE','BLOCK'];
const ACTION_W      = [0.55, 0.30, 0.15];

const randIP   = () => `${10 + ~~(Math.random() * 245)}.${~~(Math.random() * 255)}.${~~(Math.random() * 255)}.${1 + ~~(Math.random() * 254)}`;
const randPort = () => 1024 + ~~(Math.random() * 64511);
const pick     = arr => arr[~~(Math.random() * arr.length)];
const wAction  = () => { const r = Math.random(); return r < ACTION_W[0] ? ACTIONS[0] : r < ACTION_W[0] + ACTION_W[1] ? ACTIONS[1] : ACTIONS[2]; };

let _id = 1;
const makeLog = () => {
    const isVpn       = Math.random() < 0.26;
    const deanonymised = isVpn && Math.random() < 0.92;
    const action      = isVpn ? wAction() : 'ALLOW';
    const confidence  = isVpn ? 82 + ~~(Math.random() * 17) : 40 + ~~(Math.random() * 35);
    const now         = new Date();
    
    // Geographical OSINT fallbacks for dashboard mapping
    const coord = [ (Math.random() * 360) - 180, (Math.random() * 140) - 70 ];
    const location = "Unknown Region";
    
    return {
        id:           _id++,
        time:         now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        src:          `${randIP()}:${randPort()}`,
        dst:          `${randIP()}:${isVpn ? 443 : 80}`,
        flowType:     pick(FLOW_TYPES),
        isVpn,
        deanonymised,
        trueApp:      deanonymised ? pick(TRUE_APPS) : null,
        confidence,
        action,
        coord,
        location,
        type: isVpn ? 'VPN Node' : 'Direct Route'
    };
};

/* ─── Provider ────────────────────────────────────────────────── */
export const DashboardDataProvider = ({ children }) => {
    const [logs,      setLogs]      = useState([]);
    const [chartData, setChartData] = useState([]);
    const [metrics,   setMetrics]   = useState({ totalScanned: 18309, detectedVpn: 4606, deanonymisedFlows: 4470, highRiskBlocks: 440 });

    const synthInterval  = useRef(null);
    const wsRef          = useRef(null);
    const wsLive         = useRef(false); // true only while backend is sending messages
    const isUnmounted    = useRef(false);

    /* ── Tick function: push synthetic packets ── */
    const pushPackets = () => {
        if (isUnmounted.current) return;
        const count   = 1 + ~~(Math.random() * 3);
        const newLogs = Array.from({ length: count }, makeLog);

        setLogs(prev => [...newLogs, ...prev].slice(0, 50));

        setMetrics(prev => ({
            totalScanned:      prev.totalScanned + count,
            detectedVpn:       prev.detectedVpn + newLogs.filter(l => l.isVpn).length,
            deanonymisedFlows: prev.deanonymisedFlows + newLogs.filter(l => l.deanonymised).length,
            highRiskBlocks:    prev.highRiskBlocks + newLogs.filter(l => l.action === 'BLOCK').length,
        }));

        setChartData(prev => {
            const now   = new Date();
            const sec   = ~~(now.getSeconds() / 5) * 5;
            const pad   = s => String(s).padStart(2, '0');
            const tKey  = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(sec)}`;
            const vpnN  = newLogs.filter(l => l.isVpn).length;
            const norN  = count - vpnN;
            const copy  = [...prev];
            const last  = copy[copy.length - 1];

            if (last && last.time === tKey) {
                copy[copy.length - 1] = { time: tKey, normal: Math.min(100, last.normal + norN * 10), vpn: Math.min(100, last.vpn + vpnN * 15) };
                return copy;
            }
            const dn = last ? Math.max(15, ~~(last.normal * 0.6)) : 20;
            const dv = last ? Math.max(2, ~~(last.vpv * 0.4)) : 3;
            return [...copy.slice(1), { time: tKey, normal: Math.min(100, dn + norN * 10), vpn: Math.min(100, dv + vpnN * 15) }];
        });
    };

    const startSynthetic = () => {
        if (synthInterval.current) return; // already running
        console.log('[IDxVPN] Synthetic packet feed started');
        synthInterval.current = setInterval(pushPackets, 1200);
    };

    const stopSynthetic = () => {
        if (synthInterval.current) { clearInterval(synthInterval.current); synthInterval.current = null; }
    };

    /* ── Initialise chart baseline ── */
    useEffect(() => {
        const initial = [];
        const now = new Date();
        now.setSeconds(~~(now.getSeconds() / 5) * 5);
        for (let i = 19; i >= 0; i--) {
            const t = new Date(now - i * 5000);
            initial.push({
                time:   t.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                normal: 20 + ~~(Math.random() * 20),
                vpn:    1  + ~~(Math.random() * 4),
            });
        }
        setChartData(initial);
    }, []);

    /* ── WebSocket + synthetic fallback ── */
    useEffect(() => {
        isUnmounted.current = false;

        const tryWs = () => {
            if (isUnmounted.current) return;
            if (wsRef.current && wsRef.current.readyState < 2) {
                wsRef.current.close();
            }

            const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host  = import.meta.env.VITE_API_BASE_URL
                ? import.meta.env.VITE_API_BASE_URL.replace(/^https?:/, proto)
                : `${proto}//${window.location.host}`;

            let ws;
            try { ws = new WebSocket(`${host}/ws/logs`); } catch { startSynthetic(); return; }

            // If still "CONNECTING" after 1500ms → assume no backend, start synthetic
            const connectTimeout = setTimeout(() => {
                if (ws.readyState !== WebSocket.OPEN) {
                    console.log('[IDxVPN] WS connect timeout — starting synthetic feed');
                    ws.close();
                    startSynthetic();
                }
            }, 1500);

            ws.onopen = () => {
                clearTimeout(connectTimeout);
                wsLive.current = true;
                console.log('[IDxVPN] WebSocket connected — real data mode');
                stopSynthetic();
            };

            ws.onmessage = (event) => {
                wsLive.current = true;
                const log = JSON.parse(event.data);
                setLogs(prev => [log, ...prev].slice(0, 50));
                setMetrics(prev => ({
                    totalScanned:      prev.totalScanned + 1,
                    detectedVpn:       prev.detectedVpn + (log.isVpn ? 1 : 0),
                    deanonymisedFlows: prev.deanonymisedFlows + (log.deanonymised ? 1 : 0),
                    highRiskBlocks:    prev.highRiskBlocks + (log.action === 'BLOCK' ? 1 : 0),
                }));
                // chart update
                setChartData(prev => {
                    const tp  = log.time.split(':');
                    const rs  = ~~(parseInt(tp[2]) / 5) * 5;
                    const cs  = rs < 10 ? `0${rs}` : rs;
                    const nT  = `${tp[0]}:${tp[1]}:${cs}`;
                    const copy = [...prev];
                    const last = copy[copy.length - 1];
                    if (last && last.time === nT) {
                        copy[copy.length - 1] = { time: nT, normal: log.isVpn ? last.normal : Math.min(100, last.normal + 10), vpn: log.isVpn ? Math.min(100, last.vpn + 15) : last.vpn };
                        return copy;
                    }
                    const dn = last ? Math.max(15, ~~(last.normal * 0.6)) : 15;
                    const dv = last ? Math.max(2, ~~(last.vpn * 0.4)) : 2;
                    return [...copy.slice(1), { time: nT, normal: log.isVpn ? dn : Math.min(100, dn + 10), vpn: log.isVpn ? Math.min(100, dv + 15) : dv }];
                });
            };

            ws.onerror = () => {
                clearTimeout(connectTimeout);
                if (!isUnmounted.current) startSynthetic();
            };

            ws.onclose = () => {
                clearTimeout(connectTimeout);
                wsLive.current = false;
                if (!isUnmounted.current) {
                    startSynthetic();              // immediately fill with synthetic data
                    setTimeout(tryWs, 8000);       // quietly retry backend every 8s
                }
            };

            wsRef.current = ws;
        };

        tryWs();

        return () => {
            isUnmounted.current = true;
            stopSynthetic();
            if (wsRef.current) wsRef.current.close();
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <DashboardDataContext.Provider value={{ logs, chartData, metrics }}>
            {children}
        </DashboardDataContext.Provider>
    );
};

export const useDashboardData = () => useContext(DashboardDataContext);
