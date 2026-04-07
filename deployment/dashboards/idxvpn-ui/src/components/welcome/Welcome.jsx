import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BarChart2 } from 'lucide-react';
import shieldLogo from '../../assets/idxvpn-shield-logo.png';

const Welcome = () => {
    const navigate = useNavigate();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        // Slight delay so CSS transitions fire
        const t = setTimeout(() => setMounted(true), 60);
        return () => clearTimeout(t);
    }, []);

    /* Subtle floating particles around the page */
    const particles = React.useMemo(() => {
        return Array.from({ length: 36 }, (_, i) => {
            const angle  = (i / 36) * Math.PI * 2;
            const radius = 300 + (i % 5) * 60;
            const colors = ['#4f8fff', '#a855f7', '#1bc553', '#ff9900'];
            return {
                x:     Math.cos(angle) * radius,
                y:     Math.sin(angle) * radius,
                color: colors[i % colors.length],
                size:  2 + (i % 3),
                delay: `${(i * 40) % 500}ms`,
            };
        });
    }, []);

    return (
        <div
            className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden"
            style={{ backgroundColor: 'var(--bg-base)' }}
        >
            {/* ── Ambient glow ── */}
            <div
                className="absolute rounded-full blur-[120px] pointer-events-none"
                style={{
                    width: 700, height: 700,
                    top: '50%', left: '50%',
                    transform: 'translate(-50%, -50%)',
                    background: 'radial-gradient(circle, hsla(210,100%,60%,0.15) 0%, transparent 65%)',
                    opacity: mounted ? 1 : 0,
                    transition: 'opacity 1.4s ease',
                }}
            />
            {/* Secondary purple glow */}
            <div
                className="absolute rounded-full blur-[80px] pointer-events-none"
                style={{
                    width: 400, height: 300,
                    top: '30%', left: '60%',
                    background: 'radial-gradient(circle, hsla(280,100%,60%,0.10) 0%, transparent 70%)',
                    opacity: mounted ? 1 : 0,
                    transition: 'opacity 1.6s ease',
                }}
            />

            {/* ── Particles ── */}
            {particles.map((p, i) => (
                <div
                    key={i}
                    className="absolute rounded-full pointer-events-none"
                    style={{
                        left: `calc(50% + ${p.x}px)`,
                        top:  `calc(50% + ${p.y}px)`,
                        width: p.size, height: p.size,
                        backgroundColor: p.color,
                        opacity: mounted ? 0.55 : 0,
                        transform: mounted ? 'scale(1)' : 'scale(0)',
                        transition: `opacity 1.2s ${p.delay}, transform 1.2s ${p.delay}`,
                    }}
                />
            ))}

            {/* ── Main content ── */}
            <div className="relative z-10 flex flex-col items-center text-center max-w-3xl px-6 gap-0">

                {/* ── Navbar row: logo + IDxVPN + Welcome ── */}
                <div
                    className="flex items-center gap-3 mb-12"
                    style={{
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(-20px)',
                        transition: 'all 0.8s cubic-bezier(0.4,0,0.2,1) 80ms',
                    }}
                >
                    {/* Shield logo badge */}
                    <div
                        className="w-11 h-11 rounded-xl overflow-hidden shrink-0"
                        style={{
                            boxShadow: '0 0 18px hsla(210,100%,60%,0.5)',
                            border: '1.5px solid hsla(210,100%,60%,0.35)',
                        }}
                    >
                        <img
                            src={shieldLogo}
                            alt="IDxVPN Shield"
                            className="w-full h-full object-cover"
                            style={{ objectPosition: '50% 38%', transform: 'scale(1.35)' }}
                        />
                    </div>
                    <span className="text-xl font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>IDxVPN</span>
                    <span
                        className="text-sm font-medium px-2.5 py-0.5 rounded-full"
                        style={{ background: 'var(--bg-surface)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
                    >
                        Welcome
                    </span>
                </div>

                {/* ── "Welcome to" label ── */}
                <p
                    className="text-sm font-semibold uppercase tracking-[0.25em] mb-3"
                    style={{
                        color: 'var(--accent-blue)',
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(20px)',
                        transition: 'all 0.8s cubic-bezier(0.4,0,0.2,1) 160ms',
                    }}
                >
                    Welcome to
                </p>

                {/* ── IDxVPN giant title ── */}
                <h1
                    className="font-black leading-none tracking-tight mb-4"
                    style={{
                        fontSize: 'clamp(3.5rem, 10vw, 7rem)',
                        background: 'linear-gradient(135deg, var(--text-primary) 40%, var(--accent-blue) 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(24px)',
                        transition: 'all 0.9s cubic-bezier(0.4,0,0.2,1) 220ms',
                    }}
                >
                    IDxVPN
                </h1>

                {/* ── Subtitle line 1 ── */}
                <h2
                    className="text-2xl md:text-3xl font-bold mb-2"
                    style={{
                        color: 'var(--text-primary)',
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(20px)',
                        transition: 'all 0.9s cubic-bezier(0.4,0,0.2,1) 280ms',
                    }}
                >
                    Multi-Layer System for VPN Detection &amp; Deanonymisation
                </h2>

                {/* ── "Using Machine Learning" gradient ── */}
                <p
                    className="text-2xl md:text-3xl font-extrabold mb-8"
                    style={{
                        background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(20px)',
                        transition: 'all 0.9s cubic-bezier(0.4,0,0.2,1) 330ms',
                    }}
                >
                    Using Machine Learning
                </p>

                {/* ── Divider ── */}
                <div
                    className="w-16 h-px mb-8"
                    style={{ background: 'var(--border)', opacity: mounted ? 1 : 0, transition: 'opacity 1s 400ms' }}
                />

                {/* ── Section heading ── */}
                <h3
                    className="text-base font-semibold mb-3"
                    style={{
                        color: 'var(--accent-blue)',
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(16px)',
                        transition: 'all 0.9s cubic-bezier(0.4,0,0.2,1) 400ms',
                    }}
                >
                    Real-Time Network Traffic Intelligence
                </h3>

                {/* ── Body description ── */}
                <p
                    className="text-base md:text-lg max-w-2xl mb-12 leading-relaxed"
                    style={{
                        color: 'var(--text-secondary)',
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(16px)',
                        transition: 'all 0.9s cubic-bezier(0.4,0,0.2,1) 460ms',
                    }}
                >
                    Seamlessly capture, classify, and analyze encrypted network flows using a multi-stage ML pipeline
                    for VPN detection and behavioral deanonymisation.
                </p>

                {/* ── CTA Buttons ── */}
                <div
                    className="flex flex-wrap items-center justify-center gap-4"
                    style={{
                        opacity:   mounted ? 1 : 0,
                        transform: mounted ? 'translateY(0)' : 'translateY(16px)',
                        transition: 'all 0.9s cubic-bezier(0.4,0,0.2,1) 540ms',
                    }}
                >
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="group flex items-center gap-2 px-8 py-3.5 rounded-full font-semibold text-sm transition-all duration-300 hover:scale-105 active:scale-95"
                        style={{
                            background: 'var(--text-primary)',
                            color: 'var(--bg-base)',
                            boxShadow: '0 4px 24px hsla(210,100%,60%,0.25)',
                        }}
                        onMouseEnter={e => e.currentTarget.style.boxShadow = '0 6px 32px hsla(210,100%,60%,0.45)'}
                        onMouseLeave={e => e.currentTarget.style.boxShadow = '0 4px 24px hsla(210,100%,60%,0.25)'}
                    >
                        Dashboard
                        <ArrowRight size={16} className="transition-transform duration-200 group-hover:translate-x-1" />
                    </button>

                    <button
                        onClick={() => navigate('/dashboard')}
                        className="flex items-center gap-2 px-8 py-3.5 rounded-full font-semibold text-sm transition-all duration-300 hover:scale-105 active:scale-95"
                        style={{
                            background: 'var(--bg-surface)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border)',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent-blue)'; e.currentTarget.style.color = 'var(--accent-blue)'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                    >
                        <BarChart2 size={15} />
                        Explore Analytics
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Welcome;
