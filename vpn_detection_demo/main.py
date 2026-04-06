"""
main.py
--------
Orchestration entry-point for the VPN Detection Demo.

Runs three background tasks concurrently:
    1. PacketCaptureEngine   – live packet capture from interface
    2. Feature extraction    – sliding-window flow features per IP
    3. Inference loop        – ML model scoring for each ready IP
    4. State shared via thread-safe JSON file / in-memory dict for dashboard

Usage
-----
    # Full live capture (requires tshark + sudo or capture entitlements)
    python main.py --interface en0

    # Demo/mock mode (no packets needed, good for presentations)
    python main.py --mock

    # Filter to a specific target device IP
    python main.py --interface en0 --filter-ip 192.168.1.42
"""

import argparse
import json
import logging
import os
import queue
import random
import sys
import threading
import time
from typing import Dict, Any, Optional

# ── Path setup ──────────────────────────────────────────────────────────────
ROOT = os.path.dirname(__file__)
sys.path.insert(0, ROOT)

from capture.packet_capture import PacketCaptureEngine, list_interfaces, detect_local_ip
from capture.capture_types import CapturedPacket
from features.extractor import FlowFeatureExtractor
from model.inference import VPNInferenceEngine, InferenceResult
from utils.device_detection import scan_local_devices, get_gateway_ip

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vpn_demo.main")

# ── Shared state (written by inference loop, read by dashboard) ──────────────
STATE_FILE = os.path.join(ROOT, ".pipeline_state.json")

# In-memory state dict (also persisted to STATE_FILE for Streamlit to read)
_state: Dict[str, Any] = {
    "devices": {},         # ip → {label, is_vpn, risk_score, risk_level, confidence,
                           #        pkt_rate, total_packets, total_bytes, last_seen}
    "gateway_ip": "",
    "local_ip": detect_local_ip(),
    "capture_interface": "",
    "mock_mode": False,
    "running": True,
    "start_time": time.time(),
    "total_inferences": 0,
    "vpn_detected_count": 0,
}
_state_lock = threading.Lock()


def _write_state():
    """Persist in-memory state to JSON file for the Streamlit dashboard to read."""
    try:
        with _state_lock:
            snapshot = json.dumps(_state, default=str)
        with open(STATE_FILE, "w") as f:
            f.write(snapshot)
    except Exception as e:
        logger.debug(f"State write error: {e}")


def _update_device_state(ip: str, result: InferenceResult, label: str,
                         pkt_rate: float, total_packets: int, total_bytes: int):
    """Update per-device entry in shared state."""
    with _state_lock:
        _state["devices"][ip] = {
            "ip": ip,
            "label": label,
            "is_vpn": result.is_vpn,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "confidence": round(result.confidence, 4),
            "latency_ms": result.latency_ms,
            "pkt_rate": round(pkt_rate, 1),
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "last_seen": time.time(),
            "label_str": f"{'⚠ VPN' if result.is_vpn else '✓ Normal'} [{result.risk_level}]",
        }
        _state["total_inferences"] += 1
        if result.is_vpn:
            _state["vpn_detected_count"] += 1


# ─────────────────────────────────────────────────────────────────────────────
# MOCK MODE  –  simulate traffic without tshark
# ─────────────────────────────────────────────────────────────────────────────

def _mock_loop(engine: VPNInferenceEngine, device_labels: Dict[str, str]):
    """
    Generate synthetic CapturedPacket objects and feed them through the
    real feature extractor + real ML model, then update shared state.

    This produces realistic-looking output even without live capture.
    """
    extractor = FlowFeatureExtractor()
    device_ips = list(device_labels.keys()) or ["10.0.0.1", "10.0.0.2", "10.0.0.3"]

    # Assign each IP a random VPN state (toggle occasionally)
    vpn_state: Dict[str, bool] = {ip: random.random() > 0.5 for ip in device_ips}
    toggle_counters: Dict[str, int] = {ip: 0 for ip in device_ips}

    pkt_counters: Dict[str, int] = {ip: 0 for ip in device_ips}
    byte_counters: Dict[str, int] = {ip: 0 for ip in device_ips}

    logger.info("[MockMode] Starting synthetic packet generation…")

    while _state["running"]:
        for ip in device_ips:
            # Occasionally toggle VPN state for demo effect
            toggle_counters[ip] += 1
            if toggle_counters[ip] >= random.randint(80, 200):
                vpn_state[ip] = not vpn_state[ip]
                toggle_counters[ip] = 0
                logger.info(f"[MockMode] {ip}: VPN {'ON' if vpn_state[ip] else 'OFF'}")

            is_vpn = vpn_state[ip]

            # Generate a synthetic packet
            pkt = CapturedPacket(
                timestamp=time.time(),
                src_ip=ip,
                dst_ip=f"93.{random.randint(100,200)}.{random.randint(1,255)}.1",
                src_port=random.randint(1024, 65535),
                dst_port=443 if not is_vpn else random.choice([1194, 51820, 4500, 500, 8888]),
                protocol=random.choices(["TCP", "UDP"], weights=[0.7, 0.3])[0],
                # VPN traffic tends to have more uniform packet sizes
                length=(
                    random.randint(1350, 1500) if is_vpn
                    else random.choice([64, 128, 512, 1024, 1400])
                ),
                raw_layer="TLS" if not is_vpn else "UDP",
            )
            extractor.process(pkt)
            pkt_counters[ip] += 1
            byte_counters[ip] += pkt.length

            # Run inference when window ready
            fv = extractor.get_feature_vector(ip)
            if fv is not None:
                result = engine.predict(fv, src_ip=ip)
                if result:
                    _update_device_state(
                        ip=ip,
                        result=result,
                        label=device_labels.get(ip, "Unknown"),
                        pkt_rate=pkt_counters[ip] / max(1, time.time() - _state["start_time"]),
                        total_packets=pkt_counters[ip],
                        total_bytes=byte_counters[ip],
                    )

                    # Console output
                    vpn_tag = "🔴 VPN" if result.is_vpn else "🟢 Normal"
                    print(
                        f"  Device: {device_labels.get(ip, ip):20s}  "
                        f"IP: {ip:16s}  "
                        f"{vpn_tag}  "
                        f"Risk: {result.risk_score:3d}  "
                        f"Conf: {result.confidence:.0%}  "
                        f"[{result.risk_level}]"
                    )

        _write_state()
        time.sleep(0.1)  # 100ms tick → ~10 updates/sec


# ─────────────────────────────────────────────────────────────────────────────
# LIVE MODE  –  real packets from tshark
# ─────────────────────────────────────────────────────────────────────────────

def _inference_loop(
    packet_queue: queue.Queue,
    extractor: FlowFeatureExtractor,
    engine: VPNInferenceEngine,
    device_labels: Dict[str, str],
    capture_engine: PacketCaptureEngine,
):
    """
    Poll the capture queue, feed packets into the extractor,
    and run inference on any IP that has a ready feature window.
    """
    pkt_counters: Dict[str, int] = {}
    byte_counters: Dict[str, int] = {}

    logger.info("[InferenceLoop] Started")

    while _state["running"]:
        # Drain up to 100 packets per tick (non-blocking)
        drained = 0
        while drained < 100:
            try:
                pkt: CapturedPacket = packet_queue.get_nowait()
            except queue.Empty:
                break

            extractor.process(pkt)
            ip = pkt.src_ip
            pkt_counters[ip] = pkt_counters.get(ip, 0) + 1
            byte_counters[ip] = byte_counters.get(ip, 0) + pkt.length
            drained += 1

        # Run inference for all IPs with a ready window
        for ip in extractor.get_all_ready_ips():
            fv = extractor.get_feature_vector(ip)
            if fv is None:
                continue

            result = engine.predict(fv, src_ip=ip)
            if result is None:
                continue

            elapsed = time.time() - _state["start_time"]
            pkt_rate = pkt_counters.get(ip, 0) / max(1.0, elapsed)

            _update_device_state(
                ip=ip,
                result=result,
                label=device_labels.get(ip, "Unknown Device"),
                pkt_rate=pkt_rate,
                total_packets=pkt_counters.get(ip, 0),
                total_bytes=byte_counters.get(ip, 0),
            )

            vpn_tag = "🔴 VPN" if result.is_vpn else "🟢 Normal"
            print(
                f"  Device: {device_labels.get(ip, ip):20s}  "
                f"IP: {ip:16s}  "
                f"{vpn_tag}  "
                f"Risk: {result.risk_score:3d}  "
                f"Conf: {result.confidence:.0%}  "
                f"[{result.risk_level}]"
            )

        _write_state()
        extractor.purge_stale_flows()
        time.sleep(0.05)  # 50ms loop = ~20 inference ticks/sec


# ─────────────────────────────────────────────────────────────────────────────
# Entry-point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="VPN Detection Demo – real-time pipeline on macOS"
    )
    parser.add_argument("--interface", default="en0",
                        help="Network interface to capture on (default: en0)")
    parser.add_argument("--filter-ip", default="",
                        help="Capture only this source IP (BPF host filter)")
    parser.add_argument("--mock", action="store_true",
                        help="Run in mock/demo mode (no tshark needed)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # ── Announce available interfaces ──────────────────────────────────────
    print("\n" + "═" * 60)
    print("  VPN Detection & Deanonymisation – Real-Time Pipeline")
    print("═" * 60)
    ifaces = list_interfaces()
    print(f"  Available interfaces: {ifaces}")
    print(f"  Local IP:             {detect_local_ip()}")
    print(f"  Mode:                 {'MOCK/DEMO' if args.mock else 'LIVE CAPTURE'}")
    if not args.mock:
        print(f"  Interface:            {args.interface}")
        if args.filter_ip:
            print(f"  Filter IP:            {args.filter_ip}")
    print("═" * 60 + "\n")

    # ── Load ML model ──────────────────────────────────────────────────────
    print("[1/4] Loading ML model…")
    engine = VPNInferenceEngine()
    if not engine.load():
        print("  ⚠  Model load failed – inference results will use fallback scoring.")
    else:
        print("  ✓  RandomForest model loaded.")

    # ── Device discovery ───────────────────────────────────────────────────
    print("[2/4] Scanning local network devices…")
    devices = scan_local_devices()
    gateway = get_gateway_ip()
    device_labels: Dict[str, str] = {d.ip: d.label for d in devices}
    print(f"  ✓  Detected {len(devices)} device(s):")
    for d in devices:
        print(f"       {d.ip:16s}  [{d.label}]")

    # Update shared state
    with _state_lock:
        _state["gateway_ip"] = gateway
        _state["capture_interface"] = args.interface
        _state["mock_mode"] = args.mock

    # ── Start pipeline ─────────────────────────────────────────────────────
    print("[3/4] Starting capture & inference pipeline…")

    if args.mock:
        # Use synthetic IPs that look like a small LAN
        mock_devices = {
            "10.0.0.2": "Mobile (iPhone)",
            "10.0.0.3": "Laptop (MacBook)",
            "10.0.0.4": "Tablet (iPad)",
        }
        device_labels.update(mock_devices)
        _state["local_ip"] = "10.0.0.1"
        t = threading.Thread(
            target=_mock_loop,
            args=(engine, mock_devices),
            name="MockLoop",
            daemon=True,
        )
        t.start()
        print("  ✓  Mock loop started (no tshark required).")
    else:
        # Live capture
        bpf = f"host {args.filter_ip}" if args.filter_ip else "ip"
        capture = PacketCaptureEngine(interface=args.interface, bpf_filter=bpf)
        extractor = FlowFeatureExtractor()

        capture.start()

        inf_thread = threading.Thread(
            target=_inference_loop,
            args=(capture.packet_queue, extractor, engine, device_labels, capture),
            name="InferenceLoop",
            daemon=True,
        )
        inf_thread.start()
        print(f"  ✓  Live capture on {args.interface} (filter: '{bpf}')")
        print("  ✓  Inference loop running.")

    print("[4/4] Pipeline active. Press Ctrl-C to stop.\n")
    print(f"  Dashboard: run  streamlit run vpn_detection_demo/dashboard/app.py")
    print(f"  State file: {STATE_FILE}\n")

    # ── Keep main thread alive ─────────────────────────────────────────────
    try:
        while True:
            time.sleep(2)
            with _state_lock:
                n_devices = len(_state["devices"])
                total_inf = _state["total_inferences"]
                vpn_cnt   = _state["vpn_detected_count"]
            logger.info(
                f"Pipeline heartbeat: devices={n_devices}, "
                f"inferences={total_inf}, vpn_detected={vpn_cnt}"
            )
    except KeyboardInterrupt:
        print("\n[!] Shutting down pipeline…")
        with _state_lock:
            _state["running"] = False
        _write_state()
        print("  ✓  Done.")


if __name__ == "__main__":
    main()
