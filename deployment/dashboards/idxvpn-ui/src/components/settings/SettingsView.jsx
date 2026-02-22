import React, { useState } from 'react';
import { Settings, Server, Shield, Database, Save, Activity, Bell } from 'lucide-react';

const SettingsView = () => {
    const [modelLoading, setModelLoading] = useState(false);
    const [saved, setSaved] = useState(false);

    const [config, setConfig] = useState({
        modelVersion: 'v1.2',
        blockSize: 64,
        threatIntel: true,
        confidenceThreshold: 85,
        slackWebhook: '',
        emailAlerts: true
    });

    const handleSave = () => {
        setModelLoading(true);
        setSaved(false);
        setTimeout(() => {
            setModelLoading(false);
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        }, 1500);
    };

    return (
        <div className="space-y-8 animate-fade-in-up">
            {/* Header Section */}
            <div className="border-b border-divider pb-6">
                <h2 className="text-2xl font-bold text-default tracking-tight flex items-center gap-3">
                    <Settings className="text-[#4f8fff]" size={28} />
                    Settings & Configuration
                </h2>
                <p className="text-muted mt-2">Adjust system parameters for inference and edge filtering.</p>
            </div>

            {/* Health Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-2xl border border-divider flex items-center justify-between">
                    <div>
                        <div className="text-muted text-sm uppercase tracking-wider mb-1 font-medium">Live Analytics Center</div>
                        <div className="text-2xl font-bold text-default flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-[#1bc553] shadow-[0_0_10px_#1bc553] animate-pulse"></span>
                            Healthy
                        </div>
                    </div>
                    <Activity size={32} className="text-[#1bc553]" />
                </div>

                <div className="glass-panel p-6 rounded-2xl border border-divider flex items-center justify-between">
                    <div>
                        <div className="text-muted text-sm uppercase tracking-wider mb-1 font-medium">Pipeline Latency</div>
                        <div className="text-2xl font-bold text-[#4f8fff] font-mono">~45ms</div>
                    </div>
                    <Activity size={32} className="text-[#4f8fff]" />
                </div>
            </div>

            {/* Configuration Form */}
            <div className="glass-panel p-8 rounded-2xl border border-divider">
                <h3 className="text-xl font-bold text-default mb-6 flex items-center gap-2">
                    <Database size={24} className="text-[#4f8fff]" />
                    ML Pipeline
                </h3>

                <div className="space-y-8">
                    {/* Model Version */}
                    <div>
                        <label className="block text-sm font-medium text-muted mb-2">Stage 1: Model Version</label>
                        <p className="text-xs text-muted mb-3">Select the active CNN model for app classification.</p>
                        <div className="relative">
                            <select
                                value={config.modelVersion}
                                onChange={(e) => setConfig({ ...config, modelVersion: e.target.value })}
                                className="w-full bg-panel border border-divider text-default rounded-xl px-4 py-3 appearance-none focus:outline-none focus:border-[#4f8fff] focus:ring-1 focus:ring-[#4f8fff] transition-all"
                            >
                                <option value="v1.2">v1.2 (Latest - DigitalOcean)</option>
                                <option value="v1.1">v1.1 (Stable - Local)</option>
                                <option value="v1.0">v1.0 (Legacy)</option>
                            </select>
                            <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none">
                                <svg className="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>
                    </div>

                    {/* Block Size */}
                    <div>
                        <label className="block text-sm font-medium text-muted mb-2">Feature Extraction Block Size</label>
                        <p className="text-xs text-muted mb-3">Number of packets to capture to generate the CNN image.</p>
                        <input
                            type="number"
                            value={config.blockSize}
                            onChange={(e) => setConfig({ ...config, blockSize: parseInt(e.target.value) })}
                            className="w-full bg-panel border border-divider text-default rounded-xl px-4 py-3 focus:outline-none focus:border-[#4f8fff] focus:ring-1 focus:ring-[#4f8fff] transition-all"
                        />
                    </div>

                    {/* Confidence Threshold */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="block text-sm font-medium text-muted">ML Confidence Threshold</label>
                            <span className="text-sm font-bold text-[#4f8fff]">{config.confidenceThreshold}%</span>
                        </div>
                        <p className="text-xs text-muted mb-3">Minimum CNN confidence required to trigger an automated policy action.</p>
                        <input
                            type="range"
                            min="50"
                            max="99"
                            value={config.confidenceThreshold}
                            onChange={(e) => setConfig({ ...config, confidenceThreshold: parseInt(e.target.value) })}
                            className="w-full h-2 bg-black/10 dark:bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#4f8fff]"
                        />
                        <div className="flex justify-between text-xs text-muted mt-2">
                            <span>More Permissive (50%)</span>
                            <span>More Strict (99%)</span>
                        </div>
                    </div>

                    <div className="h-px w-full bg-black/10 dark:bg-white/10 my-6"></div>

                    <h3 className="text-xl font-bold text-default mb-6 flex items-center gap-2">
                        <Shield size={24} className="text-[#ff9900]" />
                        Edge Filtering
                    </h3>

                    {/* Threat Intelligence Toggle */}
                    <div className="flex items-center justify-between bg-black/5 dark:bg-white/5 p-4 rounded-xl border border-divider">
                        <div>
                            <div className="font-bold text-default">IP Threat Intelligence</div>
                            <div className="text-sm text-muted mt-1">Drop packets from known bad actors before ML inference.</div>
                        </div>

                        {/* Custom Toggle Switch */}
                        <button
                            onClick={() => setConfig({ ...config, threatIntel: !config.threatIntel })}
                            className={`w-14 h-7 rounded-full transition-colors relative focus:outline-none ${config.threatIntel ? 'bg-[#4f8fff]' : 'bg-black/10 dark:bg-white/10'}`}
                        >
                            <div className={`w-5 h-5 bg-white rounded-full absolute top-1 transition-transform shadow-md ${config.threatIntel ? 'translate-x-8' : 'translate-x-1'}`}></div>
                        </button>
                    </div>

                    <div className="h-px w-full bg-black/10 dark:bg-white/10 my-6"></div>

                    <h3 className="text-xl font-bold text-default mb-6 flex items-center gap-2">
                        <Bell size={24} className="text-[#1bc553]" />
                        Alerts & Notifications
                    </h3>

                    <div className="space-y-6">
                        {/* Email Alerts Toggle */}
                        <div className="flex items-center justify-between bg-black/5 dark:bg-white/5 p-4 rounded-xl border border-divider">
                            <div>
                                <div className="font-bold text-default">Critical Email Alerts</div>
                                <div className="text-sm text-muted mt-1">Receive daily digests and high-risk policy violations.</div>
                            </div>
                            <button
                                onClick={() => setConfig({ ...config, emailAlerts: !config.emailAlerts })}
                                className={`w-14 h-7 rounded-full transition-colors relative focus:outline-none ${config.emailAlerts ? 'bg-[#4f8fff]' : 'bg-black/10 dark:bg-white/10'}`}
                            >
                                <div className={`w-5 h-5 bg-white rounded-full absolute top-1 transition-transform shadow-md ${config.emailAlerts ? 'translate-x-8' : 'translate-x-1'}`}></div>
                            </button>
                        </div>

                        {/* Slack Webhook */}
                        <div>
                            <label className="block text-sm font-medium text-muted mb-2">Slack Webhook URL</label>
                            <p className="text-xs text-muted mb-3">Push automated real-time alerts to a Slack channel.</p>
                            <input
                                type="text"
                                placeholder="https://hooks.slack.com/services/..."
                                value={config.slackWebhook}
                                onChange={(e) => setConfig({ ...config, slackWebhook: e.target.value })}
                                className="w-full bg-panel border border-divider text-default rounded-xl px-4 py-3 focus:outline-none focus:border-[#4f8fff] focus:ring-1 focus:ring-[#4f8fff] transition-all font-mono text-sm"
                            />
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="pt-6 flex items-center justify-between">
                        {saved ? (
                            <span className="text-[#1bc553] font-bold flex items-center gap-2 animate-fade-in-up">
                                <CheckCircle size={20} /> Settings Saved Successfully
                            </span>
                        ) : <span></span>}

                        <button
                            onClick={handleSave}
                            disabled={modelLoading}
                            className={`px-8 py-3 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg ${modelLoading
                                ? 'bg-black/10 dark:bg-white/10 text-muted cursor-not-allowed'
                                : 'bg-gradient-to-r from-[#4f8fff] to-[#2555ff] hover:shadow-[0_0_20px_rgba(79,143,255,0.4)] text-default hover:scale-[1.02] active:scale-[0.98]'
                                }`}
                        >
                            {modelLoading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Save size={20} />
                                    Save Changes
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Internal icon dependency for the success state component that was not imported at the top
const CheckCircle = ({ size }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>
);

export default SettingsView;
