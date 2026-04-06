import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Shield } from 'lucide-react';

import logoImage from '../../assets/idxvpn-logo-white.png';

const Welcome = () => {
    const navigate = useNavigate();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    // Particle logic for the background ring effect (inspired by Antigravity)
    const renderParticles = () => {
        const particles = [];
        const numParticles = 40;
        
        for (let i = 0; i < numParticles; i++) {
            // Distribute around a partial circle
            const angle = (i / numParticles) * Math.PI * 2;
            // Radius varying for a scattered look
            const radius = 300 + Math.random() * 200;
            
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            // Assign theme colors
            const colors = ['var(--accent-blue)', 'var(--accent-purple)', 'var(--accent-green)', 'var(--accent-orange)'];
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            particles.push(
                <div
                    key={i}
                    className="absolute rounded-full"
                    style={{
                        left: `calc(50% + ${x}px)`,
                        top: `calc(50% + ${y}px)`,
                        width: `${Math.random() * 4 + 2}px`,
                        height: `${Math.random() * 4 + 2}px`,
                        backgroundColor: color,
                        opacity: mounted ? 0.6 : 0,
                        transform: mounted ? `scale(1)` : `scale(0)`,
                        transition: `all ${1 + Math.random() * 2}s cubic-bezier(0.175, 0.885, 0.32, 1.275)`,
                        transitionDelay: `${Math.random() * 0.5}s`
                    }}
                />
            );
        }
        return particles;
    };

    return (
        <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden transition-colors duration-500" style={{ backgroundColor: 'var(--bg-base)' }}>
            
            {/* Ambient Background Glow */}
            <div 
                className={`absolute w-[800px] h-[800px] rounded-full blur-[100px] pointer-events-none transition-all duration-1000 ${mounted ? 'opacity-30 scale-100' : 'opacity-0 scale-50'}`}
                style={{ 
                    background: 'radial-gradient(circle, var(--accent-blue-glow) 0%, transparent 60%)',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)'
                }}
            />

            {/* Particles */}
            {renderParticles()}

            <div className="relative z-10 flex flex-col items-center text-center max-w-4xl px-6">
                
                {/* Header Logo */}
                <div 
                    className={`flex items-center gap-2 mb-10 transition-all duration-1000 transform ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                    style={{ transitionDelay: '100ms' }}
                >
                    <div 
                        className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white text-sm shadow-lg"
                        style={{ background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))' }}
                    >
                        ID
                    </div>
                    <span className="font-bold text-xl tracking-wide" style={{ color: 'var(--text-primary)' }}>IDxVPN</span>
                    <span className="text-xl" style={{ color: 'var(--text-secondary)' }}>Welcome</span>
                </div>

                {/* Hero Logo Image (Attached Shield) */}
                <div 
                    className={`mb-8 w-64 md:w-80 rounded-2xl overflow-hidden transition-all duration-1000 transform ${mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-90'}`}
                    style={{ transitionDelay: '200ms', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', border: '1px solid var(--border)' }}
                >
                    <img src={logoImage} alt="Traffic Insight - VPN Detection Pipeline" className="w-full h-auto" />
                </div>

                {/* Main Headline */}
                <h1 
                    className={`text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.2] mb-4 transition-all duration-1000 transform ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                    style={{ color: 'var(--text-primary)', transitionDelay: '300ms' }}
                >
                    Multi-Layer System for VPN Detection & Deanonymisation
                    <br />
                    <span style={{ 
                        backgroundImage: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        display: 'inline-block',
                        marginTop: '0.2em'
                    }}>
                        Using Machine Learning
                    </span>
                </h1>

                {/* Sub-headline 1 */}
                <h2 
                    className={`text-xl md:text-2xl font-semibold mb-6 transition-all duration-1000 transform ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                    style={{ color: 'var(--accent-blue)', transitionDelay: '350ms' }}
                >
                    AI-Powered Real-Time Network Traffic Intelligence
                </h2>

                {/* Sub-headline 2 */}
                <p 
                    className={`text-lg md:text-xl max-w-3xl mb-12 transition-all duration-1000 transform ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                    style={{ color: 'var(--text-secondary)', transitionDelay: '400ms' }}
                >
                    Seamlessly capture, classify, and analyze encrypted network flows 
                    using a multi-stage ML pipeline for VPN detection and 
                    behavioral deanonymisation.
                </p>

                {/* Call to Action Actions */}
                <div 
                    className={`flex items-center gap-4 transition-all duration-1000 transform ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
                    style={{ transitionDelay: '500ms' }}
                >
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="group flex items-center gap-2 px-8 py-4 rounded-full font-semibold text-white transition-all duration-300 transform hover:scale-105"
                        style={{ background: 'var(--text-primary)', color: 'var(--bg-base)' }}
                    >
                        Launch Dashboard
                        <ArrowRight size={18} className="transition-transform duration-300 group-hover:translate-x-1" />
                    </button>
                    
                    <button
                        onClick={() => navigate('/dashboard')} // Defaults to dashboard but gives explore feeling
                        className="px-8 py-4 rounded-full font-semibold transition-all duration-300 hover:bg-opacity-80"
                        style={{ 
                            background: 'var(--bg-surface)', 
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border)' 
                        }}
                    >
                        Explore Analytics
                    </button>
                </div>
            </div>

        </div>
    );
};

export default Welcome;
