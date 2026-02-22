import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ activeTab, setActiveTab, children }) => {
    return (
        <div className="min-h-screen flex bg-[#0d1017] text-[#e2e8f0] font-sans selection:bg-[#4f8fff] selection:text-white">
            {/* Dynamic background effects */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#2555ff] rounded-full mix-blend-screen filter blur-[150px] opacity-10 animate-blob"></div>
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#7b2cbf] rounded-full mix-blend-screen filter blur-[150px] opacity-10 animate-blob animation-delay-2000"></div>
            </div>

            <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

            <main className="flex-1 ml-64 p-8 overflow-y-auto z-10 relative">
                <div className="max-w-7xl mx-auto space-y-8 animate-fade-in-up">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
