import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Eye, EyeOff, Wifi, Lock, AlertTriangle } from 'lucide-react';
import shieldLogo from '../../assets/idxvpn-shield-logo.png';

const Login = () => {
    const [username, setUsername]   = useState('');
    const [password, setPassword]   = useState('');
    const [showPass, setShowPass]   = useState(false);
    const [error, setError]         = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { login } = useAuth();
    const navigate  = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        const success = await login(username, password);
        if (success) {
            navigate('/welcome');
        } else {
            setError('Invalid username or password. Please try again.');
        }
        setIsLoading(false);
    };

    const quickFill = (u, p) => { setUsername(u); setPassword(p); setError(''); };

    return (
        <div
            className="min-h-screen flex"
            style={{ backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}
        >
            {/* ── LEFT PANEL — Project Identity ── */}
            <div
                className="hidden lg:flex flex-col justify-between w-[52%] relative overflow-hidden p-12"
                style={{
                    background: 'linear-gradient(135deg, hsl(222,60%,10%) 0%, hsl(215,80%,14%) 50%, hsl(260,50%,12%) 100%)',
                    borderRight: '1px solid var(--border)',
                }}
            >
                {/* Animated grid bg */}
                <div
                    className="absolute inset-0 opacity-[0.04]"
                    style={{
                        backgroundImage: `
                            linear-gradient(var(--accent-blue) 1px, transparent 1px),
                            linear-gradient(90deg, var(--accent-blue) 1px, transparent 1px)
                        `,
                        backgroundSize: '48px 48px',
                    }}
                />

                {/* Glow orbs */}
                <div
                    className="absolute top-1/4 left-1/4 w-80 h-80 rounded-full animate-pulse-glow pointer-events-none"
                    style={{ background: 'radial-gradient(circle, hsla(215,100%,62%,0.20) 0%, transparent 70%)' }}
                />
                <div
                    className="absolute bottom-1/3 right-1/4 w-64 h-64 rounded-full animate-pulse-glow pointer-events-none delay-300"
                    style={{ background: 'radial-gradient(circle, hsla(260,80%,65%,0.15) 0%, transparent 70%)' }}
                />

                {/* Scan line */}
                <div
                    className="scan-line absolute left-0 right-0 h-[2px] pointer-events-none"
                    style={{ background: 'linear-gradient(90deg, transparent, var(--accent-blue), transparent)' }}
                />

                {/* Logo + brand */}
                <div className="relative z-10 animate-fade-in-up">
                    <div className="flex items-center gap-3 mb-2">
                        <div
                            className="w-11 h-11 rounded-xl overflow-hidden shrink-0"
                            style={{ boxShadow: '0 0 18px hsla(210,100%,60%,0.55)', border: '1.5px solid hsla(210,100%,60%,0.35)' }}
                        >
                            <img src={shieldLogo} alt="IDxVPN" className="w-full h-full object-cover" style={{ objectPosition: '50% 38%', transform: 'scale(1.35)' }} />
                        </div>
                        <span className="text-white font-bold text-xl tracking-wide">IDxVPN</span>
                    </div>
                </div>

                {/* Hero content */}
                <div className="relative z-10 space-y-8">
                    <div className="animate-fade-in-up delay-100">
                        <h1 className="text-5xl font-bold leading-tight text-white mb-4">
                            VPN Detection &<br />
                            <span
                                className="text-gradient"
                                style={{ backgroundImage: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))' }}
                            >
                                Deanonymisation
                            </span>
                        </h1>
                        <p style={{ color: 'hsl(215,20%,72%)', lineHeight: 1.7 }} className="text-lg max-w-sm">
                            AI-powered, 4-layer ML pipeline for real-time VPN traffic classification,
                            intent scoring and automated gateway enforcement.
                        </p>
                    </div>

                    {/* Feature pills */}
                    <div className="flex flex-col gap-3 animate-fade-in-up delay-200">
                        {[
                            { icon: <Shield size={15}/>, label: 'Stage 1: CNN App Classifier', color: 'var(--accent-blue)' },
                            { icon: <Wifi size={15}/>,   label: 'Stage 2: RF Intent Scorer',  color: 'var(--accent-purple)' },
                            { icon: <Lock size={15}/>,   label: 'Stage 3: Policy Enforcer',   color: 'var(--accent-green)' },
                        ].map(({ icon, label, color }) => (
                            <div
                                key={label}
                                className="flex items-center gap-3 px-4 py-2.5 rounded-lg w-fit"
                                style={{
                                    background: 'hsla(220,30%,100%,0.06)',
                                    border: `1px solid hsla(220,30%,100%,0.10)`,
                                    backdropFilter: 'blur(8px)',
                                }}
                            >
                                <span style={{ color }}>{icon}</span>
                                <span className="text-sm font-medium" style={{ color: 'hsl(215,20%,82%)' }}>{label}</span>
                            </div>
                        ))}
                    </div>

                    {/* Stats row */}
                    <div className="grid grid-cols-3 gap-4 animate-fade-in-up delay-300">
                        {[
                            { val: '94.2%', lbl: 'CNN Precision' },
                            { val: '~45ms', lbl: 'Pipeline Latency' },
                            { val: '92%',  lbl: 'Deanon. Rate' },
                        ].map(({ val, lbl }) => (
                            <div key={lbl} className="text-center">
                                <div className="text-2xl font-bold text-white">{val}</div>
                                <div className="text-xs mt-0.5" style={{ color: 'hsl(215,18%,58%)' }}>{lbl}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer badge */}
                <div className="relative z-10 animate-fade-in-up delay-400">
                    <span
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
                        style={{ background: 'hsla(152,70%,45%,0.15)', border: '1px solid hsla(152,70%,45%,0.30)', color: 'hsl(152,70%,60%)' }}
                    >
                        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                        Pipeline Active — DigitalOcean Node
                    </span>
                </div>
            </div>

            {/* ── RIGHT PANEL — Sign In Form ── */}
            <div
                className="flex-1 flex flex-col items-center justify-center p-8 relative overflow-hidden"
                style={{ backgroundColor: 'var(--bg-base)' }}
            >
                {/* Subtle bg blob */}
                <div
                    className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none animate-pulse-glow"
                    style={{ background: 'radial-gradient(circle, var(--accent-blue-glow) 0%, transparent 70%)', transform: 'translate(30%, -30%)' }}
                />

                <div className="w-full max-w-md relative z-10">

                    {/* Mobile logo */}
                    <div className="lg:hidden flex items-center gap-3 mb-8 animate-fade-in-up">
                        <div
                            className="w-9 h-9 rounded-xl overflow-hidden shrink-0"
                            style={{ boxShadow: '0 0 14px hsla(210,100%,60%,0.45)', border: '1.5px solid hsla(210,100%,60%,0.3)' }}
                        >
                            <img src={shieldLogo} alt="IDxVPN" className="w-full h-full object-cover" style={{ objectPosition: '50% 38%', transform: 'scale(1.35)' }} />
                        </div>
                        <div>
                            <div className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>IDxVPN</div>
                            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>VPN Detection & Deanonymisation</div>
                        </div>
                    </div>

                    {/* Card */}
                    <div
                        className="rounded-2xl p-8 animate-fade-in-up"
                        style={{
                            background: 'var(--bg-surface)',
                            border: '1px solid var(--border)',
                            boxShadow: 'var(--shadow-card)',
                            backdropFilter: 'blur(20px)',
                        }}
                    >
                        {/* Header */}
                        <div className="mb-8">
                            <div className="flex items-center gap-2 mb-1">
                                <Shield size={18} style={{ color: 'var(--accent-blue)' }} />
                                <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--accent-blue)' }}>
                                    Secure Access
                                </span>
                            </div>
                            <h2 className="text-2xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
                                Sign in to IDxVPN
                            </h2>
                            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                Access the real-time VPN classification dashboard
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5">
                            {/* Username */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }} htmlFor="login-username">
                                    Username
                                </label>
                                <input
                                    id="login-username"
                                    type="text"
                                    value={username}
                                    onChange={e => setUsername(e.target.value)}
                                    required
                                    placeholder="Enter your username"
                                    className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all duration-200"
                                    style={{
                                        background: 'var(--bg-input)',
                                        border: '1px solid var(--border)',
                                        color: 'var(--text-primary)',
                                    }}
                                    onFocus={e => e.target.style.borderColor = 'var(--border-focus)'}
                                    onBlur={e => e.target.style.borderColor = 'var(--border)'}
                                />
                            </div>

                            {/* Password */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }} htmlFor="login-password">
                                    Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="login-password"
                                        type={showPass ? 'text' : 'password'}
                                        value={password}
                                        onChange={e => setPassword(e.target.value)}
                                        required
                                        placeholder="••••••••"
                                        className="w-full px-4 py-3 pr-11 rounded-xl text-sm outline-none transition-all duration-200"
                                        style={{
                                            background: 'var(--bg-input)',
                                            border: '1px solid var(--border)',
                                            color: 'var(--text-primary)',
                                        }}
                                        onFocus={e => e.target.style.borderColor = 'var(--border-focus)'}
                                        onBlur={e => e.target.style.borderColor = 'var(--border)'}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPass(v => !v)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md transition-colors"
                                        style={{ color: 'var(--text-muted)' }}
                                        aria-label="Toggle password visibility"
                                    >
                                        {showPass ? <EyeOff size={16}/> : <Eye size={16}/>}
                                    </button>
                                </div>
                            </div>

                            {/* Error */}
                            {error && (
                                <div
                                    className="flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm animate-fade-in"
                                    style={{ background: 'hsla(350,75%,55%,0.10)', border: '1px solid hsla(350,75%,55%,0.25)', color: 'var(--accent-red)' }}
                                >
                                    <AlertTriangle size={15} className="shrink-0" />
                                    {error}
                                </div>
                            )}

                            {/* Submit */}
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full py-3 rounded-xl font-semibold text-sm text-white transition-all duration-200 flex items-center justify-center gap-2"
                                style={{
                                    background: isLoading
                                        ? 'var(--border)'
                                        : 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
                                    boxShadow: isLoading ? 'none' : '0 4px 20px var(--accent-blue-glow)',
                                    cursor: isLoading ? 'not-allowed' : 'pointer',
                                    transform: 'scale(1)',
                                }}
                                onMouseEnter={e => !isLoading && (e.currentTarget.style.transform = 'scale(1.01)')}
                                onMouseLeave={e => (e.currentTarget.style.transform = 'scale(1)')}
                            >
                                {isLoading
                                    ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Authenticating…</>
                                    : 'Sign In'}
                            </button>
                        </form>

                        {/* Divider */}
                        <div className="flex items-center gap-3 my-6">
                            <div className="flex-1 h-px" style={{ background: 'var(--border)' }} />
                            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>or</span>
                            <div className="flex-1 h-px" style={{ background: 'var(--border)' }} />
                        </div>

                        {/* Register */}
                        <Link
                            to="/register"
                            className="w-full py-3 rounded-xl font-semibold text-sm text-center block transition-all duration-200"
                            style={{
                                background: 'var(--bg-input)',
                                border: '1px solid var(--border)',
                                color: 'var(--text-secondary)',
                            }}
                            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent-blue)'; e.currentTarget.style.color = 'var(--accent-blue)'; }}
                            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                        >
                            Create a new account
                        </Link>

                        {/* Demo credentials */}
                        <div
                            className="mt-6 p-3 rounded-xl"
                            style={{ background: 'hsla(215,100%,62%,0.07)', border: '1px dashed hsla(215,100%,62%,0.25)' }}
                        >
                            <p className="text-xs font-semibold mb-2" style={{ color: 'var(--accent-blue)' }}>
                                Demo accounts
                            </p>
                            <div className="space-y-1">
                                {[
                                    { u: 'admin',  p: 'admin123',  role: 'Admin'  },
                                    { u: 'viewer', p: 'viewer123', role: 'Viewer' },
                                ].map(({ u, p, role }) => (
                                    <button
                                        key={u}
                                        type="button"
                                        onClick={() => quickFill(u, p)}
                                        className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs transition-all duration-150"
                                        style={{ background: 'hsla(215,100%,62%,0.08)', color: 'var(--text-secondary)' }}
                                        onMouseEnter={e => e.currentTarget.style.background = 'hsla(215,100%,62%,0.16)'}
                                        onMouseLeave={e => e.currentTarget.style.background = 'hsla(215,100%,62%,0.08)'}
                                    >
                                        <span><code style={{ color: 'var(--text-primary)' }}>{u}</code> / <code>{p}</code></span>
                                        <span className="font-medium" style={{ color: 'var(--accent-blue)' }}>{role} ›</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted)' }}>
                        IDxVPN Platform · Final Year Research Project · MSc AI, University of Southampton
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Login;
