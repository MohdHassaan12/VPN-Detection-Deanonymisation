import { useState, useEffect } from 'react';

export const useDashboardData = () => {
    const [logs, setLogs] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [metrics, setMetrics] = useState({
        totalScanned: 0,
        detectedVpn: 0,
        deanonymisedFlows: 0,
        highRiskBlocks: 0,
    });

    useEffect(() => {
        // Initialize chart data with last 10 seconds empty
        const initialChart = [];
        const now = new Date();
        for (let i = 19; i >= 0; i--) {
            const t = new Date(now.getTime() - i * 1000);
            initialChart.push({
                time: t.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                normal: 0,
                vpn: 0
            });
        }
        setChartData(initialChart);

        const connectWebSocket = () => {
            // Dynamically derive WS URL so it works in dev (localhost:8080) and prod (same-origin via Nginx /ws/)
            const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = import.meta.env.VITE_API_BASE_URL
                ? import.meta.env.VITE_API_BASE_URL.replace(/^https?:/, wsProto)
                : `${wsProto}//${window.location.host}`;
            const ws = new WebSocket(`${wsHost}/ws/logs`);

            ws.onopen = () => {
                console.log("Connected to VPN logs stream");
            };

            ws.onmessage = (event) => {
                const newLog = JSON.parse(event.data);

                // Update Logs
                setLogs(prev => [newLog, ...prev].slice(0, 15));

                // Update Metrics
                setMetrics(prev => ({
                    totalScanned: prev.totalScanned + 1,
                    detectedVpn: prev.detectedVpn + (newLog.isVpn ? 1 : 0),
                    deanonymisedFlows: prev.deanonymisedFlows + (newLog.deanonymised ? 1 : 0),
                    highRiskBlocks: prev.highRiskBlocks + (newLog.action === 'BLOCK' ? 1 : 0),
                }));

                // Update Chart
                setChartData(prev => {
                    const newTime = newLog.time;
                    const last = prev[prev.length - 1];

                    if (last.time === newTime) {
                        const updated = [...prev];
                        updated[updated.length - 1] = {
                            time: newTime,
                            normal: newLog.isVpn ? last.normal : last.normal + 1,
                            vpn: newLog.isVpn ? last.vpn + 1 : last.vpn
                        };
                        return updated;
                    } else {
                        const newDataPoint = {
                            time: newTime,
                            normal: newLog.isVpn ? 0 : 1,
                            vpn: newLog.isVpn ? 1 : 0
                        };
                        return [...prev.slice(1), newDataPoint];
                    }
                });
            };

            ws.onerror = (error) => {
                console.error("WebSocket Error: ", error);
            };

            ws.onclose = () => {
                console.log("WebSocket disconnected. Reconnecting in 3s...");
                setTimeout(connectWebSocket, 3000);
            };

            return ws;
        };

        const ws = connectWebSocket();

        return () => {
            ws.onclose = null; // Prevent reconnect loop on unmount
            ws.close();
        };
    }, []);

    return { logs, chartData, metrics };
};
