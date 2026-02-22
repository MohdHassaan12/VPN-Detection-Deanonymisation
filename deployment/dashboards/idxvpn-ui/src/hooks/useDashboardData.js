import { useState, useEffect } from 'react';

const generateLog = (id) => {
    const isVpn = Math.random() > 0.6;
    const flowTypes = isVpn ? ['OpenVPN', 'IPSec', 'WireGuard', 'Shadowsocks'] : ['HTTPS', 'DNS', 'QUIC', 'TCP', 'UDP'];
    const apps = ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'VOIP', 'GAMING'];

    const deanonymised = isVpn ? Math.random() > 0.1 : false; // 90% deanonymisation rate
    const trueApp = isVpn && deanonymised ? apps[Math.floor(Math.random() * apps.length)] : flowTypes[Math.floor(Math.random() * flowTypes.length)];

    return {
        id,
        time: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        src: `10.0.0.${Math.floor(Math.random() * 255)}`,
        dst: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.1.${Math.floor(Math.random() * 255)}`,
        flowType: isVpn ? flowTypes[Math.floor(Math.random() * (flowTypes.length - 1))] : trueApp,
        action: isVpn ? (Math.random() > 0.4 ? 'BLOCK' : 'CHALLENGE') : 'ALLOW',
        confidence: (Math.random() * 15 + 85).toFixed(1),
        latency: Math.floor(Math.random() * 40 + 10),
        isVpn,
        deanonymised,
        trueApp
    };
};

export const useDashboardData = () => {
    const [logs, setLogs] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [metrics, setMetrics] = useState({
        totalFlows: 14250,
        deanonymisedFlows: 2891,
        detectedVpn: 843,
    });

    useEffect(() => {
        // Initialize chart data with last 10 seconds empty
        const initialChart = [];
        const now = new Date();
        for (let i = 9; i >= 0; i--) {
            const t = new Date(now.getTime() - i * 1500);
            initialChart.push({
                time: t.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                normal: Math.floor(Math.random() * 200 + 100),
                vpn: Math.floor(Math.random() * 100 + 50)
            });
        }
        setChartData(initialChart);

        // Initialize 5 mock logs
        let idCounter = 1;
        const initialLogs = Array.from({ length: 5 }).map(() => generateLog(idCounter++));
        setLogs(initialLogs);

        const interval = setInterval(() => {
            const newLog = generateLog(idCounter++);

            // Update Logs
            setLogs(prev => [newLog, ...prev].slice(0, 15));

            // Update Chart (sync with log generation)
            setChartData(prev => {
                const newTime = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

                // Let's create some dynamic variance based on the log
                const baseNormal = prev[prev.length - 1].normal;
                const baseVpn = prev[prev.length - 1].vpn;

                const nextNormal = Math.max(50, baseNormal + (Math.random() * 60 - 30));
                const nextVpn = Math.max(10, baseVpn + (Math.random() * 40 - 20) + (newLog.isVpn ? 30 : 0));

                const newDataPoint = {
                    time: newTime,
                    normal: Math.floor(nextNormal),
                    vpn: Math.floor(nextVpn)
                };
                return [...prev.slice(1), newDataPoint];
            });

            // Update Metrics
            setMetrics(prev => ({
                totalFlows: prev.totalFlows + 1,
                deanonymisedFlows: prev.deanonymisedFlows + (newLog.deanonymised ? 1 : 0),
                detectedVpn: prev.detectedVpn + (newLog.isVpn ? 1 : 0),
            }));

        }, 1500);

        return () => clearInterval(interval);
    }, []);

    return { logs, chartData, metrics };
};
