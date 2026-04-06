"""
capture/packet_capture.py
--------------------------
Real-time live packet capture for macOS (Apple Silicon compatible).

Uses PyShark (backed by tshark) to capture packets from a given interface
and pushes them into a thread-safe queue for the feature extractor to consume.

Supports:
- en0 (WiFi), bridge100 (Internet Sharing / Hotspot)
- Per-device IP filtering
- Non-blocking threaded capture
"""

import threading
import queue
import time
import logging
import socket
import subprocess
from typing import Optional, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data contract: one packet pushed into the shared queue
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Helper – macOS interface discovery
# ---------------------------------------------------------------------------

def list_interfaces() -> List[str]:
    """Return available network interfaces using tshark (macOS)."""
    try:
        out = subprocess.check_output(
            ["tshark", "-D"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        ifaces = []
        for line in out.strip().splitlines():
            # tshark -D output: "1. en0 (Wi-Fi)"
            parts = line.split(". ", 1)
            if len(parts) == 2:
                iface_name = parts[1].split(" ")[0]
                ifaces.append(iface_name)
        return ifaces
    except Exception as e:
        logger.warning(f"Could not list interfaces via tshark: {e}")
        return ["en0", "bridge100", "lo0"]


def detect_local_ip() -> str:
    """Best-effort: return this machine's primary LAN IP on en0."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ---------------------------------------------------------------------------
# Core capture engine
# ---------------------------------------------------------------------------

class PacketCaptureEngine:
    """
    Spawns a background thread that continuously reads packets via PyShark
    and enqueues CapturedPacket objects.

    Usage
    -----
        engine = PacketCaptureEngine(interface="en0")
        engine.start()

        while True:
            pkt = engine.packet_queue.get(timeout=5)
            ...   # hand off to feature extractor

        engine.stop()
    """

    def __init__(
        self,
        interface: str = "en0",
        bpf_filter: str = "",          # optional BPF filter string, e.g. "host 192.168.1.5"
        capture_filter: str = "",      # same as bpf_filter, kept for compat
        max_queue_size: int = 5_000,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        self.interface = interface
        self.bpf_filter = bpf_filter or capture_filter
        self.packet_queue: queue.Queue[CapturedPacket] = queue.Queue(maxsize=max_queue_size)
        self.on_error = on_error

        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Stats
        self.packets_received: int = 0
        self.packets_dropped: int = 0   # queue full
        self._start_time: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Start the capture thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Capture already running")
            return

        self._running.set()
        self._start_time = time.time()
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="PacketCapture",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"[PacketCapture] Started on interface={self.interface}, filter='{self.bpf_filter}'")

    def stop(self):
        """Signal the capture thread to stop and wait for it."""
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[PacketCapture] Stopped.")

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def packet_rate(self) -> float:
        """Packets per second since start."""
        elapsed = time.time() - self._start_time
        if elapsed <= 0 or self._start_time == 0:
            return 0.0
        return self.packets_received / elapsed

    # ------------------------------------------------------------------
    # Internal capture loop
    # ------------------------------------------------------------------

    def _capture_loop(self):
        """Main loop: opens PyShark live capture, parses each packet."""
        try:
            import pyshark  # lazy import — not needed for imports

            kwargs = dict(interface=self.interface, use_json=True, include_raw=False)
            if self.bpf_filter:
                kwargs["bpf_filter"] = self.bpf_filter

            capture = pyshark.LiveCapture(**kwargs)

            for raw_pkt in capture.sniff_continuously():
                if not self._running.is_set():
                    break

                parsed = self._parse_packet(raw_pkt)
                if parsed is None:
                    continue

                try:
                    self.packet_queue.put_nowait(parsed)
                    self.packets_received += 1
                except queue.Full:
                    self.packets_dropped += 1

        except Exception as exc:
            logger.error(f"[PacketCapture] Fatal error in capture loop: {exc}")
            if self.on_error:
                self.on_error(exc)

    # ------------------------------------------------------------------
    # Packet parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_packet(raw_pkt) -> Optional[CapturedPacket]:
        """Convert a PyShark packet to a CapturedPacket. Returns None on failure."""
        try:
            pkt = CapturedPacket()
            pkt.timestamp = float(raw_pkt.sniff_timestamp)
            pkt.length = int(raw_pkt.length)

            # Highest transport layer name
            pkt.raw_layer = raw_pkt.highest_layer

            # IP layer
            if hasattr(raw_pkt, "ip"):
                pkt.src_ip = raw_pkt.ip.src
                pkt.dst_ip = raw_pkt.ip.dst

            # Transport layer (TCP / UDP)
            if hasattr(raw_pkt, "tcp"):
                pkt.protocol = "TCP"
                pkt.src_port = int(raw_pkt.tcp.srcport)
                pkt.dst_port = int(raw_pkt.tcp.dstport)
            elif hasattr(raw_pkt, "udp"):
                pkt.protocol = "UDP"
                pkt.src_port = int(raw_pkt.udp.srcport)
                pkt.dst_port = int(raw_pkt.udp.dstport)
            elif hasattr(raw_pkt, "icmp"):
                pkt.protocol = "ICMP"
            else:
                pkt.protocol = raw_pkt.highest_layer

            return pkt

        except Exception as e:
            logger.debug(f"[PacketCapture] Could not parse packet: {e}")
            return None


# ---------------------------------------------------------------------------
# Demo / standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    ifaces = list_interfaces()
    print(f"Available interfaces: {ifaces}")
    local_ip = detect_local_ip()
    print(f"Local IP: {local_ip}")

    engine = PacketCaptureEngine(interface="en0", bpf_filter="ip")
    engine.start()

    print("Capturing for 10 seconds…")
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            pkt = engine.packet_queue.get(timeout=1)
            print(f"  {pkt.src_ip}:{pkt.src_port} → {pkt.dst_ip}:{pkt.dst_port}  [{pkt.protocol}] {pkt.length}B")
        except queue.Empty:
            pass

    engine.stop()
    print(f"Total received={engine.packets_received}, dropped={engine.packets_dropped}, rate={engine.packet_rate:.1f} pkt/s")
