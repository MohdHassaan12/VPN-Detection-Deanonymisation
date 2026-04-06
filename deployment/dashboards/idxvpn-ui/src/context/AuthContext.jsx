import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            // In a real app, you would validate the token with the backend here.
            // For now, we'll just decode the JWT payload or set a dummy user.
            try {
                // Fix base64url padding before atob (JWT payloads are unpadded base64url)
                const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
                const padded = b64 + '='.repeat((4 - b64.length % 4) % 4);
                const payload = JSON.parse(atob(padded));
                setUser({ username: payload.sub, role: payload.role });
            } catch (e) {
                console.error("Invalid token found in storage", e);
                localStorage.removeItem('token');
            }
        }
        setLoading(false);
    }, []);

    // Demo credentials — seeded with defaults plus any locally registered users
    const getUsers = () => {
        const stored = JSON.parse(localStorage.getItem('idxvpn-registered-users') || '{}');
        return {
            admin:  { password: 'admin123',  role: 'admin'  },
            viewer: { password: 'viewer123', role: 'viewer' },
            ...stored,
        };
    };

    /** Create a minimal mock JWT (unsigned) for local sessions */
    const makeMockToken = (username, role) => {
        const header = btoa(JSON.stringify({ alg: 'none', typ: 'JWT' }));
        const payload = btoa(JSON.stringify({ sub: username, role, exp: Math.floor(Date.now() / 1000) + 86400 }));
        return `${header}.${payload}.mock`;
    };

    const register = async ({ username, password, fullName, email, role = 'viewer' }) => {
        const users = getUsers();
        if (users[username]) {
            return { success: false, message: `Username "${username}" is already taken. Please choose another.` };
        }
        // Persist to localStorage (demo mode — no backend)
        const stored = JSON.parse(localStorage.getItem('idxvpn-registered-users') || '{}');
        stored[username] = { password, role, fullName, email };
        localStorage.setItem('idxvpn-registered-users', JSON.stringify(stored));
        return { success: true };
    };

    const login = async (username, password) => {
        // --- 1. Try local demo credentials first (works offline / without backend) ---
        const demoUser = getUsers()[username];
        if (demoUser && demoUser.password === password) {
            const token = makeMockToken(username, demoUser.role);
            localStorage.setItem('token', token);
            setUser({ username, role: demoUser.role });
            return true;
        }

        // --- 2. Fall back to live backend if credentials don't match local demos ---
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            // Use VITE_API_BASE_URL in prod (set at build time) or the current origin in dev
            const apiBase = import.meta.env.VITE_API_BASE_URL || '';
            const response = await fetch(`${apiBase}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            if (!response.ok) {
                const errText = await response.text();
                console.error('Login failed:', response.status, errText);
                throw new Error('Login failed');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);

            // Fix base64url padding before atob (JWT payloads are unpadded)
            const b64 = data.access_token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
            const padded = b64 + '='.repeat((4 - b64.length % 4) % 4);
            const payload = JSON.parse(atob(padded));
            setUser({ username: payload.sub, role: payload.role });
            return true;
        } catch (error) {
            console.error('Login error:', error);
            return false;
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, register, isAuthenticated: !!user, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
