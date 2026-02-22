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
                // simple base64 decode for the payload part of JWT
                const payload = JSON.parse(atob(token.split('.')[1]));
                setUser({ username: payload.sub, role: payload.role });
            } catch (e) {
                console.error("Invalid token found in storage", e);
                localStorage.removeItem('token');
            }
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('http://localhost:8080/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error('Login failed');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);

            const payload = JSON.parse(atob(data.access_token.split('.')[1]));
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
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
