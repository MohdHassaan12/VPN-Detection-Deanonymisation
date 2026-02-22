import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        const success = await login(username, password);

        if (success) {
            navigate('/');
        } else {
            setError('Invalid username or password');
        }

        setIsLoading(false);
    };

    return (
        <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-4 transition-colors duration-300">
            <div className="w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border-color)] p-8 rounded-xl shadow-lg relative transform transition-all duration-300">
                {/* Decorative Elements */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--accent-red)] opacity-10 rounded-full blur-3xl -z-10 animate-pulse"></div>
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-[var(--accent-blue)] opacity-10 rounded-full blur-3xl -z-10 animate-pulse" style={{ animationDelay: '1s' }}></div>

                <h2 className="text-2xl font-bold bg-gradient-to-r from-[var(--text-primary)] to-[var(--text-secondary)] bg-clip-text text-transparent text-center mb-6">
                    IdxVPN Auth
                </h2>

                <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2" htmlFor="username">
                            Username
                        </label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)] px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-blue)] transition-all"
                            placeholder="admin or viewer"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2" htmlFor="password">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)] px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-blue)] transition-all"
                            required
                            placeholder="••••••••"
                        />
                    </div>

                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm text-center">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading}
                        className={`w-full bg-[var(--accent-blue)] text-white hover:bg-blue-600 disabled:bg-[var(--border-color)] disabled:cursor-not-allowed font-medium py-3 rounded-lg transition-all duration-200 shadow-md shadow-blue-500/20 active:scale-[0.98] flex items-center justify-center gap-2`}
                    >
                        {isLoading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        ) : 'Sign In'}
                    </button>

                    <div className="text-center text-xs text-[var(--text-muted)] mt-4">
                        <p>Demo accounts:</p>
                        <p className="mt-1"><code>admin / admin123</code> | <code>viewer / viewer123</code></p>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Login;
