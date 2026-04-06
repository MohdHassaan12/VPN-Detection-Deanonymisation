import React from 'react';
import Sidebar from './Sidebar';

const Layout = ({ activeTab, setActiveTab, children }) => {
    return (
        <div className="min-h-screen flex bg-background text-default font-sans selection:bg-[#4f8fff] selection:text-white">
            {/* Dynamic abstract background effects */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[0%] left-[-10%] w-[60%] h-[60%] bg-gradient-to-br from-[#2555ff]/15 to-transparent rounded-full mix-blend-screen filter blur-[120px] opacity-30 animate-pulse"></div>
                <div className="absolute bottom-[0%] right-[-10%] w-[60%] h-[60%] bg-gradient-to-tl from-[#7b2cbf]/15 to-transparent rounded-full mix-blend-screen filter blur-[120px] opacity-30 animate-pulse" style={{ animationDelay: '2s' }}></div>
                <div className="absolute top-[40%] left-[30%] w-[40%] h-[40%] bg-gradient-to-r from-[#ff9900]/5 to-transparent rounded-full mix-blend-screen filter blur-[100px] opacity-20 hidden lg:block"></div>
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
