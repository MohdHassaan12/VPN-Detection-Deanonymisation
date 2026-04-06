"""
capture/capture_types.py
-------------------------
Shared dataclass contracts used across the capture and feature layers.
Kept in a separate file to avoid circular imports.
"""
import time
from dataclasses import dataclass, field


@dataclass
class CapturedPacket:
    """Lightweight, serialisable representation of a captured packet."""
    timestamp: float = field(default_factory=time.time)
    src_ip: str = ""
    dst_ip: str = ""
    src_port: int = 0
    dst_port: int = 0
    protocol: str = "UNKNOWN"   # TCP / UDP / ICMP / ARP …
    length: int = 0             # total wire length in bytes
    raw_layer: str = ""         # highest-layer name (e.g. "TLS", "HTTP", "DNS")
