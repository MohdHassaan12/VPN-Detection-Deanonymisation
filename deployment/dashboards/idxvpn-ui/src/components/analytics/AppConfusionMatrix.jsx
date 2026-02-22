import React from 'react';

const classes = ['Video', 'VoIP', 'P2P', 'Chat', 'Web'];
const data = [
    [92, 2, 1, 3, 2],
    [1, 88, 0, 9, 2],
    [2, 0, 85, 1, 12],
    [0, 8, 0, 90, 2],
    [3, 1, 9, 1, 86]
];

const AppConfusionMatrix = () => {
    return (
        <div className="glass-panel p-6 rounded-2xl border border-[#ffffff1a] overflow-hidden flex flex-col">
            <div className="mb-6">
                <h3 className="text-xl font-bold text-white tracking-tight">Confusion Matrix (Top 5 Apps)</h3>
                <p className="text-[#a0aabf] text-sm mt-2 leading-relaxed">
                    The CNN accurately separates Chat from VoIP despite similarities in encrypted packet length distributions.
                </p>
            </div>

            <div className="overflow-x-auto pb-2 mt-auto">
                <table className="w-full text-center border-collapse text-sm">
                    <thead>
                        <tr>
                            <th className="p-3 text-[#a0aabf] font-medium border-b border-[#ffffff1a]"></th>
                            {classes.map(c => (
                                <th key={c} className="p-3 text-[#a0aabf] font-medium border-b border-[#ffffff1a]">{c}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="font-mono">
                        {data.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                                <th className="p-3 text-[#a0aabf] font-medium text-right border-r border-[#ffffff1a]">
                                    {classes[rowIndex]}
                                </th>
                                {row.map((value, colIndex) => {
                                    const isDiagonal = rowIndex === colIndex;
                                    const alpha = value / 100;

                                    let bgColor = 'transparent';
                                    let textColor = value > 40 ? 'text-white' : 'text-[#a0aabf]';

                                    if (isDiagonal) {
                                        bgColor = `hsla(215, 100%, 65%, ${alpha * 0.8 + 0.1})`;
                                    } else if (value > 0) {
                                        bgColor = `hsla(260, 100%, 70%, ${alpha * 1.5 + 0.05})`;
                                    }

                                    return (
                                        <td
                                            key={colIndex}
                                            className={`p-3 m-1 border border-[#ffffff0d] transition-colors rounded-sm hover:bg-[#ffffff1a] cursor-default ${textColor} ${isDiagonal ? 'font-bold' : ''}`}
                                            style={{ backgroundColor: bgColor }}
                                        >
                                            {value}%
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AppConfusionMatrix;
