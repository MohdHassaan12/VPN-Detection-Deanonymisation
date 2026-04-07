import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Activity } from 'lucide-react';
import shieldLogo from '../../assets/idxvpn-shield-logo.png';

const Welcome = () => {
    const navigate = useNavigate();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        const t = setTimeout(() => setMounted(true), 60);
        return () => clearTimeout(t);
    }, []);

    const particles = useMemo(() =>
        Array.from({ length: 36 }, (_, i) => {
            const angle  = (i / 36) * Math.PI * 2;
            const radius = 280 + (i % 5) * 70;
            const colors = ['#4f8fff', '#a855f7', '#1bc553', '#ff9900'];
            return {
                x: Math.cos(angle) * radius,
                y: Math.sin(angle) * radius,
                color: colors[i % colors.length],
                size: 2 + (i % 3),
                delay: `${(i * 40) % 600}ms`,
            };
        }), []);

    const fade = (delay = '0ms') => ({
        opacity:   mounted ? 1 : 0,
        transform: mounted ? 'translateY(0)' : 'translateY(22px)',
        transition: `opacity 0.9s ease ${delay}, transform 0.9s cubic-bezier(0.4,0,0.2,1) ${delay}`,
    });

    return (
        <div
            className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden"
            style={{ backgroundColor: 'var(--bg-base)' }}
        >
            {/* ── Ambient glows ── */}
            <div className="absolute rounded-full blur-[130px] pointer-events-none" style={{
                width: 750, height: 750,
                top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                background: 'radial-gradient(circle, hsla(210,100%,60%,0.14) 0%, transparent 65%)',
                opacity: mounted ? 1 : 0, transition: 'opacity 1.5s ease',
            }} />
            <div className="absolute rounded-full blur-[90px] pointer-events-none" style={{
                width: 420, height: 320,
                top: '28%', left: '62%',
                background: 'radial-gradient(circle, hsla(280,100%,60%,0.09) 0%, transparent 70%)',
                opacity: mounted ? 1 : 0, transition: 'opacity 1.8s ease',
            }} />

            {/* ── Particles ── */}
            {particles.map((p, i) => (
                <div key={i} className="absolute rounded-full pointer-events-none" style={{
                    left: `calc(50% + ${p.x}px)`, top: `calc(50% + ${p.y}px)`,
                    width: p.size, height: p.size,
                    backgroundColor: p.color,
                    opacity: mounted ? 0.5 : 0,
                    transform: mounted ? 'scale(1)' : 'scale(0)',
                    transition: `opacity 1.3s ${p.delay}, transform 1.3s ${p.delay}`,
                }} />
            ))}

            {/* ── Content ── */}
            <div className="relative z-10 flex flex-col items-center text-center max-w-4xl px-6">

                {/* ── Top bar: shield logo + IDxVPN (small, clean) ── */}
                <div
                    className="flex items-center gap-2.5 mb-14"
                    style={{
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(-18px)',
                        transition: 'all 0.8s cubic-bezier(0.4,0,0.2,1) 60ms',
                    }}
                >
                    <div
                        className="w-9 h-9 rounded-xl overflow-hidden shrink-0"
                        style={{
                            boxShadow: '0 0 14px hsla(210,100%,60%,0.45)',
                            border: '1.5px solid hsla(210,100%,60%,0.3)',
                        }}
                    >
                        <img
                            src={shieldLogo}
                            alt="IDxVPN Shield Logo"
                            className="w-full h-full object-cover"
                            style={{ objectPosition: '50% 38%', transform: 'scale(1.35)' }}
                        />
                    </div>
                    <span className="text-base font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
                        IDxVPN
                    </span>
                </div>

                {/* ── "Welcome to" micro label ── */}
                <p
                    className="text-xs font-semibold uppercase tracking-[0.3em] mb-4"
                    style={{ color: 'var(--accent-blue)', ...fade('140ms') }}
                >
                    Welcome to
                </p>

                {/* ── IDxVPN — rendered small/compact, not the hero ── */}
                <p
                    className="text-2xl font-bold mb-5 tracking-wide"
                    style={{ color: 'var(--text-secondary)', ...fade('190ms') }}
                >
                    IDxVPN
                </p>

                {/* ── PROJECT NAME — the real hero headline ── */}
                <h1
                    className="font-black leading-tight tracking-tight mb-3"
                    style={{
                        fontSize: 'clamp(2.6rem, 7vw, 5.5rem)',
                        color: 'var(--text-primary)',
                        ...fade('250ms'),
                    }}
                >
                    Multi-Layer System for VPN Detection
                    <br />
                    &amp; Deanonymisation
                </h1>

                {/* ── "Using Machine Learning" gradient accent ── */}
                <p
                    className="font-extrabold mb-10"
                    style={{
                        fontSize: 'clamp(1.6rem, 4vw, 3rem)',
                        background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        ...fade('310ms'),
                    }}
                >
                    Using Machine Learning
                </p>

                {/* ── Divider ── */}
                <div
                    className="w-14 h-px mb-8"
                    style={{ background: 'var(--border)', opacity: mounted ? 1 : 0, transition: 'opacity 1s 370ms' }}
                />

                {/* ── Body subtitle ── */}
                <h2
                    className="text-sm font-semibold mb-3 uppercase tracking-widest"
                    style={{ color: 'var(--accent-blue)', ...fade('390ms') }}
                >
                    Real-Time Network Traffic Intelligence
                </h2>

                <p
                    className="text-base md:text-lg leading-relaxed max-w-2xl mb-12"
                    style={{ color: 'var(--text-secondary)', ...fade('440ms') }}
                >
                    Seamlessly capture, classify, and analyze encrypted network flows using a multi-stage ML pipeline
                    for VPN detection and behavioral deanonymisation.
                </p>

                {/* ── CTA Buttons ── */}
                <div
                    className="flex flex-wrap items-center justify-center gap-4"
                    style={fade('510ms')}
                >
                    {/* Primary — Dashboard */}
                    <button
                        onClick={() => navigate('/dashboard', { state: { tab: 'dashboard' } })}
                        className="group flex items-center gap-2 px-8 py-3.5 rounded-full font-semibold text-sm transition-all duration-300 hover:scale-105 active:scale-95"
                        style={{ background: 'var(--text-primary)', color: 'var(--bg-base)', boxShadow: '0 4px 24px hsla(210,100%,60%,0.22)' }}
                        onMouseEnter={e => e.currentTarget.style.boxShadow = '0 6px 32px hsla(210,100%,60%,0.42)'}
                        onMouseLeave={e => e.currentTarget.style.boxShadow = '0 4px 24px hsla(210,100%,60%,0.22)'}
                    >
                        Dashboard
                        <ArrowRight size={16} className="transition-transform duration-200 group-hover:translate-x-1" />
                    </button>

                    {/* Secondary — Detection */}
                    <button
                        onClick={() => navigate('/dashboard', { state: { tab: 'detection' } })}
                        className="flex items-center gap-2 px-8 py-3.5 rounded-full font-semibold text-sm transition-all duration-300 hover:scale-105 active:scale-95"
                        style={{ background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border)' }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent-blue)'; e.currentTarget.style.color = 'var(--accent-blue)'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                    >
                        <Activity size={15} />
                        Detection
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Welcome;
