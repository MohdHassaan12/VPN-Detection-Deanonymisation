"""
PCAP to Flow Converter using Scapy
Processes PCAP files and extracts network flow features
Alternative to NFStream for environments where NFStream cannot be installed
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from collections import defaultdict
import numpy as np
from datetime import datetime

try:
    from scapy.all import rdpcap, IP, IPv6, TCP, UDP, ICMP
except ImportError:
    print("ERROR: Scapy not installed. Install with: pip install scapy")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlowKey:
    """Represents a bidirectional flow identifier"""
    def __init__(self, src_ip, dst_ip, src_port, dst_port, protocol):
        # Normalize flow direction (smaller IP first for bidirectional matching)
        if src_ip < dst_ip:
            self.ip1, self.ip2 = src_ip, dst_ip
            self.port1, self.port2 = src_port, dst_port
            self.direction = 'fwd'
        else:
            self.ip1, self.ip2 = dst_ip, src_ip
            self.port1, self.port2 = dst_port, src_port
            self.direction = 'bwd'
        self.protocol = protocol
    
    def __hash__(self):
        return hash((self.ip1, self.ip2, self.port1, self.port2, self.protocol))
    
    def __eq__(self, other):
        return (self.ip1, self.ip2, self.port1, self.port2, self.protocol) == \
               (other.ip1, other.ip2, other.port1, other.port2, other.protocol)


class Flow:
    """Represents a network flow with statistics"""
    def __init__(self, flow_key: FlowKey, first_packet_time):
        self.flow_key = flow_key
        self.start_time = first_packet_time
        self.end_time = first_packet_time
        
        # Packet and byte counts (bidirectional)
        self.packets_fwd = 0
        self.packets_bwd = 0
        self.bytes_fwd = 0
        self.bytes_bwd = 0
        
        # Packet sizes
        self.packet_sizes_fwd = []
        self.packet_sizes_bwd = []
        
        # Inter-arrival times
        self.iat_fwd = []
        self.iat_bwd = []
        self.last_time_fwd = None
        self.last_time_bwd = None
        
        # TCP flags
        self.syn_count = 0
        self.ack_count = 0
        self.fin_count = 0
        self.rst_count = 0
        self.psh_count = 0
        
        # TCP/IP features
        self.ttl_values = []
        self.window_sizes = []
    
    def add_packet(self, packet, timestamp, direction):
        """Add a packet to the flow"""
        packet_size = len(packet)
        self.end_time = timestamp
        
        if direction == 'fwd':
            self.packets_fwd += 1
            self.bytes_fwd += packet_size
            self.packet_sizes_fwd.append(packet_size)
            
            if self.last_time_fwd is not None:
                iat = (timestamp - self.last_time_fwd).total_seconds()
                if iat >= 0:
                    self.iat_fwd.append(iat)
            self.last_time_fwd = timestamp
        else:
            self.packets_bwd += 1
            self.bytes_bwd += packet_size
            self.packet_sizes_bwd.append(packet_size)
            
            if self.last_time_bwd is not None:
                iat = (timestamp - self.last_time_bwd).total_seconds()
                if iat >= 0:
                    self.iat_bwd.append(iat)
            self.last_time_bwd = timestamp
        
        # Extract TCP flags
        if TCP in packet:
            tcp_layer = packet[TCP]
            if tcp_layer.flags:
                if tcp_layer.flags & 0x02:  # SYN
                    self.syn_count += 1
                if tcp_layer.flags & 0x10:  # ACK
                    self.ack_count += 1
                if tcp_layer.flags & 0x01:  # FIN
                    self.fin_count += 1
                if tcp_layer.flags & 0x04:  # RST
                    self.rst_count += 1
                if tcp_layer.flags & 0x08:  # PSH
                    self.psh_count += 1
            
            if tcp_layer.window:
                self.window_sizes.append(tcp_layer.window)
        
        # Extract TTL
        if IP in packet:
            self.ttl_values.append(packet[IP].ttl)
    
    def get_features(self) -> Dict:
        """Calculate flow features"""
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Basic counts
        total_packets = self.packets_fwd + self.packets_bwd
        total_bytes = self.bytes_fwd + self.bytes_bwd
        
        all_packet_sizes = self.packet_sizes_fwd + self.packet_sizes_bwd
        all_iats = self.iat_fwd + self.iat_bwd
        
        features = {
            # Flow identifiers
            'src_ip': self.flow_key.ip1,
            'dst_ip': self.flow_key.ip2,
            'src_port': self.flow_key.port1,
            'dst_port': self.flow_key.port2,
            'protocol': self.flow_key.protocol,
            
            # Temporal
            'timestamp': self.start_time,
            'flow_duration': duration,
            
            # Packet counts
            'packet_count_fwd': self.packets_fwd,
            'packet_count_bwd': self.packets_bwd,
            'packet_count_total': total_packets,
            
            # Byte counts
            'byte_count_fwd': self.bytes_fwd,
            'byte_count_bwd': self.bytes_bwd,
            'byte_count_total': total_bytes,
            
            # Packet size statistics
            'packet_length_min': min(all_packet_sizes) if all_packet_sizes else 0,
            'packet_length_max': max(all_packet_sizes) if all_packet_sizes else 0,
            'packet_length_mean': np.mean(all_packet_sizes) if all_packet_sizes else 0,
            'packet_length_std': np.std(all_packet_sizes) if all_packet_sizes else 0,
            'packet_length_variance': np.var(all_packet_sizes) if all_packet_sizes else 0,
            
            # Inter-arrival time statistics
            'mean_iat_fwd': np.mean(self.iat_fwd) if self.iat_fwd else 0,
            'mean_iat_bwd': np.mean(self.iat_bwd) if self.iat_bwd else 0,
            'mean_iat_total': np.mean(all_iats) if all_iats else 0,
            'std_iat_fwd': np.std(self.iat_fwd) if self.iat_fwd else 0,
            'std_iat_bwd': np.std(self.iat_bwd) if self.iat_bwd else 0,
            'std_iat_total': np.std(all_iats) if all_iats else 0,
            'min_iat_total': min(all_iats) if all_iats else 0,
            'max_iat_total': max(all_iats) if all_iats else 0,
            
            # Rate features
            'packets_per_second': total_packets / duration if duration > 0 else 0,
            'bytes_per_second': total_bytes / duration if duration > 0 else 0,
            
            # Ratio features
            'byte_ratio': self.bytes_fwd / self.bytes_bwd if self.bytes_bwd > 0 else 0,
            'packet_ratio': self.packets_fwd / self.packets_bwd if self.packets_bwd > 0 else 0,
            'down_up_ratio': self.bytes_bwd / self.bytes_fwd if self.bytes_fwd > 0 else 0,
            
            # TCP flags
            'syn_flag_count': self.syn_count,
            'ack_flag_count': self.ack_count,
            'fin_flag_count': self.fin_count,
            'rst_flag_count': self.rst_count,
            'psh_flag_count': self.psh_count,
            
            # TCP/IP features (for VPN detection)
            'ttl': int(np.mean(self.ttl_values)) if self.ttl_values else -1,
            'window_size': int(np.mean(self.window_sizes)) if self.window_sizes else -1,
            
            # Placeholder features (not available from basic PCAP parsing)
            'active_mean': 0,
            'active_std': 0,
            'idle_mean': 0,
            'idle_std': 0,
            'mtu': -1,
            'mss': -1,
            'tcp_options_count': 0,
            'protocol_hint': 'Unknown',
            'encryption_detected': -1,
            'entropy_score': -1.0,
            
            # Labels (to be determined)
            'app_label': 'Unknown',
            'intent_label': 'Unknown',
            'vpn_flag': -1,
        }
        
        return features


class ScapyPCAPProcessor:
    """Process PCAP files using Scapy"""
    
    def __init__(self, flow_timeout: int = 120):
        self.flow_timeout = flow_timeout
        self.flows = {}
        self.stats = {
            'total_packets': 0,
            'processed_packets': 0,
            'total_flows': 0
        }
    
    def process_pcap(self, pcap_path: str, output_csv: Optional[str] = None) -> pd.DataFrame:
        """Process a single PCAP file"""
        logger.info(f"Processing PCAP: {pcap_path}")
        
        try:
            # Read PCAP file
            logger.info("Reading PCAP file (this may take a while for large files)...")
            packets = rdpcap(pcap_path)
            logger.info(f"Loaded {len(packets)} packets")
            
            self.stats['total_packets'] = len(packets)
            
            # Process each packet
            for i, packet in enumerate(packets):
                self._process_packet(packet)
                
                if (i + 1) % 10000 == 0:
                    logger.info(f"Processed {i + 1}/{len(packets)} packets, {len(self.flows)} flows")
            
            self.stats['processed_packets'] = len(packets)
            self.stats['total_flows'] = len(self.flows)
            
            logger.info(f"Extracted {len(self.flows)} flows from {len(packets)} packets")
            
            # Convert flows to DataFrame
            flow_features = [flow.get_features() for flow in self.flows.values()]
            
            if flow_features:
                df = pd.DataFrame(flow_features)
                
                # Add metadata
                df['dataset_source'] = 'University_PCAP'
                df['source_file'] = Path(pcap_path).name
                
                # Save to CSV if output path provided
                if output_csv:
                    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
                    df.to_csv(output_csv, index=False)
                    logger.info(f"✓ Saved to {output_csv}")
                
                return df
            else:
                logger.warning(f"No flows extracted from {pcap_path}")
                return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"Error processing {pcap_path}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _process_packet(self, packet):
        """Process a single packet"""
        try:
            # Extract IP layer
            if IP in packet:
                ip_layer = packet[IP]
                src_ip = ip_layer.src
                dst_ip = ip_layer.dst
                protocol = ip_layer.proto
                
                # Get ports for TCP/UDP
                src_port = 0
                dst_port = 0
                
                if TCP in packet:
                    src_port = packet[TCP].sport
                    dst_port = packet[TCP].dport
                elif UDP in packet:
                    src_port = packet[UDP].sport
                    dst_port = packet[UDP].dport
                
                # Get timestamp
                if hasattr(packet, 'time'):
                    timestamp = datetime.fromtimestamp(float(packet.time))
                else:
                    timestamp = datetime.now()
                
                # Create flow key
                flow_key = FlowKey(src_ip, dst_ip, src_port, dst_port, protocol)
                
                # Get or create flow
                if flow_key not in self.flows:
                    self.flows[flow_key] = Flow(flow_key, timestamp)
                
                # Add packet to flow
                self.flows[flow_key].add_packet(packet, timestamp, flow_key.direction)
        
        except Exception as e:
            # Skip packets that can't be processed
            pass
    
    def process_directory(self, input_dir: str, output_dir: str, pattern: str = "*.pcapng") -> pd.DataFrame:
        """Process all PCAP files in a directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all PCAP files
        pcap_files = list(input_path.glob(pattern))
        
        # Also look for .pcap extension
        if pattern == "*.pcapng":
            pcap_files.extend(list(input_path.glob("*.pcap")))
        
        logger.info(f"Found {len(pcap_files)} PCAP file(s) in {input_dir}")
        
        all_flows = []
        
        for pcap_file in pcap_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {pcap_file.name}")
            logger.info(f"{'='*60}")
            
            # Reset flows for each file
            self.flows = {}
            
            # Generate output filename
            output_csv = output_path / f"{pcap_file.stem}_flows.csv"
            
            # Process PCAP
            df = self.process_pcap(str(pcap_file), str(output_csv))
            
            if not df.empty:
                all_flows.append(df)
        
        # Combine all flows
        if all_flows:
            combined_df = pd.concat(all_flows, ignore_index=True)
            logger.info(f"\n{'='*60}")
            logger.info(f"Combined Results:")
            logger.info(f"{'='*60}")
            logger.info(f"Total flows extracted: {len(combined_df)}")
            logger.info(f"Total packets processed: {self.stats['total_packets']}")
            
            # Save combined dataset
            combined_path = output_path / "combined_pcap_flows.csv"
            combined_df.to_csv(combined_path, index=False)
            logger.info(f"✓ Combined dataset saved to {combined_path}")
            
            # Show some statistics
            logger.info(f"\nProtocol distribution:")
            print(combined_df['protocol'].value_counts().head())
            
            logger.info(f"\nTop destination ports:")
            print(combined_df['dst_port'].value_counts().head(10))
            
            return combined_df
        else:
            logger.warning("No flows extracted from any files")
            return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="Process PCAP files using Scapy")
    parser.add_argument("--input", "-i", required=True, help="Input PCAP file or directory")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file or directory")
    parser.add_argument("--pattern", default="*.pcapng", help="File pattern for directory mode")
    parser.add_argument("--flow-timeout", type=int, default=120, help="Flow idle timeout in seconds")
    
    args = parser.parse_args()
    
    processor = ScapyPCAPProcessor(flow_timeout=args.flow_timeout)
    
    # Check if input is file or directory
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single file mode
        logger.info("Processing single PCAP file...")
        df = processor.process_pcap(args.input, args.output)
        
        if not df.empty:
            logger.info(f"✓ Successfully processed {len(df)} flows")
        else:
            logger.error("✗ Failed to process PCAP")
            sys.exit(1)
    
    elif input_path.is_dir():
        # Directory mode
        logger.info("Processing directory of PCAP files...")
        df = processor.process_directory(args.input, args.output, args.pattern)
        
        if not df.empty:
            logger.info(f"✓ Successfully processed {len(df)} total flows")
        else:
            logger.error("✗ No flows extracted")
            sys.exit(1)
    
    else:
        logger.error(f"Input path does not exist: {args.input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
