import datetime
from collections import defaultdict
import numpy as np

class FlowTracker:
    def __init__(self, max_window=50):
        self.max_window = max_window
        # State tracking: mapping flow_id -> flow dictionary
        self.flows = defaultdict(lambda: {
            "src_ip": None,
            "dst_ip": None,
            "src_port": None,
            "dst_port": None,
            "protocol": None,
            "packets": [],     # Stores basic packet metadata (size, time)
            "start_time": None,
            "last_time": None,
            "fwd_count": 0,
            "bwd_count": 0,
            "fwd_bytes": 0,
            "bwd_bytes": 0
        })

    def get_flow_id(self, src_ip, src_port, dst_ip, dst_port, protocol):
        """Creates a bidirectional flow ID"""
        # Sort endpoints so A->B and B->A map to the same flow context if needed,
        # but typically ISCX separates Fwd vs Bwd based on initiator. 
        # For simplicity, initiator is whoever sends the first packet.
        ep1 = f"{src_ip}:{src_port}"
        ep2 = f"{dst_ip}:{dst_port}"
        if ep1 < ep2:
            return f"{protocol}-{ep1}-{ep2}"
        return f"{protocol}-{ep2}-{ep1}"

    def process_packet(self, packet):
        try:
            # Extract basic IP info
            if hasattr(packet, 'ip'):
                src_ip = packet.ip.src
                dst_ip = packet.ip.dst
            elif hasattr(packet, 'ipv6'):
                src_ip = packet.ipv6.src
                dst_ip = packet.ipv6.dst
            else:
                return None # Skip non-IP
                
            protocol = "UNKNOWN"
            src_port = 0
            dst_port = 0
            
            if hasattr(packet, 'tcp'):
                protocol = "TCP"
                src_port = int(packet.tcp.srcport)
                dst_port = int(packet.tcp.dstport)
            elif hasattr(packet, 'udp'):
                protocol = "UDP"
                src_port = int(packet.udp.srcport)
                dst_port = int(packet.udp.dstport)
            else:
                # Not TCP or UDP payload
                return None
                
            # Filter local traffic to our UI so we don't recursive loop
            if dst_port in [8080, 5173] or src_port in [8080, 5173]:
                return None

            length = int(packet.length)
            timestamp = float(packet.sniff_timestamp)
            
            flow_id = self.get_flow_id(src_ip, src_port, dst_ip, dst_port, protocol)
            flow = self.flows[flow_id]
            
            # Initialization
            if flow["src_ip"] is None:
                flow["src_ip"] = src_ip
                flow["dst_ip"] = dst_ip
                flow["src_port"] = src_port
                flow["dst_port"] = dst_port
                flow["protocol"] = protocol
                flow["start_time"] = timestamp
            
            flow["last_time"] = timestamp
            
            # FWD vs BWD 
            is_fwd = (src_ip == flow["src_ip"])
            if is_fwd:
                flow["fwd_count"] += 1
                flow["fwd_bytes"] += length
            else:
                flow["bwd_count"] += 1
                flow["bwd_bytes"] += length
                
            # Keep rolling window
            flow["packets"].append({
                "len": length,
                "time": timestamp,
                "is_fwd": is_fwd
            })
            
            if len(flow["packets"]) > self.max_window:
                flow["packets"].pop(0)
                
            # Once we hit a threshold, we compute and trigger inference
            # (e.g., every 10 packets, return features)
            if len(flow["packets"]) >= 10 and len(flow["packets"]) % 10 == 0:
                return self.extract_features(flow_id)
                
        except Exception as e:
            pass # Ignore malformed packets dynamically
            
        return None

    def extract_features(self, flow_id):
        flow = self.flows[flow_id]
        pkts = flow["packets"]
        
        if len(pkts) < 2:
            return None
            
        lengths = [p["len"] for p in pkts]
        fwd_lengths = [p["len"] for p in pkts if p["is_fwd"]]
        bwd_lengths = [p["len"] for p in pkts if not p["is_fwd"]]
        
        # Inter-arrival times
        iats = [pkts[i]["time"] - pkts[i-1]["time"] for i in range(1, len(pkts))]
        flow_duration = pkts[-1]["time"] - pkts[0]["time"]
        
        # Compute exact ISCX/CICFlowMeter equivalents
        features = {}
        features["Flow Duration"] = flow_duration * 1e6 # in microseconds
        features["Total Fwd Packets"] = flow["fwd_count"]
        features["Total Backward Packets"] = flow["bwd_count"]
        features["Total Length of Fwd Packets"] = flow["fwd_bytes"]
        features["Total Length of Bwd Packets"] = flow["bwd_bytes"]
        
        if fwd_lengths:
            features["Fwd Packet Length Max"] = max(fwd_lengths)
            features["Fwd Packet Length Min"] = min(fwd_lengths)
            features["Fwd Packet Length Mean"] = np.mean(fwd_lengths)
            features["Fwd Packet Length Std"] = np.std(fwd_lengths)
        else:
            features["Fwd Packet Length Max"] = 0
            features["Fwd Packet Length Min"] = 0
            features["Fwd Packet Length Mean"] = 0.0
            features["Fwd Packet Length Std"] = 0.0
            
        if bwd_lengths:
            features["Bwd Packet Length Max"] = max(bwd_lengths)
            features["Bwd Packet Length Min"] = min(bwd_lengths)
            features["Bwd Packet Length Mean"] = np.mean(bwd_lengths)
            features["Bwd Packet Length Std"] = np.std(bwd_lengths)
        else:
            features["Bwd Packet Length Max"] = 0
            features["Bwd Packet Length Min"] = 0
            features["Bwd Packet Length Mean"] = 0.0
            features["Bwd Packet Length Std"] = 0.0
            
        if iats:
            features["Flow IAT Mean"] = np.mean(iats) * 1e6
            features["Flow IAT Std"] = np.std(iats) * 1e6
            features["Flow IAT Max"] = max(iats) * 1e6
            features["Flow IAT Min"] = min(iats) * 1e6
        else:
            features["Flow IAT Mean"] = 0.0
            features["Flow IAT Std"] = 0.0
            features["Flow IAT Max"] = 0.0
            features["Flow IAT Min"] = 0.0

        features["Packet Length Mean"] = np.mean(lengths)
        features["Packet Length Std"] = np.std(lengths)
        features["Packet Length Variance"] = np.var(lengths)
        
        if flow_duration > 0:
            features["Flow Bytes/s"] = sum(lengths) / flow_duration
            features["Flow Packets/s"] = len(lengths) / flow_duration
        else:
            features["Flow Bytes/s"] = 0.0
            features["Flow Packets/s"] = 0.0
            
        return {
            "src_ip": flow["src_ip"],
            "dst_ip": flow["dst_ip"],
            "src_port": flow["src_port"],
            "dst_port": flow["dst_port"],
            "protocol": flow["protocol"],
            "raw_features": features,    # Computed mathematical features
            "packet_count": len(lengths)
        }
