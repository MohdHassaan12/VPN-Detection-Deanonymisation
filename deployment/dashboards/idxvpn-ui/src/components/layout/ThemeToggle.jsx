import React from 'react';
import { useTheme } from '../../context/ThemeContext';
import { Sun, Moon, Monitor } from 'lucide-react';

const themes = [
    { id: 'light',  icon: Sun,     label: 'Light'  },
    { id: 'dark',   icon: Moon,    label: 'Dark'   },
    { id: 'system', icon: Monitor, label: 'System' },
];

const ThemeToggle = () => {
    const { theme, setTheme } = useTheme();

    return (
        <div
            className="flex rounded-xl p-1"
            style={{
                background: 'var(--bg-surface-hover)',
                border: '1px solid var(--border)',
            }}
        >
            {themes.map(({ id, icon: Icon, label }) => {
                const isActive = theme === id;
                return (
                    <button
                        key={id}
                        onClick={() => setTheme(id)}
                        title={`${label} theme`}
                        className="flex-1 flex items-center justify-center py-2 px-3 rounded-lg transition-all duration-200 text-sm font-medium"
                        style={{
                            background: isActive ? 'var(--bg-base)' : 'transparent',
                            color:      isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                            boxShadow:  isActive ? 'var(--shadow-card)' : 'none',
                            border:     isActive ? '1px solid var(--border)' : '1px solid transparent',
                        }}
                        onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = 'var(--text-primary)'; }}
                        onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = 'var(--text-muted)'; }}
                    >
                        <Icon size={15} />
                    </button>
                );
            })}
        </div>
    );
};

export default ThemeToggle;
