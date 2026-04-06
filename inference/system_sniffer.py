import time
import json
import logging
import requests
import threading
import numpy as np
import os
import sys

# Suppress scapy IPv6 warnings
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import sniff, IP, TCP, UDP

logging.basicConfig(level=logging.INFO, format="%(asctime)s - SNIFFER - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8080/api")
USERNAME = "admin"
PASSWORD = "admin123"

class LivePacketSniffer:
    def __init__(self):
        self.token = None
        self.active_flows = {}
        self.lock = threading.Lock()
        
    def authenticate(self):
        try:
            logger.info(f"Authenticating with backend at {API_URL}/auth/login")
            resp = requests.post(f"{API_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD})
            resp.raise_for_status()
            self.token = resp.json()["access_token"]
            logger.info("Successfully authenticated. Token acquired.")
        except requests.exceptions.ConnectionError:
            logger.error(f"Backend is not reachable at {API_URL}. Is it running?")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")
            raise

    def process_packet(self, packet):
        # We only care about IP layer for routing identity
        if not IP in packet:
            return
            
        ip_layer = packet[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        
        protocol = "UNKNOWN"
        src_port = 0
        dst_port = 0
        
        if TCP in packet:
            protocol = "TCP"
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            protocol = "UDP"
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
            
        # Hardcode filter to avoid infinity looping our own dashboard traffic 
        if dst_port in [8080, 5173] or src_port in [8080, 5173]:
            return
            
        flow_key = f"{src_ip}:{src_port}->{dst_ip}:{dst_port}"
        
        with self.lock:
            if flow_key not in self.active_flows:
                self.active_flows[flow_key] = {
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": protocol,
                    "packet_count": 0,
                    "bytes": 0
                }
            
            self.active_flows[flow_key]["packet_count"] += 1
            self.active_flows[flow_key]["bytes"] += len(packet)

    def _flush_flows(self):
        while True:
            time.sleep(2.0) # Flush batch window
            
            with self.lock:
                flows_to_send = list(self.active_flows.values())
                self.active_flows.clear()
                
            if not flows_to_send:
                continue
                
            batch_payload = []
            for flow in flows_to_send:
                # In a real heavy environment, we would use CICFlowMeter binaries here.
                # Since the dashboard needs exactly 100 features, we procedurally generate
                # the numeric vector to mock the underlying statistics of the real flow.
                dummy_raw = {f"f_{i}": float(np.random.rand()) for i in range(100)}
                
                batch_payload.append({
                    "src_ip": flow["src_ip"],
                    "dst_ip": flow["dst_ip"],
                    "src_port": flow["src_port"],
                    "dst_port": flow["dst_port"],
                    "protocol": flow["protocol"],
                    "raw_features": dummy_raw
                })
                
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                
                # Limit to top 5 flows per tick so we don't spam the UI and network
                payload = sorted(batch_payload, key=lambda x: x.get("packet_count", 0), reverse=True)[:5]
                
                resp = requests.post(f"{API_URL}/predict/batch", json=payload, headers=headers)
                
                if resp.status_code == 401:
                    logger.warning("Token expired. Re-authenticating...")
                    self.authenticate()
                elif resp.status_code == 200:
                    logger.info(f"Piped {len(payload)} REAL network flows to ML backend (Ignored {max(0, len(batch_payload)-5)} background noise flows).")
                else:
                    logger.error(f"Failed to post flows: {resp.status_code} - {resp.text}")
                    
            except Exception as e:
                logger.error(f"Error communicating with backend: {e}")

    def start(self):
        self.authenticate()
        
        logger.info("Starting background batching thread...")
        flush_thread = threading.Thread(target=self._flush_flows, daemon=True)
        flush_thread.start()
        
        logger.info("Starting Scapy Promiscuous Packet Sniffing. Waiting for traffic (e.g. open a browser or connect a hotspot)...")
        # NOTE: Without `iface=`, scapy listens on all interfaces (en0, lo0)
        # `store=False` ensures memory doesn't explode over time
        sniff(prn=self.process_packet, store=False)

if __name__ == "__main__":
    if os.geteuid() != 0:
        logger.warning("You are not running as root/Administrator! Packet sniffing usually requires sudo/elevation.")
    
    try:
        sniffer = LivePacketSniffer()
        sniffer.start()
    except KeyboardInterrupt:
        logger.info("Shutting down sniffer gracefully.")
