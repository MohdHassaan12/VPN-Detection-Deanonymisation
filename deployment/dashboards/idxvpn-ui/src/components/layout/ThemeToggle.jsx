import React from 'react';
import { useTheme } from '../../context/ThemeContext';
import { Sun, Moon, Monitor } from 'lucide-react';

const ThemeToggle = () => {
    const { theme, setTheme } = useTheme();

    const themes = [
        { id: 'light', icon: Sun, label: 'Light' },
        { id: 'dark', icon: Moon, label: 'Dark' },
        { id: 'system', icon: Monitor, label: 'System' }
    ];

    return (
        <div className="flex bg-black/5 dark:bg-white/5 dark:bg-black/5 dark:bg-black/40 rounded-xl p-1 border border-divider">
            {themes.map(({ id, icon: Icon, label }) => (
                <button
                    key={id}
                    onClick={() => setTheme(id)}
                    className={`flex-1 flex items-center justify-center py-2 px-3 rounded-lg transition-all text-sm font-medium ${theme === id
                            ? 'bg-panel text-default shadow-sm border border-divider'
                            : 'text-muted hover:text-default hover:bg-black/10 dark:bg-white/10'
                        }`}
                    title={`${label} theme`}
                >
                    <Icon size={16} />
                </button>
            ))}
        </div>
    );
};

export default ThemeToggle;
