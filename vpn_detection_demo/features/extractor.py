"""
features/extractor.py
----------------------
Flow-based feature extraction over a sliding window of packets.

The model (vpn_classifier.joblib) was trained on 11 features:
    [0]  mean_pkt_size        – mean packet length in flow
    [1]  std_pkt_size         – std dev of packet length
    [2]  min_pkt_size         – min packet length
    [3]  max_pkt_size         – max packet length
    [4]  mean_iat             – mean inter-arrival time (seconds)
    [5]  std_iat              – std dev of inter-arrival time
    [6]  flow_duration        – total flow duration (seconds)
    [7]  total_bytes          – bytes in window
    [8]  packet_count         – number of packets in window
    [9]  tcp_ratio            – fraction of TCP packets
    [10] udp_ratio            – fraction of UDP packets

Features are computed over a configurable sliding window (default: 50 packets).
"""

import collections
import math
import time
import threading
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Deque

# Support both package import and direct execution
try:
    from capture.capture_types import CapturedPacket
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from capture.capture_types import CapturedPacket

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WINDOW_SIZE = 50       # number of packets per feature window
N_FEATURES  = 11       # must match model expectation

FEATURE_NAMES = [
    "mean_pkt_size",
    "std_pkt_size",
    "min_pkt_size",
    "max_pkt_size",
    "mean_iat",
    "std_iat",
    "flow_duration",
    "total_bytes",
    "packet_count",
    "tcp_ratio",
    "udp_ratio",
]


# ---------------------------------------------------------------------------
# Per-source-IP flow state
# ---------------------------------------------------------------------------

@dataclass
class FlowRecord:
    """Keeps a rolling window of packet data for a single src_ip."""
    src_ip: str
    window: Deque[CapturedPacket] = field(default_factory=lambda: collections.deque(maxlen=WINDOW_SIZE))
    last_seen: float = field(default_factory=time.time)

    # cumulative counters (survive beyond the window)
    total_packets: int = 0
    total_bytes: int = 0

    def add(self, pkt: CapturedPacket):
        self.window.append(pkt)
        self.last_seen = pkt.timestamp
        self.total_packets += 1
        self.total_bytes += pkt.length

    @property
    def is_ready(self) -> bool:
        """True once enough packets accumulated for a feature window."""
        return len(self.window) >= WINDOW_SIZE


# ---------------------------------------------------------------------------
# Feature vector computation
# ---------------------------------------------------------------------------

def _safe_std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def compute_features(record: FlowRecord) -> Optional[np.ndarray]:
    """
    Compute the 11-feature vector from the current sliding window.

    Returns None if window is not ready yet.
    """
    pkts = list(record.window)
    n = len(pkts)

    if n < 2:
        return None

    sizes = [p.length for p in pkts]
    timestamps = [p.timestamp for p in pkts]

    # Inter-arrival times
    iats = [timestamps[i] - timestamps[i - 1] for i in range(1, n)]
    # Clip negatives that can arise from clock issues
    iats = [max(0.0, t) for t in iats]

    # Duration
    flow_duration = timestamps[-1] - timestamps[0]
    if flow_duration < 0:
        flow_duration = 0.0

    # Protocol ratios
    tcp_count = sum(1 for p in pkts if p.protocol == "TCP")
    udp_count = sum(1 for p in pkts if p.protocol == "UDP")
    tcp_ratio = tcp_count / n
    udp_ratio = udp_count / n

    mean_size  = float(np.mean(sizes))
    std_size   = float(np.std(sizes)) if n > 1 else 0.0
    min_size   = float(min(sizes))
    max_size   = float(max(sizes))
    mean_iat   = float(np.mean(iats)) if iats else 0.0
    std_iat    = float(np.std(iats))  if len(iats) > 1 else 0.0
    total_bytes= float(sum(sizes))

    features = np.array([
        mean_size,
        std_size,
        min_size,
        max_size,
        mean_iat,
        std_iat,
        flow_duration,
        total_bytes,
        float(n),
        tcp_ratio,
        udp_ratio,
    ], dtype=np.float32)

    assert len(features) == N_FEATURES, f"Expected {N_FEATURES} features, got {len(features)}"
    return features


# ---------------------------------------------------------------------------
# Real-time feature extractor (thread-safe)
# ---------------------------------------------------------------------------

class FlowFeatureExtractor:
    """
    Maintains per-IP flow records.  Feed packets via `process()`.
    Call `get_feature_vector(ip)` to retrieve the latest feature vector.

    Thread-safe for concurrent packet feeds and model inference queries.
    """

    def __init__(self, window_size: int = WINDOW_SIZE, flow_timeout_sec: float = 60.0):
        self.window_size = window_size
        self.flow_timeout_sec = flow_timeout_sec
        self._flows: Dict[str, FlowRecord] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Feed packets
    # ------------------------------------------------------------------

    def process(self, pkt: CapturedPacket):
        """Insert a packet into the appropriate per-IP flow record."""
        if not pkt.src_ip:
            return

        with self._lock:
            rec = self._flows.setdefault(pkt.src_ip, FlowRecord(src_ip=pkt.src_ip))
            rec.add(pkt)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_feature_vector(self, ip: str) -> Optional[np.ndarray]:
        """Return 11-feature vector for a given IP, or None if not ready."""
        with self._lock:
            rec = self._flows.get(ip)
            if rec is None:
                return None
            return compute_features(rec)

    def get_all_ready_ips(self) -> List[str]:
        """Return list of IPs that have a full feature window."""
        with self._lock:
            return [ip for ip, rec in self._flows.items() if rec.is_ready]

    def get_flow_summary(self, ip: str) -> Optional[Dict]:
        """Return a human-readable summary dict for a given IP."""
        with self._lock:
            rec = self._flows.get(ip)
            if rec is None:
                return None
            return {
                "src_ip": rec.src_ip,
                "window_size": len(rec.window),
                "total_packets": rec.total_packets,
                "total_bytes": rec.total_bytes,
                "last_seen": rec.last_seen,
            }

    def known_ips(self) -> List[str]:
        """All IPs we have seen at least one packet from."""
        with self._lock:
            return list(self._flows.keys())

    def purge_stale_flows(self):
        """Remove flows that have been idle for longer than `flow_timeout_sec`."""
        now = time.time()
        with self._lock:
            stale = [
                ip for ip, rec in self._flows.items()
                if now - rec.last_seen > self.flow_timeout_sec
            ]
            for ip in stale:
                del self._flows[ip]
            if stale:
                logger.debug(f"[FlowFeatureExtractor] Purged stale flows: {stale}")



