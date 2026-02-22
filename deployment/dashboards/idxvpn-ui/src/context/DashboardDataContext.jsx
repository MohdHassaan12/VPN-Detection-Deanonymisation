import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

const DashboardDataContext = createContext(null);

export const DashboardDataProvider = ({ children }) => {
    const [logs, setLogs] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [metrics, setMetrics] = useState({
        totalScanned: 0,
        detectedVpn: 0,
        deanonymisedFlows: 0,
        highRiskBlocks: 0,
    });

    // We use a ref to track if we've already initialized the base data,
    // so we don't reset it if the provider re-renders for some reason.
    const isInitialized = useRef(false);
    const wsRef = useRef(null);

    useEffect(() => {
        if (!isInitialized.current) {
            // Initialize chart data with last 10 5-second intervals
            const initialChart = [];
            const now = new Date();
            // Round down current time to nearest 5 seconds
            now.setSeconds(Math.floor(now.getSeconds() / 5) * 5);

            for (let i = 19; i >= 0; i--) {
                const t = new Date(now.getTime() - i * 5000); // 5 sec intervals
                initialChart.push({
                    time: t.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                    normal: Math.floor(Math.random() * 20 + 20), // Synthesize a baseline around 30
                    vpn: Math.floor(Math.random() * 4 + 1)
                });
            }
            setChartData(initialChart);

            // Give it some base synthetic metrics so it doesn't look like 0 usage.
            setMetrics({
                totalScanned: 18309,
                detectedVpn: 4606,
                deanonymisedFlows: 4470,
                highRiskBlocks: 440,
            });
            isInitialized.current = true;
        }

        const connectWebSocket = () => {
            if (wsRef.current?.readyState === WebSocket.OPEN) return wsRef.current;

            const ws = new WebSocket('ws://localhost:8080/ws/logs');

            ws.onopen = () => {
                console.log("Connected to VPN logs stream");
            };

            ws.onmessage = (event) => {
                const newLog = JSON.parse(event.data);

                // Update Logs
                setLogs(prev => [newLog, ...prev].slice(0, 50)); // Keep up to 50 logs in history

                // Update Metrics
                setMetrics(prev => ({
                    totalScanned: prev.totalScanned + 1,
                    detectedVpn: prev.detectedVpn + (newLog.isVpn ? 1 : 0),
                    deanonymisedFlows: prev.deanonymisedFlows + (newLog.deanonymised ? 1 : 0),
                    highRiskBlocks: prev.highRiskBlocks + (newLog.action === 'BLOCK' ? 1 : 0),
                }));

                // Update Chart
                setChartData(prev => {
                    // Normalize the incoming time string to nearest 5-second interval
                    // The time string from backend is like "14:05:27"
                    const timeParts = newLog.time.split(':');
                    const roundedSeconds = Math.floor(parseInt(timeParts[2]) / 5) * 5;
                    const cleanSeconds = roundedSeconds < 10 ? `0${roundedSeconds}` : roundedSeconds;
                    const normalizedTime = `${timeParts[0]}:${timeParts[1]}:${cleanSeconds}`;

                    const prevCopy = [...prev];
                    const last = prevCopy[prevCopy.length - 1];

                    if (last && last.time === normalizedTime) {
                        const updated = [...prevCopy];
                        // Aggregate counts in the current 5sec window
                        updated[updated.length - 1] = {
                            time: normalizedTime,
                            normal: newLog.isVpn ? last.normal : Math.min(100, last.normal + 10), // Boost for visibility, cap at 100
                            vpn: newLog.isVpn ? Math.min(100, last.vpn + 15) : last.vpn
                        };
                        return updated;
                    } else {
                        // Start a new 5-second window. Carry over a synthetic decay so it doesn't hard-drop to 0
                        const decayedNormal = last ? Math.max(15, Math.floor(last.normal * 0.6)) : 15;
                        const decayedVpn = last ? Math.max(2, Math.floor(last.vpn * 0.4)) : 2;

                        const newDataPoint = {
                            time: normalizedTime,
                            normal: newLog.isVpn ? decayedNormal : Math.min(100, decayedNormal + 10),
                            vpn: newLog.isVpn ? Math.min(100, decayedVpn + 15) : decayedVpn
                        };
                        return [...prevCopy.slice(1), newDataPoint];
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

            wsRef.current = ws;
            return ws;
        };

        const ws = connectWebSocket();

        return () => {
            // We intentionally do NOT close the WebSocket here!
            // This useEffect runs once globally because we will mount this provider high in App.jsx.
            // Leaving the socket open means data continues streaming even when not on the Dashboard view.
            // We only close if the whole browser tab is shut.
        };
    }, []);

    return (
        <DashboardDataContext.Provider value={{ logs, chartData, metrics }}>
            {children}
        </DashboardDataContext.Provider>
    );
};

export const useDashboardData = () => useContext(DashboardDataContext);
