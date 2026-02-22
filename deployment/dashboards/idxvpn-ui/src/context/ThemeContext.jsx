import React, { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};

export const ThemeProvider = ({ children }) => {
    const [theme, setTheme] = useState(() => {
        // Hydrate from localStorage or default to 'system'
        const savedTheme = localStorage.getItem('idxvpn-theme');
        return savedTheme || 'system';
    });

    useEffect(() => {
        const root = window.document.documentElement;

        const applyTheme = (targetTheme) => {
            root.classList.remove('light', 'dark');
            if (targetTheme === 'dark') {
                root.classList.add('dark');
            } else if (targetTheme === 'light') {
                root.classList.add('light'); // light mode is default, but class is useful for scoping if needed
            }
        };

        const handleSystemThemeChange = (e) => {
            if (theme === 'system') {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        };

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        if (theme === 'system') {
            applyTheme(mediaQuery.matches ? 'dark' : 'light');
            mediaQuery.addEventListener('change', handleSystemThemeChange);
        } else {
            applyTheme(theme);
        }

        // Save preference
        localStorage.setItem('idxvpn-theme', theme);

        return () => {
            mediaQuery.removeEventListener('change', handleSystemThemeChange);
        };
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};
