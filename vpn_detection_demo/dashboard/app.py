"""
dashboard/app.py
-----------------
Real-time Streamlit dashboard for VPN Detection Demo.

• Reads shared state from .pipeline_state.json (written by main.py)
• Auto-refreshes every 1 second  (streamlit-autorefresh)
• Displays:
    – Connected devices with VPN status & risk scores
    – Live traffic timeline chart
    – Per-device flow statistics
    – Risk score gauge per device
    – Global KPIs (total packets, VPN rate, blocked flows)

Run:
    # First start the pipeline (in another terminal):
    python vpn_detection_demo/main.py --mock

    # Then start the dashboard:
    streamlit run vpn_detection_demo/dashboard/app.py
"""

import json
import os
import sys
import time
import collections
import random
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np

# ── Path setup ───────────────────────────────────────────────────────────────
DASHBOARD_DIR = os.path.dirname(__file__)
DEMO_ROOT     = os.path.dirname(DASHBOARD_DIR)
PROJECT_ROOT  = os.path.dirname(DEMO_ROOT)
sys.path.insert(0, DEMO_ROOT)
sys.path.insert(0, PROJECT_ROOT)

STATE_FILE = os.path.join(DEMO_ROOT, ".pipeline_state.json")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IDX VPN Detection | Cyber Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-refresh (try streamlit-autorefresh, fall back to manual) ─────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, key="autorefresh")
except ImportError:
    pass   # User can click "Refresh" manually

# ── Custom CSS – premium dark cyber theme ────────────────────────────────────
st.markdown("""
<style>
  /* ── Base ── */
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"]   { font-family: 'Outfit', sans-serif; }
  .stApp                        { background: #080b12; color: #e2e8f0; }
  section[data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #1e2432; }

  /* ── Metric cards ── */
  .metric-card {
    background: linear-gradient(135deg, #111827 0%, #0d1117 100%);
    border: 1px solid #1e2432;
    border-radius: 16px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    transition: transform .2s, border-color .2s;
  }
  .metric-card:hover { transform: translateY(-2px); border-color: #2e3a50; }
  .metric-card .label { font-size: 11px; font-weight: 600; letter-spacing: 1.5px;
                         text-transform: uppercase; color: #5a6a85; margin-bottom: 8px; }
  .metric-card .value { font-family: 'JetBrains Mono', monospace; font-size: 2.2rem;
                         font-weight: 700; line-height: 1; }
  .metric-card .sub   { font-size: 12px; color: #5a6a85; margin-top: 8px; }

  /* ── Risk badge ── */
  .badge-low    { background:#0d3320; color:#1bc553; border:1px solid #1bc55340;
                   border-radius:8px; padding:3px 10px; font-size:12px; font-weight:700; }
  .badge-medium { background:#3a2500; color:#ff9900; border:1px solid #ff990040;
                   border-radius:8px; padding:3px 10px; font-size:12px; font-weight:700; }
  .badge-high   { background:#3a0a0a; color:#ff5050; border:1px solid #ff505040;
                   border-radius:8px; padding:3px 10px; font-size:12px; font-weight:700; }
  .badge-vpn    { background:#3a1500; color:#ff7b00; border:1px solid #ff7b0040;
                   border-radius:8px; padding:3px 10px; font-size:12px; font-weight:700; }
  .badge-normal { background:#0a1f0a; color:#1bc553; border:1px solid #1bc55340;
                   border-radius:8px; padding:3px 10px; font-size:12px; font-weight:700; }

  /* ── Device table ── */
  .dev-row {
    background:#0d1117;
    border:1px solid #1e2432;
    border-radius:12px;
    padding:16px 20px;
    margin-bottom:10px;
    display:flex;
    align-items:center;
    gap:16px;
    transition: border-color .15s;
  }
  .dev-row:hover { border-color: #2e3a50; }
  .dev-row .ip   { font-family:'JetBrains Mono',monospace; font-size:13px; color:#4f8fff; min-width:130px; }
  .dev-row .lbl  { font-size:14px; font-weight:600; min-width:160px; }
  .dev-row .risk { font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:700; min-width:50px; text-align:right; }

  /* ── Pulse dot ── */
  .pulse { display:inline-block; width:10px; height:10px; border-radius:50%;
            animation: pulse 1.4s infinite; }
  @keyframes pulse {
    0%  { box-shadow: 0 0 0 0 currentColor; }
    70% { box-shadow: 0 0 0 6px transparent; }
    100%{ box-shadow: 0 0 0 0 transparent; }
  }

  /* ── Streamlit overrides ── */
  div[data-testid="stMetricValue"] { font-family:'JetBrains Mono',monospace; font-size:2rem; font-weight:700; }
  h1,h2,h3 { font-family:'Outfit',sans-serif !important; }
  .stProgress > div > div { background: linear-gradient(90deg,#2555ff,#4f8fff) !important; border-radius:4px; }
  hr { border-color: #1e2432; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# State helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_state() -> dict:
    """Load pipeline state from JSON file written by main.py."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _risk_colour(level: str) -> str:
    return {"LOW": "#1bc553", "MEDIUM": "#ff9900", "HIGH": "#ff5050"}.get(level, "#5a6a85")


def _badge_class(level: str) -> str:
    return {"LOW": "badge-low", "MEDIUM": "badge-medium", "HIGH": "badge-high"}.get(level, "badge-low")


# ─────────────────────────────────────────────────────────────────────────────
# Session-state: rolling chart history
# ─────────────────────────────────────────────────────────────────────────────

if "chart_history" not in st.session_state:
    st.session_state.chart_history = collections.deque(maxlen=60)  # 60 seconds
if "event_log" not in st.session_state:
    st.session_state.event_log = collections.deque(maxlen=50)


def _append_chart_point(state: dict):
    devices = state.get("devices", {})
    n_vpn    = sum(1 for d in devices.values() if d.get("is_vpn"))
    n_normal = len(devices) - n_vpn
    total_pkt_rate = sum(d.get("pkt_rate", 0) for d in devices.values())
    st.session_state.chart_history.append({
        "time":       time.strftime("%H:%M:%S"),
        "vpn":        n_vpn,
        "normal":     n_normal,
        "pkt_rate":   round(total_pkt_rate, 1),
    })


def _append_event(state: dict):
    devices = state.get("devices", {})
    for ip, d in devices.items():
        last_event = {
            "time":       time.strftime("%H:%M:%S"),
            "ip":         ip,
            "label":      d.get("label", "Unknown"),
            "is_vpn":     d.get("is_vpn", False),
            "risk_score": d.get("risk_score", 0),
            "risk_level": d.get("risk_level", "LOW"),
            "confidence": d.get("confidence", 0),
            "pkt_rate":   d.get("pkt_rate", 0),
        }
        # Only append if changed from last entry for this IP
        existing = [e for e in st.session_state.event_log if e.get("ip") == ip]
        if not existing or existing[-1]["is_vpn"] != last_event["is_vpn"] or existing[-1]["risk_score"] != last_event["risk_score"]:
            st.session_state.event_log.appendleft(last_event)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛡 IDX VPN Detection")
    st.markdown("---")

    state = _load_state()
    running = state.get("running", False)
    mock    = state.get("mock_mode", False)
    iface   = state.get("capture_interface", "—")

    status_color = "#1bc553" if running else "#ff5050"
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">'
        f'<span class="pulse" style="color:{status_color};background:{status_color};"></span>'
        f'<span style="font-weight:600;color:{status_color}">{"Pipeline Active" if running else "Pipeline Offline"}</span>'
        f'</div>', unsafe_allow_html=True
    )

    st.markdown(f"""
| Parameter | Value |
|-----------|-------|
| Mode | {'🎭 Mock/Demo' if mock else '📡 Live Capture'} |
| Interface | `{iface}` |
| Local IP | `{state.get('local_ip', '—')}` |
| Gateway | `{state.get('gateway_ip', '—')}` |
""")

    st.markdown("---")
    st.markdown("### ▶ Quick Start")
    st.code("# Terminal 1: start pipeline\npython vpn_detection_demo/main.py --mock\n\n# Terminal 2: start dashboard\nstreamlit run vpn_detection_demo/dashboard/app.py", language="bash")
    st.markdown("### 📡 Live Capture")
    st.code("sudo python vpn_detection_demo/main.py --interface en0", language="bash")


# ─────────────────────────────────────────────────────────────────────────────
# Main dashboard
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<h1 style="font-size:1.8rem;font-weight:700;margin:0 0 4px">🛡 VPN Detection & Deanonymisation</h1>'
    '<p style="color:#5a6a85;font-size:14px;margin:0 0 24px">Real-time ML-powered network traffic analysis on macOS</p>',
    unsafe_allow_html=True
)

# Load latest state
state = _load_state()
devices = state.get("devices", {})

# Guard: no pipeline state yet
if not state:
    st.warning("⚠️ Pipeline not running. Start `main.py` first (see sidebar for commands).", icon="⚠️")
    # Show demo mode hint
    col1, col2 = st.columns(2)
    with col1:
        st.code("python vpn_detection_demo/main.py --mock", language="bash")
    with col2:
        st.markdown("_No tshark / root access needed in mock mode._")
    st.stop()

# Append chart history
_append_chart_point(state)
_append_event(state)

# ─── Top KPI strip ────────────────────────────────────────────────────────────
total_inf = state.get("total_inferences", 0)
vpn_cnt   = state.get("vpn_detected_count", 0)
n_devices = len(devices)
n_vpn     = sum(1 for d in devices.values() if d.get("is_vpn"))
n_high    = sum(1 for d in devices.values() if d.get("risk_level") == "HIGH")
vpn_pct   = (vpn_cnt / max(1, total_inf)) * 100

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""<div class="metric-card">
      <div class="label">Total Inferences</div>
      <div class="value" style="color:#4f8fff">{total_inf:,}</div>
      <div class="sub">since pipeline start</div>
    </div>""", unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""<div class="metric-card">
      <div class="label">VPN Detected</div>
      <div class="value" style="color:#ff9900">{vpn_cnt:,}</div>
      <div class="sub">{vpn_pct:.1f}% of total</div>
    </div>""", unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""<div class="metric-card">
      <div class="label">Active Devices</div>
      <div class="value" style="color:#a78bfa">{n_devices}</div>
      <div class="sub">on local network</div>
    </div>""", unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""<div class="metric-card">
      <div class="label">VPN Active Now</div>
      <div class="value" style="color:#{"ff5050" if n_vpn > 0 else "1bc553"}">{n_vpn}</div>
      <div class="sub">device(s) using VPN</div>
    </div>""", unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""<div class="metric-card">
      <div class="label">High-Risk</div>
      <div class="value" style="color:#ff5050">{n_high}</div>
      <div class="sub">device(s) risk ≥ 61</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Device panel ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("### 📡 Connected Devices – Live Status")

    if not devices:
        st.info("No devices detected yet. Waiting for traffic…")
    else:
        for ip, d in sorted(devices.items(), key=lambda x: x[1].get("risk_score", 0), reverse=True):
            label      = d.get("label", "Unknown")
            is_vpn     = d.get("is_vpn", False)
            risk_score = d.get("risk_score", 0)
            risk_level = d.get("risk_level", "LOW")
            confidence = d.get("confidence", 0)
            pkt_rate   = d.get("pkt_rate", 0)
            total_pkts = d.get("total_packets", 0)
            total_kbytes = d.get("total_bytes", 0) / 1024

            vpn_html  = '<span class="badge-vpn">VPN ON</span>' if is_vpn else '<span class="badge-normal">Normal</span>'
            risk_html = f'<span class="{_badge_class(risk_level)}">{risk_level}</span>'
            risk_col  = _risk_colour(risk_level)

            st.markdown(f"""
<div class="dev-row">
  <span style="font-size:22px">{"📱" if "mobile" in label.lower() or "iphone" in label.lower() else "💻" if "laptop" in label.lower() or "mac" in label.lower() else "📡" if "router" in label.lower() else "🖥"}</span>
  <div style="flex:1">
    <div class="lbl">{label}</div>
    <div class="ip">{ip}</div>
  </div>
  <div style="text-align:center;min-width:80px">
    {vpn_html}
  </div>
  <div style="text-align:center;min-width:70px">
    {risk_html}
  </div>
  <div class="risk" style="color:{risk_col}">{risk_score}</div>
  <div style="text-align:right;min-width:90px;font-size:12px;color:#5a6a85">
    {pkt_rate:.0f} pkt/s<br>
    <span style="font-family:'JetBrains Mono',monospace">{confidence:.0%}</span> conf
  </div>
</div>""", unsafe_allow_html=True)

            # Risk score progress bar
            st.progress(min(1.0, risk_score / 100))


with col_right:
    st.markdown("### 📊 Traffic Timeline")

    if st.session_state.chart_history:
        df_chart = pd.DataFrame(list(st.session_state.chart_history))
        st.area_chart(
            df_chart.set_index("time")[["vpn", "normal"]],
            color=["#ff9900", "#4f8fff"],
            use_container_width=True,
            height=200,
        )
        st.markdown("_Orange = VPN flows · Blue = Normal flows_")
    else:
        st.info("Chart data accumulating…")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📦 Packet Rate")
    if st.session_state.chart_history:
        df_pkt = pd.DataFrame(list(st.session_state.chart_history))
        st.line_chart(
            df_pkt.set_index("time")[["pkt_rate"]],
            color=["#a78bfa"],
            use_container_width=True,
            height=150,
        )
    else:
        st.info("Waiting…")

# ─── Event log ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Inference Event Log")

if st.session_state.event_log:
    rows = []
    for e in list(st.session_state.event_log)[:20]:
        rows.append({
            "Time":        e["time"],
            "IP":          e["ip"],
            "Device":      e["label"],
            "VPN?":        "🔴 YES" if e["is_vpn"] else "🟢 NO",
            "Risk Score":  e["risk_score"],
            "Risk Level":  e["risk_level"],
            "Confidence":  f"{e['confidence']:.0%}",
            "Pkt/s":       f"{e['pkt_rate']:.0f}",
        })
    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk Score": st.column_config.ProgressColumn(
                "Risk Score", min_value=0, max_value=100, format="%d"
            )
        }
    )
else:
    st.info("No events yet. Waiting for pipeline data…")

# ─── Device statistics table ──────────────────────────────────────────────────
if devices:
    st.markdown("---")
    st.markdown("### 🔬 Device Flow Statistics")
    rows = []
    for ip, d in devices.items():
        rows.append({
            "IP Address": ip,
            "Label": d.get("label", "—"),
            "VPN": "YES" if d.get("is_vpn") else "NO",
            "Risk Score": d.get("risk_score", 0),
            "Risk Level": d.get("risk_level", "LOW"),
            "Confidence": f"{d.get('confidence', 0):.1%}",
            "Pkt/s": f"{d.get('pkt_rate', 0):.1f}",
            "Total Pkts": d.get("total_packets", 0),
            "Total KB": f"{d.get('total_bytes', 0) / 1024:.1f}",
            "Latency (ms)": f"{d.get('latency_ms', 0):.2f}",
        })
    df_devices = pd.DataFrame(rows)
    st.dataframe(df_devices, use_container_width=True, hide_index=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="margin-top:48px;text-align:center;color:#2e3a50;font-size:12px">'
    'IDX VPN Detection & Deanonymisation · macOS · RandomForest + tshark pipeline · Auto-refresh 1s'
    '</div>',
    unsafe_allow_html=True
)
