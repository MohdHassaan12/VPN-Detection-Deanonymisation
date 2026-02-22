// app.js

// Initialize Charts
const initCharts = () => {
    // Shared chart options
    Chart.defaults.color = 'hsl(210, 16%, 65%)';
    Chart.defaults.font.family = 'Inter, sans-serif';

    // --- Dashboard: Line Chart (Traffic) ---
    const trafficCtx = document.getElementById('trafficChart').getContext('2d');
    const gradientBlue = trafficCtx.createLinearGradient(0, 0, 0, 400);
    gradientBlue.addColorStop(0, 'hsla(215, 100%, 65%, 0.5)');
    gradientBlue.addColorStop(1, 'hsla(215, 100%, 65%, 0)');

    const trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: ['10:00', '10:05', '10:10', '10:15', '10:20', '10:25', '10:30', '10:35', '10:40', '10:45', '10:50'],
            datasets: [{
                label: 'Total Requests',
                data: [120, 190, 150, 180, 220, 210, 280, 250, 310, 290, 350],
                borderColor: 'hsl(215, 100%, 65%)',
                backgroundColor: gradientBlue,
                borderWidth: 2,
                pointBackgroundColor: 'hsl(215, 100%, 65%)',
                pointBorderColor: '#fff',
                pointRadius: 3,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.4
            },
            {
                label: 'VPN Detected',
                data: [30, 45, 35, 60, 55, 70, 65, 80, 75, 90, 85],
                borderColor: 'hsl(260, 100%, 70%)',
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [5, 5],
                pointBackgroundColor: 'hsl(260, 100%, 70%)',
                pointRadius: 2,
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: { boxWidth: 10, usePointStyle: true }
                },
                tooltip: {
                    backgroundColor: 'rgba(30,33,40, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 10,
                    boxPadding: 4
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false }
                },
                x: {
                    grid: { display: false, drawBorder: false }
                }
            }
        }
    });

    // --- Dashboard: Doughnut Chart (App Classes) ---
    const appCtx = document.getElementById('appClassChart').getContext('2d');
    const appChart = new Chart(appCtx, {
        type: 'doughnut',
        data: {
            labels: ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'Other'],
            datasets: [{
                data: [45, 25, 15, 10, 5],
                backgroundColor: [
                    'hsl(215, 100%, 65%)', // Blue
                    'hsl(260, 100%, 70%)', // Purple
                    'hsl(150, 70%, 55%)',  // Green
                    'hsl(350, 80%, 65%)',  // Red
                    'hsl(210, 10%, 45%)'   // Gray
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20, boxWidth: 12, usePointStyle: true, color: 'hsl(210, 16%, 65%)' }
                }
            }
        }
    });

    // --- Analytics: Bar Chart (Accuracy) ---
    const accCtx = document.getElementById('accuracyChart').getContext('2d');
    const accuracyChart = new Chart(accCtx, {
        type: 'bar',
        data: {
            labels: ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'VOIP', 'GAMING'],
            datasets: [{
                label: 'F1 Score per App Class',
                data: [0.96, 0.92, 0.88, 0.85, 0.89, 0.95],
                backgroundColor: 'hsla(150, 70%, 55%, 0.7)',
                borderColor: 'hsl(150, 70%, 55%)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1.0,
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                x: {
                    grid: { display: false }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    initConfusionMatrix();

    return { trafficChart, appChart, accuracyChart };
};

// Initialize Confusion Matrix Table
const initConfusionMatrix = () => {
    const tbody = document.querySelector('#confMatrix tbody');
    if (!tbody) return;

    const classes = ['Video', 'VoIP', 'P2P', 'Chat', 'Web'];
    const data = [
        [92, 2, 1, 3, 2],    // Video
        [1, 88, 0, 9, 2],    // VoIP
        [2, 0, 85, 1, 12],   // P2P
        [0, 8, 0, 90, 2],    // Chat (some confusion with VoIP)
        [3, 1, 9, 1, 86]     // Web
    ];

    let html = '';
    data.forEach((row, rowIndex) => {
        html += `<tr><th>${classes[rowIndex]}</th>`;
        row.forEach((value, colIndex) => {
            // Calculate a color mapping (blue/purple scale based on percentage)
            // Using logic: if high value (diagonal), strong blue. If low, very dim.
            const isDiagonal = rowIndex === colIndex;
            const alpha = value / 100;
            // Base color string
            let bgColor;
            if (isDiagonal) {
                // Diagonal uses accent-blue
                bgColor = `hsla(215, 100%, 65%, ${alpha * 0.8 + 0.1})`;
            } else {
                // Off-diagonal errors use a purplish or reddish hue
                bgColor = value > 0 ? `hsla(260, 100%, 70%, ${alpha * 1.5 + 0.05})` : 'transparent';
            }

            html += `<td class="val-cell" style="background-color: ${bgColor};">${value}%</td>`;
        });
        html += '</tr>';
    });
    tbody.innerHTML = html;
};

// Simulate Real-time data updates
const simulateLiveData = () => {
    let totals = 12458;
    let vpns = 3142;
    let blocks = 156;
    let deanonymised = 2891;

    const apps = ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'VOIP', 'GAMING'];
    const ips = ['192.168.1.100', '10.0.0.5', '172.16.0.42', '192.168.1.205', '10.0.1.15'];

    const logsBody = document.getElementById('logs-body');

    // Add initial rows
    for (let i = 0; i < 5; i++) {
        addLogEntry(logsBody, generateRandomLog(apps, ips));
    }

    // Interval to update stats and table
    setInterval(() => {
        // Update top KPIs incrementally
        totals += Math.floor(Math.random() * 5);
        if (Math.random() > 0.5) vpns += 1;
        if (Math.random() > 0.9) blocks += 1;
        if (Math.random() > 0.45) deanonymised += 1;

        const totalEl = document.getElementById('kpi-total');
        if (totalEl) totalEl.textContent = totals.toLocaleString();

        const vpnEl = document.getElementById('kpi-vpn');
        if (vpnEl) vpnEl.textContent = vpns.toLocaleString();

        const blockEl = document.getElementById('kpi-blocks');
        if (blockEl) blockEl.textContent = blocks.toLocaleString();

        const deanonEl = document.getElementById('kpi-deanon');
        if (deanonEl) deanonEl.textContent = deanonymised.toLocaleString();

        // Add a new row every 2 seconds
        if (Math.random() > 0.4) {
            addLogEntry(logsBody, generateRandomLog(apps, ips));
            // Keep table size manageable
            if (logsBody.children.length > 8) {
                logsBody.removeChild(logsBody.lastChild);
            }
        }
    }, 2000);
};

const generateRandomLog = (apps, ips) => {
    const isVpn = Math.random() > 0.6;
    const isMalicious = isVpn && Math.random() > 0.7; // malicious intent more likely if VPN

    let score = Math.floor(Math.random() * 20); // allow
    let actionStr = '<span class="action-badge action-allow">Allow</span>';
    let scoreClass = 'score-low';

    if (isMalicious) {
        score = Math.floor(Math.random() * 30 + 70); // 70-100
        actionStr = '<span class="action-badge action-block">Block</span>';
        scoreClass = 'score-high';
    } else if (isVpn && Math.random() > 0.5) {
        score = Math.floor(Math.random() * 40 + 21); // 21-60
        actionStr = '<span class="action-badge action-challenge">Challenge</span>';
        scoreClass = 'score-med';
    }

    const app = apps[Math.floor(Math.random() * apps.length)];
    const ip = ips[Math.floor(Math.random() * ips.length)];

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour12: false }) + '.' + Math.floor(now.getMilliseconds() / 10).toString().padStart(2, '0');

    // New Columns: Timestamp | Source IP | Is VPN? | True App | Intent Score | Policy Action
    return `
        <tr>
            <td class="timestamp">${timeStr}</td>
            <td class="ip-address">${ip}</td>
            <td>${isVpn ? '<span class="vpn-badge">Yes (Deanonymised)</span>' : '<span class="text-muted">No</span>'}</td>
            <td><span class="app-class">${app}</span></td>
            <td class="${scoreClass}">${score}/100</td>
            <td>${actionStr}</td>
        </tr>
    `;
};

const addLogEntry = (tbody, htmlString) => {
    // Insert at top
    tbody.insertAdjacentHTML('afterbegin', htmlString);

    // Simple flash animation to highlight new row
    const newRow = tbody.firstElementChild;
    newRow.style.backgroundColor = 'rgba(112, 164, 255, 0.1)';
    setTimeout(() => {
        newRow.style.backgroundColor = '';
    }, 1000);
};

// Handle Navigation
const initNavigation = () => {
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            // Remove active class from all links
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add to clicked link
            item.classList.add('active');

            // Hide all views
            views.forEach(view => view.classList.remove('active'));

            // Show target view
            const targetId = 'view-' + item.getAttribute('data-view');
            document.getElementById(targetId).classList.add('active');
        });
    });
};

// Handle Detection Simulator
const initDetectionSimulator = () => {
    const btn = document.getElementById('btn-detect');
    if (!btn) return;

    btn.addEventListener('click', () => {
        const isVpn = document.getElementById('sim-is-vpn').checked;

        document.getElementById('detect-idle').style.display = 'none';
        document.getElementById('detect-output').style.display = 'none';
        document.getElementById('detect-loading').style.display = 'block';

        // Disable button during scan
        btn.disabled = true;
        btn.textContent = 'Scanning...';
        btn.style.opacity = '0.7';

        setTimeout(() => {
            document.getElementById('detect-loading').style.display = 'none';
            document.getElementById('detect-output').style.display = 'block';

            btn.disabled = false;
            btn.textContent = 'Run Pipeline Detection';
            btn.style.opacity = '1';

            // Generate some plausible results
            const apps = ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'GAMING'];
            const app = apps[Math.floor(Math.random() * apps.length)];
            const conf = (Math.random() * 10 + 89).toFixed(1); // 89.0 to 99.0

            document.getElementById('res-app').textContent = app;
            document.getElementById('res-conf').textContent = conf + '%';

            // Risk logic
            const isMalicious = isVpn && Math.random() > 0.6;
            let score = Math.floor(Math.random() * 20); // 0-20
            let actionStr = 'ALLOW';
            let descStr = `Normal ${app.toLowerCase()} behavior detected.`;
            let iconColor = 'var(--accent-green)';
            let iconShadow = 'var(--accent-green-dim)';
            let borderColor = 'var(--accent-green)';

            if (isMalicious) {
                score = Math.floor(Math.random() * 30 + 70); // 70-100
                actionStr = 'BLOCK';
                descStr = `High risk pattern indicative of evasion or botnet C2 activity.`;
                iconColor = 'var(--accent-red)';
                iconShadow = 'var(--accent-red-dim)';
                borderColor = 'var(--accent-red)';
            } else if (isVpn && Math.random() > 0.4) {
                score = Math.floor(Math.random() * 40 + 21); // 21-60
                actionStr = 'CHALLENGE';
                descStr = `Anomalous flow characteristics observed inside tunnel.`;
                iconColor = 'var(--accent-yellow)';
                iconShadow = 'rgba(243, 156, 18, 0.15)';
                borderColor = 'var(--accent-yellow)';
            }

            document.getElementById('res-action').textContent = actionStr;
            document.getElementById('res-action').style.color = iconColor;
            document.getElementById('res-desc').textContent = descStr;
            document.getElementById('res-score').textContent = `Risk Score: ${score}/100`;

            const card = document.getElementById('res-policy-card');
            card.style.borderLeft = `4px solid ${borderColor}`;

            const icon = document.getElementById('res-icon');
            icon.style.color = iconColor;
            icon.style.boxShadow = `0 0 15px ${iconShadow}`;
            icon.innerHTML = actionStr === 'ALLOW'
                ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>'
                : actionStr === 'BLOCK'
                    ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
                    : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';

        }, 1500);
    });
};

// Init On Load
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initCharts();
    simulateLiveData();
    initDetectionSimulator();
});
