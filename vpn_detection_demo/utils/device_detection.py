"""
utils/device_detection.py
--------------------------
Detect local network devices on macOS using ARP + psutil.

Provides:
    - scan_local_devices()     → List[DeviceInfo]
    - label_device(ip)         → "Mobile" | "Laptop" | "Router" | "Unknown"
    - get_gateway_ip()          → str
    - get_local_network_prefix() → str  (e.g. "192.168.1.")
"""

import re
import socket
import subprocess
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Device info dataclass
# ---------------------------------------------------------------------------

@dataclass
class DeviceInfo:
    """Represents a detected network device."""
    ip: str
    mac: str = ""
    hostname: str = ""
    label: str = "Unknown"          # "Mobile" | "Laptop" | "Router" | "Gateway" | "This Device"
    is_local: bool = True           # True if on LAN
    first_seen: float = 0.0
    last_seen: float = 0.0
    total_packets: int = 0
    total_bytes: int = 0

    @property
    def display_name(self) -> str:
        if self.hostname and self.hostname != self.ip:
            return f"{self.hostname} ({self.ip})"
        return self.ip


# ---------------------------------------------------------------------------
# macOS ARP scanner
# ---------------------------------------------------------------------------

def _parse_arp_output(raw: str) -> List[Dict[str, str]]:
    """
    Parse `arp -a` output on macOS.

    Example line:
        MacBook-Air.local (192.168.1.3) at a4:83:e7:xx:yy:zz on en0 ifscope [ethernet]
    """
    entries = []
    pattern = re.compile(
        r"(?P<hostname>\S+)\s+\((?P<ip>[\d.]+)\)\s+at\s+(?P<mac>[0-9a-f:]+)",
        re.IGNORECASE,
    )
    for line in raw.splitlines():
        m = pattern.search(line)
        if m:
            entries.append({
                "hostname": m.group("hostname").rstrip("."),
                "ip": m.group("ip"),
                "mac": m.group("mac"),
            })
    return entries


def _run_arp() -> str:
    """Run `arp -a` and return stdout."""
    try:
        return subprocess.check_output(["arp", "-a"], stderr=subprocess.DEVNULL, text=True, timeout=5)
    except Exception as e:
        logger.debug(f"arp -a failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# Gateway / network info (macOS)
# ---------------------------------------------------------------------------

def get_gateway_ip() -> str:
    """Parse `netstat -rn` to find the default gateway IP."""
    try:
        out = subprocess.check_output(["netstat", "-rn"], stderr=subprocess.DEVNULL, text=True, timeout=5)
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0] in ("default", "0.0.0.0/0"):
                # Second column is typically the gateway
                if len(parts) >= 2 and re.match(r"\d+\.\d+\.\d+\.\d+", parts[1]):
                    return parts[1]
    except Exception as e:
        logger.debug(f"get_gateway_ip failed: {e}")
    return ""


def get_local_ip() -> str:
    """Best-effort local primary IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_local_network_prefix() -> str:
    """Return first three octets of local IP (e.g. '192.168.1.')"""
    ip = get_local_ip()
    parts = ip.rsplit(".", 1)
    return parts[0] + "." if len(parts) == 2 else "192.168.1."


# ---------------------------------------------------------------------------
# Heuristic device labeller
# ---------------------------------------------------------------------------

# OUI prefix → likely device type
_OUI_HINTS: Dict[str, str] = {
    "a4:83:e7": "Apple",
    "f0:18:98": "Apple",
    "7c:d9:5c": "Samsung Mobile",
    "34:02:86": "Samsung Mobile",
    "dc:a6:32": "Raspberry Pi",
    "b8:27:eb": "Raspberry Pi",
    "00:50:56": "VMware",
    "00:0c:29": "VMware",
    "08:00:27": "VirtualBox",
}

# Hostname keywords
_HOSTNAME_MOBILE_HINTS   = {"iphone", "android", "pixel", "samsung", "oneplus", "redmi", "xiaomi"}
_HOSTNAME_LAPTOP_HINTS   = {"macbook", "laptop", "imac", "mac", "desktop", "pc", "windows", "ubuntu"}
_HOSTNAME_ROUTER_HINTS   = {"router", "gateway", "modem", "fritz", "asus-rt", "tplink", "netgear"}


def label_device(ip: str, mac: str = "", hostname: str = "", gateway_ip: str = "") -> str:
    """
    Assign a human-readable label to a device.

    Priority: explicit gateway IP → MAC OUI hints → hostname keywords → fallback
    """
    local_ip = get_local_ip()
    if ip == local_ip:
        return "This Device"
    if gateway_ip and ip == gateway_ip:
        return "Router / Gateway"

    hn = hostname.lower()
    for hint in _HOSTNAME_ROUTER_HINTS:
        if hint in hn:
            return "Router / Gateway"
    for hint in _HOSTNAME_MOBILE_HINTS:
        if hint in hn:
            return "Mobile"
    for hint in _HOSTNAME_LAPTOP_HINTS:
        if hint in hn:
            return "Laptop / Desktop"

    # MAC OUI
    if mac:
        mac_lower = mac.lower()
        for oui, label in _OUI_HINTS.items():
            if mac_lower.startswith(oui):
                return label

    return "Unknown Device"


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

def scan_local_devices() -> List[DeviceInfo]:
    """
    Scan the local network using ARP and return a list of DeviceInfo.

    On macOS this reads the ARP cache (fast, no root needed).
    Typically refreshed automatically as network traffic flows.
    """
    import time
    gateway = get_gateway_ip()
    raw = _run_arp()
    entries = _parse_arp_output(raw)

    devices: List[DeviceInfo] = []
    seen_ips = set()

    for entry in entries:
        ip  = entry["ip"]
        mac = entry["mac"]
        hn  = entry["hostname"]

        # Skip duplicates, broadcast addresses, multicast
        if ip in seen_ips:
            continue
        if ip.endswith(".255") or ip.startswith("224.") or ip.startswith("239."):
            continue

        seen_ips.add(ip)
        lbl = label_device(ip, mac, hn, gateway)

        devices.append(DeviceInfo(
            ip=ip,
            mac=mac,
            hostname=hn,
            label=lbl,
            first_seen=time.time(),
            last_seen=time.time(),
        ))

    # Always include "This Device"
    local_ip = get_local_ip()
    if local_ip not in seen_ips:
        devices.insert(0, DeviceInfo(
            ip=local_ip,
            hostname=socket.gethostname(),
            label="This Device",
            first_seen=time.time(),
            last_seen=time.time(),
        ))

    logger.info(f"[DeviceDetection] Found {len(devices)} device(s): {[d.ip for d in devices]}")
    return devices


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"Local IP:      {get_local_ip()}")
    print(f"Gateway IP:    {get_gateway_ip()}")
    print(f"Network Prefix:{get_local_network_prefix()}")
    print("\nARP Scan results:")
    for d in scan_local_devices():
        print(f"  [{d.label:20s}] {d.ip:16s}  MAC={d.mac:20s}  Host={d.hostname}")
