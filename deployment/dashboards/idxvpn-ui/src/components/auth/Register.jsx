import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, User, Mail, Lock, CheckCircle2, AlertTriangle, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import shieldLogo from '../../assets/idxvpn-shield-logo.png';

const ROLES = [
    { value: 'viewer', label: 'Viewer', desc: 'Real-time monitoring of VPN detection, analytics dashboards, and traffic intelligence insights.' },
    { value: 'admin',  label: 'Admin',  desc: 'Full control over ML pipeline, policy engine, risk scoring configuration, and detection rules.' },
];

const strength = (pwd) => {
    let score = 0;
    if (pwd.length >= 8)           score++;
    if (/[A-Z]/.test(pwd))         score++;
    if (/[0-9]/.test(pwd))         score++;
    if (/[^A-Za-z0-9]/.test(pwd))  score++;
    return score; // 0-4
};

const strengthLabel = [
    { label: '',        color: 'transparent' },
    { label: 'Weak',    color: 'var(--accent-red)' },
    { label: 'Fair',    color: 'var(--accent-orange)' },
    { label: 'Good',    color: 'hsl(55,90%,50%)' },
    { label: 'Strong',  color: 'var(--accent-green)' },
];

const Register = () => {
    const navigate  = useNavigate();
    const { register } = useAuth();

    const [form, setForm] = useState({ fullName: '', email: '', username: '', password: '', confirm: '', role: 'viewer' });
    const [showPass, setShowPass]     = useState(false);
    const [showConf, setShowConf]     = useState(false);
    const [error, setError]           = useState('');
    const [success, setSuccess]       = useState(false);
    const [isLoading, setIsLoading]   = useState(false);

    const pwdStrength = strength(form.password);
    const bar = strengthLabel[pwdStrength];

    const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!form.fullName.trim()) return setError('Full name is required.');
        if (!form.username.trim()) return setError('Username is required.');
        if (form.username.trim().length < 3) return setError('Username must be at least 3 characters.');
        if (form.password.length < 6) return setError('Password must be at least 6 characters.');
        if (form.password !== form.confirm) return setError('Passwords do not match.');

        setIsLoading(true);
        const result = await register({ ...form });
        setIsLoading(false);

        if (result.success) {
            setSuccess(true);
            setTimeout(() => navigate('/login'), 2500);
        } else {
            setError(result.message || 'Registration failed. Please try again.');
        }
    };

    const inputStyle = {
        background: 'var(--bg-input)',
        border: '1px solid var(--border)',
        color: 'var(--text-primary)',
    };

    const focusIn  = e => e.target.style.borderColor = 'var(--border-focus)';
    const focusOut = e => e.target.style.borderColor = 'var(--border)';

    /* ── Success State ── */
    if (success) return (
        <div
            className="min-h-screen flex items-center justify-center p-6"
            style={{ backgroundColor: 'var(--bg-base)' }}
        >
            <div
                className="w-full max-w-sm rounded-2xl p-10 text-center animate-fade-in-up"
                style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', boxShadow: 'var(--shadow-card)' }}
            >
                <div
                    className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                    style={{ background: 'hsla(152,70%,45%,0.15)', border: '1px solid hsla(152,70%,45%,0.30)' }}
                >
                    <CheckCircle2 size={32} style={{ color: 'var(--accent-green)' }} />
                </div>
                <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Account Created!</h2>
                <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                    Your <strong>{form.role}</strong> account for <code style={{ color: 'var(--accent-blue)' }}>{form.username}</code> has been registered.
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Redirecting to sign in…</p>
            </div>
        </div>
    );

    return (
        <div
            className="min-h-screen flex"
            style={{ backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}
        >
            {/* ── LEFT PANEL ── */}
            <div
                className="hidden lg:flex flex-col justify-between w-[44%] relative overflow-hidden p-12"
                style={{
                    background: 'linear-gradient(135deg, hsl(222,60%,10%) 0%, hsl(215,80%,14%) 50%, hsl(260,50%,12%) 100%)',
                    borderRight: '1px solid var(--border)',
                }}
            >
                {/* Grid bg */}
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
                {/* Glow */}
                <div
                    className="absolute top-1/3 left-1/3 w-72 h-72 rounded-full animate-pulse-glow pointer-events-none"
                    style={{ background: 'radial-gradient(circle, hsla(260,80%,65%,0.18) 0%, transparent 70%)' }}
                />
                {/* Scan line */}
                <div
                    className="scan-line absolute left-0 right-0 h-[2px] pointer-events-none"
                    style={{ background: 'linear-gradient(90deg, transparent, var(--accent-purple), transparent)' }}
                />

                {/* Logo */}
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

                {/* Copy */}
                <div className="relative z-10 space-y-6 animate-fade-in-up delay-100">
                    <div>
                        {/* IDxVPN heading */}
                        <h1 className="text-5xl font-black leading-tight mb-3"
                            style={{
                                background: 'linear-gradient(135deg, #ffffff 40%, var(--accent-blue) 100%)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                            }}
                        >
                            IDxVPN
                        </h1>

                        {/* Project subtitle */}
                        <h2 className="text-xl font-bold text-white mb-4 leading-snug">
                            Multi-Layer VPN Detection &amp; Deanonymisation Platform
                        </h2>

                        {/* Description */}
                        <p style={{ color: 'hsl(215,20%,72%)', lineHeight: 1.75 }} className="text-base max-w-sm mb-5">
                            Monitor real-time VPN traffic, detect encrypted flows,
                            and analyze behavioral deanonymisation using our
                            multi-layer Machine learning system.
                        </p>

                        {/* Badges */}
                        <div className="flex flex-wrap gap-2">
                            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ background: 'hsla(215,100%,62%,0.15)', color: 'var(--accent-blue)', border: '1px solid hsla(215,100%,62%,0.25)' }}>
                                <div className="w-1.5 h-1.5 rounded-full bg-current" /> Real-Time Packet Analysis
                            </span>
                            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ background: 'hsla(260,80%,65%,0.15)', color: 'var(--accent-purple)', border: '1px solid hsla(260,80%,65%,0.25)' }}>
                                <div className="w-1.5 h-1.5 rounded-full bg-current" /> Multi-Stage ML Detection
                            </span>
                            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ background: 'hsla(152,70%,45%,0.15)', color: 'var(--accent-green)', border: '1px solid hsla(152,70%,45%,0.25)' }}>
                                <div className="w-1.5 h-1.5 rounded-full bg-current" /> Risk-Based Policy Engine
                            </span>
                        </div>
                    </div>

                    {/* Role cards */}
                    <div className="space-y-3 animate-fade-in-up delay-200">
                        {ROLES.map(r => (
                            <div
                                key={r.value}
                                className="flex items-start gap-3 px-4 py-3 rounded-xl"
                                style={{ background: 'hsla(220,30%,100%,0.06)', border: '1px solid hsla(220,30%,100%,0.10)' }}
                            >
                                <div
                                    className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                                    style={{ background: r.value === 'admin' ? 'hsla(260,80%,65%,0.2)' : 'hsla(215,100%,62%,0.2)' }}
                                >
                                    {r.value === 'admin'
                                        ? <Shield size={13} style={{ color: 'var(--accent-purple)' }} />
                                        : <User   size={13} style={{ color: 'var(--accent-blue)' }} />}
                                </div>
                                <div>
                                    <div className="text-sm font-semibold text-white">{r.label} Role</div>
                                    <div className="text-xs mt-0.5" style={{ color: 'hsl(215,18%,60%)' }}>{r.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer */}
                <div className="relative z-10 animate-fade-in-up delay-300">
                    <span className="text-xs" style={{ color: 'hsl(215,16%,50%)' }}>
                        AI-Driven VPN Detection & Deanonymisation System
                    </span>
                </div>
            </div>

            {/* ── RIGHT PANEL — Register Form ── */}
            <div
                className="flex-1 flex flex-col items-center justify-center p-6 overflow-y-auto relative"
                style={{ backgroundColor: 'var(--bg-base)' }}
            >
                {/* BG glow */}
                <div
                    className="absolute top-0 right-0 w-96 h-96 rounded-full pointer-events-none animate-pulse-glow"
                    style={{ background: 'radial-gradient(circle, hsla(260,80%,65%,0.08) 0%, transparent 70%)', transform: 'translate(30%,-30%)' }}
                />

                <div className="w-full max-w-md relative z-10">

                    {/* Back link */}
                    <Link
                        to="/login"
                        className="inline-flex items-center gap-1.5 text-sm mb-6 transition-colors"
                        style={{ color: 'var(--text-muted)' }}
                        onMouseEnter={e => e.currentTarget.style.color = 'var(--accent-blue)'}
                        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
                    >
                        <ArrowLeft size={14} /> Back to Sign In
                    </Link>

                    {/* Mobile logo */}
                    <div className="lg:hidden flex items-center gap-3 mb-6 animate-fade-in-up">
                        <div
                            className="w-9 h-9 rounded-xl overflow-hidden shrink-0"
                            style={{ boxShadow: '0 0 14px hsla(210,100%,60%,0.45)', border: '1.5px solid hsla(210,100%,60%,0.3)' }}
                        >
                            <img src={shieldLogo} alt="IDxVPN" className="w-full h-full object-cover" style={{ objectPosition: '50% 38%', transform: 'scale(1.35)' }} />
                        </div>
                        <div>
                            <div className="font-bold text-base" style={{ color: 'var(--text-primary)' }}>IDxVPN</div>
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
                        <div className="mb-7">
                            <h2 className="text-2xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>Create account</h2>
                            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                Register for access to the IDxVPN monitoring platform
                            </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* Full name */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }} htmlFor="reg-fullname">
                                    Full Name
                                </label>
                                <input
                                    id="reg-fullname"
                                    type="text"
                                    value={form.fullName}
                                    onChange={set('fullName')}
                                    placeholder="e.g. Mohd Hassan"
                                    required
                                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all duration-200"
                                    style={inputStyle}
                                    onFocus={focusIn} onBlur={focusOut}
                                />
                            </div>

                            {/* Email */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }} htmlFor="reg-email">
                                    Email <span style={{ color: 'var(--text-muted)' }}>(optional)</span>
                                </label>
                                <input
                                    id="reg-email"
                                    type="email"
                                    value={form.email}
                                    onChange={set('email')}
                                    placeholder="you@example.com"
                                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all duration-200"
                                    style={inputStyle}
                                    onFocus={focusIn} onBlur={focusOut}
                                />
                            </div>

                            {/* Username */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }} htmlFor="reg-username">
                                    Username
                                </label>
                                <input
                                    id="reg-username"
                                    type="text"
                                    value={form.username}
                                    onChange={set('username')}
                                    placeholder="Choose a username"
                                    required
                                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all duration-200"
                                    style={inputStyle}
                                    onFocus={focusIn} onBlur={focusOut}
                                />
                            </div>

                            {/* Password */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }} htmlFor="reg-password">
                                    Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="reg-password"
                                        type={showPass ? 'text' : 'password'}
                                        value={form.password}
                                        onChange={set('password')}
                                        placeholder="••••••••"
                                        required
                                        className="w-full px-4 py-2.5 pr-11 rounded-xl text-sm outline-none transition-all duration-200"
                                        style={inputStyle}
                                        onFocus={focusIn} onBlur={focusOut}
                                    />
                                    <button type="button" onClick={() => setShowPass(v => !v)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md"
                                        style={{ color: 'var(--text-muted)' }} aria-label="Toggle password">
                                        {showPass ? <EyeOff size={15}/> : <Eye size={15}/>}
                                    </button>
                                </div>
                                {/* Strength bar */}
                                {form.password && (
                                    <div className="mt-2 space-y-1">
                                        <div className="flex gap-1">
                                            {[1,2,3,4].map(i => (
                                                <div key={i} className="h-1 flex-1 rounded-full transition-all duration-300"
                                                    style={{ background: i <= pwdStrength ? bar.color : 'var(--border)' }} />
                                            ))}
                                        </div>
                                        <span className="text-xs" style={{ color: bar.color }}>{bar.label}</span>
                                    </div>
                                )}
                            </div>

                            {/* Confirm password */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }} htmlFor="reg-confirm">
                                    Confirm Password
                                </label>
                                <div className="relative">
                                    <input
                                        id="reg-confirm"
                                        type={showConf ? 'text' : 'password'}
                                        value={form.confirm}
                                        onChange={set('confirm')}
                                        placeholder="••••••••"
                                        required
                                        className="w-full px-4 py-2.5 pr-11 rounded-xl text-sm outline-none transition-all duration-200"
                                        style={{
                                            ...inputStyle,
                                            borderColor: form.confirm && form.confirm !== form.password
                                                ? 'hsla(350,75%,55%,0.6)'
                                                : form.confirm && form.confirm === form.password
                                                    ? 'hsla(152,70%,45%,0.6)'
                                                    : 'var(--border)',
                                        }}
                                        onFocus={focusIn}
                                        onBlur={e => e.target.style.borderColor = form.confirm && form.confirm !== form.password ? 'hsla(350,75%,55%,0.6)' : form.confirm === form.password ? 'hsla(152,70%,45%,0.6)' : 'var(--border)'}
                                    />
                                    <button type="button" onClick={() => setShowConf(v => !v)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md"
                                        style={{ color: 'var(--text-muted)' }} aria-label="Toggle confirm password">
                                        {showConf ? <EyeOff size={15}/> : <Eye size={15}/>}
                                    </button>
                                </div>
                            </div>

                            {/* Role selector */}
                            <div>
                                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>
                                    Access Role
                                </label>
                                <div className="grid grid-cols-2 gap-2">
                                    {ROLES.map(r => (
                                        <button
                                            key={r.value}
                                            type="button"
                                            onClick={() => setForm(f => ({ ...f, role: r.value }))}
                                            className="px-4 py-2.5 rounded-xl text-sm font-medium text-left transition-all duration-200"
                                            style={{
                                                background: form.role === r.value ? 'hsla(215,100%,62%,0.14)' : 'var(--bg-input)',
                                                border: `1px solid ${form.role === r.value ? 'var(--accent-blue)' : 'var(--border)'}`,
                                                color: form.role === r.value ? 'var(--accent-blue)' : 'var(--text-secondary)',
                                            }}
                                        >
                                            {r.label}
                                        </button>
                                    ))}
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
                                        : 'linear-gradient(135deg, var(--accent-purple), var(--accent-blue))',
                                    boxShadow: isLoading ? 'none' : '0 4px 20px var(--accent-blue-glow)',
                                    cursor: isLoading ? 'not-allowed' : 'pointer',
                                }}
                            >
                                {isLoading
                                    ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/> Creating account…</>
                                    : 'Create Account'}
                            </button>
                        </form>

                        <p className="text-sm text-center mt-5" style={{ color: 'var(--text-muted)' }}>
                            Already have an account?{' '}
                            <Link
                                to="/login"
                                className="font-semibold transition-colors"
                                style={{ color: 'var(--accent-blue)' }}
                                onMouseEnter={e => e.currentTarget.style.textDecoration = 'underline'}
                                onMouseLeave={e => e.currentTarget.style.textDecoration = 'none'}
                            >
                                Sign in
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Register;
