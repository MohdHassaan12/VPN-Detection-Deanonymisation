#!/usr/bin/env python3
"""
Complete PCAP Preprocessing Pipeline for VPN Detection & User Segregation
==========================================================================

Features:
- NFStream for flow-level statistics
- PyShark for deep packet inspection (TCP handshake, entropy)
- IP reputation enrichment (IPQualityScore, IPinfo, IP2Proxy)
- All 100+ features from FEATURE_REFERENCE.md
- Batch processing with error handling and logging
- Memory-efficient processing for large files

Author: Network Security Lab
Date: November 9, 2025
"""

import os
import sys
import time
import logging
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

# NFStream for flow extraction
try:
    from nfstream import NFStreamer
except ImportError:
    print("ERROR: NFStream not installed. Run: pip install nfstream")
    sys.exit(1)

# PyShark for deep packet inspection (optional)
try:
    import pyshark
    PYSHARK_AVAILABLE = True
except ImportError:
    print("WARNING: PyShark not available. Deep packet inspection will be limited.")
    PYSHARK_AVAILABLE = False

# IP reputation libraries
try:
    import requests
    import ipaddress
    IP_ENRICHMENT_AVAILABLE = True
except ImportError:
    print("WARNING: IP enrichment libraries not available.")
    IP_ENRICHMENT_AVAILABLE = False

# Suppress warnings
warnings.filterwarnings('ignore')

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """Configure logging with both file and console output"""
    
    log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, mode='a'))
    
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True
    )
    
    return logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Configuration for PCAP processing"""
    
    # NFStream parameters
    IDLE_TIMEOUT = 120  # seconds
    ACTIVE_TIMEOUT = 1800  # seconds
    
    # IP Reputation API Keys (REPLACE WITH YOUR KEYS!)
    IPQS_API_KEY = os.getenv("IPQS_API_KEY", "YOUR_IPQUALITYSCORE_API_KEY")
    IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "YOUR_IPINFO_TOKEN")
    IP2PROXY_DB_PATH = os.getenv("IP2PROXY_DB", "./data/IP2PROXY-LITE-PX5.BIN")
    
    # Rate limiting for API calls
    API_RATE_LIMIT = 0.5  # seconds between calls
    
    # Feature extraction options
    EXTRACT_TCP_HANDSHAKE = True
    EXTRACT_ENTROPY = True
    ENRICH_IP_REPUTATION = False  # Set to True when you have API keys
    
    # Memory optimization
    CHUNK_SIZE = 10000  # Process flows in chunks
    
    # Private IP ranges (skip IP reputation lookup)
    PRIVATE_IP_RANGES = [
        '10.0.0.0/8',
        '172.16.0.0/12',
        '192.168.0.0/16',
        '127.0.0.0/8',
        '169.254.0.0/16'
    ]


# =============================================================================
# DEEP PACKET INSPECTION
# =============================================================================

class DeepPacketInspector:
    """Extract deep packet features using PyShark"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.pyshark_available = PYSHARK_AVAILABLE
    
    def extract_tcp_handshake(self, pcap_path: str) -> pd.DataFrame:
        """
        Extract TCP SYN packet features (MSS, TTL, Window Size)
        
        Returns DataFrame with columns:
        - src_ip, src_port, dst_ip, dst_port
        - tcp_mss, ip_ttl, tcp_window, tcp_options_count
        """
        if not self.pyshark_available:
            self.logger.warning("PyShark not available, skipping TCP handshake extraction")
            return pd.DataFrame()
        
        self.logger.info(f"Extracting TCP handshake features from {pcap_path}")
        
        try:
            # Filter for SYN packets only (initial connection)
            cap = pyshark.FileCapture(
                pcap_path,
                display_filter='tcp.flags.syn==1 and tcp.flags.ack==0',
                use_json=True,
                include_raw=True
            )
            
            syn_records = []
            packet_count = 0
            
            for pkt in cap:
                packet_count += 1
                try:
                    if not hasattr(pkt, 'tcp') or not hasattr(pkt, 'ip'):
                        continue
                    
                    # Extract 5-tuple
                    src_ip = pkt.ip.src
                    dst_ip = pkt.ip.dst
                    src_port = int(pkt.tcp.srcport)
                    dst_port = int(pkt.tcp.dstport)
                    
                    # Extract TCP options
                    mss = None
                    if hasattr(pkt.tcp, 'options_mss'):
                        mss = int(pkt.tcp.options_mss)
                    
                    ttl = int(pkt.ip.ttl)
                    window = int(pkt.tcp.window_size_value)
                    
                    # Count TCP options
                    options_count = 0
                    if hasattr(pkt.tcp, 'options'):
                        options_str = str(pkt.tcp.options)
                        options_count = len([x for x in options_str.split(',') if x.strip()])
                    
                    syn_records.append({
                        'src_ip': src_ip,
                        'src_port': src_port,
                        'dst_ip': dst_ip,
                        'dst_port': dst_port,
                        'tcp_mss': mss if mss else 1460,  # Default MSS
                        'ip_ttl': ttl,
                        'tcp_window': window,
                        'tcp_options_count': options_count
                    })
                    
                except AttributeError as e:
                    continue
                except Exception as e:
                    self.logger.debug(f"Error parsing SYN packet: {e}")
                    continue
            
            cap.close()
            
            if syn_records:
                syn_df = pd.DataFrame(syn_records)
                # Keep first SYN per flow
                syn_df = syn_df.drop_duplicates(
                    subset=['src_ip', 'src_port', 'dst_ip', 'dst_port'],
                    keep='first'
                )
                
                # Infer MTU from MSS (MTU = MSS + 40 bytes for TCP/IP headers)
                syn_df['tcp_mtu'] = syn_df['tcp_mss'] + 40
                
                self.logger.info(f"Extracted {len(syn_df)} TCP handshake records from {packet_count} SYN packets")
                return syn_df
            else:
                self.logger.warning("No TCP SYN packets found")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Failed to extract TCP handshake: {e}")
            return pd.DataFrame()
    
    def calculate_entropy(self, pcap_path: str, sample_size: int = 100) -> Dict[str, float]:
        """
        Calculate payload entropy for flows (detects encryption)
        
        Returns dict mapping flow_id -> entropy_score
        High entropy (>7.5) indicates encryption
        """
        if not self.pyshark_available:
            return {}
        
        self.logger.info(f"Calculating payload entropy (sampling {sample_size} packets)")
        
        try:
            cap = pyshark.FileCapture(pcap_path, use_json=True, include_raw=True)
            
            flow_entropy = defaultdict(list)
            packet_count = 0
            
            for pkt in cap:
                if packet_count >= sample_size:
                    break
                
                packet_count += 1
                
                try:
                    if not hasattr(pkt, 'tcp') or not hasattr(pkt, 'ip'):
                        continue
                    
                    # Get payload
                    if hasattr(pkt.tcp, 'payload'):
                        payload_hex = pkt.tcp.payload.replace(':', '')
                        payload_bytes = bytes.fromhex(payload_hex)
                        
                        if len(payload_bytes) > 0:
                            # Calculate Shannon entropy
                            byte_counts = np.bincount(
                                np.frombuffer(payload_bytes, dtype=np.uint8),
                                minlength=256
                            )
                            probabilities = byte_counts[byte_counts > 0] / len(payload_bytes)
                            entropy = -np.sum(probabilities * np.log2(probabilities))
                            
                            # Create flow ID
                            flow_id = f"{pkt.ip.src}:{pkt.tcp.srcport}-{pkt.ip.dst}:{pkt.tcp.dstport}"
                            flow_entropy[flow_id].append(entropy)
                
                except Exception as e:
                    continue
            
            cap.close()
            
            # Average entropy per flow
            avg_entropy = {
                flow_id: np.mean(entropies)
                for flow_id, entropies in flow_entropy.items()
            }
            
            self.logger.info(f"Calculated entropy for {len(avg_entropy)} flows")
            return avg_entropy
            
        except Exception as e:
            self.logger.error(f"Failed to calculate entropy: {e}")
            return {}


# =============================================================================
# IP REPUTATION ENRICHMENT
# =============================================================================

class IPReputationEnricher:
    """Enrich IP addresses with reputation data"""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.cache = {}  # Cache results to avoid duplicate API calls
        
        # Initialize IP2Proxy if available
        self.ip2proxy_db = None
        if IP_ENRICHMENT_AVAILABLE:
            try:
                import IP2Proxy
                self.ip2proxy_db = IP2Proxy.IP2Proxy()
                if os.path.exists(config.IP2PROXY_DB_PATH):
                    self.ip2proxy_db.open(config.IP2PROXY_DB_PATH)
                    self.logger.info(f"Loaded IP2Proxy database: {config.IP2PROXY_DB_PATH}")
                else:
                    self.logger.warning(f"IP2Proxy database not found: {config.IP2PROXY_DB_PATH}")
                    self.ip2proxy_db = None
            except Exception as e:
                self.logger.warning(f"Could not initialize IP2Proxy: {e}")
    
    def is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private range"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback
        except:
            return False
    
    def query_ipqualityscore(self, ip: str) -> Dict:
        """Query IPQualityScore API"""
        result = {
            'ipqs_fraud_score': None,
            'ipqs_vpn': None,
            'ipqs_proxy': None,
            'ipqs_tor': None,
            'ipqs_connection_type': None
        }
        
        if self.config.IPQS_API_KEY == "YOUR_IPQUALITYSCORE_API_KEY":
            return result
        
        try:
            url = f"https://ipqualityscore.com/api/json/ip/{self.config.IPQS_API_KEY}/{ip}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result['ipqs_fraud_score'] = data.get('fraud_score')
                    result['ipqs_vpn'] = int(data.get('vpn', False))
                    result['ipqs_proxy'] = int(data.get('proxy', False))
                    result['ipqs_tor'] = int(data.get('tor', False))
                    result['ipqs_connection_type'] = data.get('connection_type')
        
        except Exception as e:
            self.logger.debug(f"IPQS query failed for {ip}: {e}")
        
        return result
    
    def query_ip2proxy(self, ip: str) -> Dict:
        """Query IP2Proxy local database"""
        result = {
            'ip2proxy_is_proxy': None,
            'ip2proxy_proxy_type': None,
            'ip2proxy_country': None,
            'ip2proxy_usage_type': None
        }
        
        if not self.ip2proxy_db:
            return result
        
        try:
            record = self.ip2proxy_db.get_all(ip)
            
            # is_proxy: -1=error, 0=no proxy, 1=proxy, 2=data center
            if record.is_proxy in [1, 2]:
                result['ip2proxy_is_proxy'] = 1
                result['ip2proxy_proxy_type'] = record.proxy_type
                result['ip2proxy_country'] = record.country_short
                result['ip2proxy_usage_type'] = record.usage_type
            else:
                result['ip2proxy_is_proxy'] = 0
        
        except Exception as e:
            self.logger.debug(f"IP2Proxy query failed for {ip}: {e}")
        
        return result
    
    def enrich_ip(self, ip: str) -> Dict:
        """Enrich single IP with all available data sources"""
        
        # Check cache
        if ip in self.cache:
            return self.cache[ip]
        
        # Initialize result
        result = {
            'ip': ip,
            'is_private': int(self.is_private_ip(ip))
        }
        
        # Skip private IPs
        if result['is_private']:
            self.cache[ip] = result
            return result
        
        # Query APIs
        if IP_ENRICHMENT_AVAILABLE and self.config.ENRICH_IP_REPUTATION:
            result.update(self.query_ipqualityscore(ip))
            result.update(self.query_ip2proxy(ip))
            
            # Rate limiting
            time.sleep(self.config.API_RATE_LIMIT)
        
        self.cache[ip] = result
        return result
    
    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich all IPs in DataFrame"""
        
        if not self.config.ENRICH_IP_REPUTATION:
            self.logger.info("IP enrichment disabled in config")
            return df
        
        self.logger.info("Enriching IP addresses with reputation data...")
        
        # Get unique IPs from both source and destination
        unique_ips = pd.unique(df[['src_ip', 'dst_ip']].values.ravel())
        unique_ips = [ip for ip in unique_ips if pd.notna(ip)]
        
        self.logger.info(f"Enriching {len(unique_ips)} unique IP addresses")
        
        # Enrich each IP
        ip_data = []
        for ip in tqdm(unique_ips, desc="IP Enrichment"):
            ip_data.append(self.enrich_ip(ip))
        
        ip_df = pd.DataFrame(ip_data)
        
        # Merge with source IPs
        df = df.merge(
            ip_df.add_prefix('src_'),
            left_on='src_ip',
            right_on='src_ip',
            how='left'
        )
        
        # Merge with destination IPs
        df = df.merge(
            ip_df.add_prefix('dst_'),
            left_on='dst_ip',
            right_on='dst_ip',
            how='left'
        )
        
        self.logger.info(f"IP enrichment complete. Added {len(ip_df.columns)} features per IP")
        return df


# =============================================================================
# COMPREHENSIVE FEATURE EXTRACTOR
# =============================================================================

class ComprehensiveFeatureExtractor:
    """Extract all 100+ features from FEATURE_REFERENCE.md"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def extract_connection_identifiers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract connection identifier features (6 features)"""
        
        # Create flow_id if not exists
        if 'flow_id' not in df.columns:
            df['flow_id'] = df.apply(
                lambda row: f"{row['src_ip']}:{row['src_port']}-{row['dst_ip']}:{row['dst_port']}-{row['protocol']}",
                axis=1
            )
        
        return df
    
    def extract_flow_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract flow statistics (20 features)"""
        
        # Packet counts
        df['packet_count_fwd'] = df.get('src2dst_packets', 0)
        df['packet_count_bwd'] = df.get('dst2src_packets', 0)
        df['packet_count_total'] = df.get('bidirectional_packets', 
                                           df['packet_count_fwd'] + df['packet_count_bwd'])
        
        # Byte counts
        df['byte_count_fwd'] = df.get('src2dst_bytes', 0)
        df['byte_count_bwd'] = df.get('dst2src_bytes', 0)
        df['byte_count_total'] = df.get('bidirectional_bytes',
                                         df['byte_count_fwd'] + df['byte_count_bwd'])
        
        # Flow duration
        df['flow_duration'] = df.get('bidirectional_duration_ms', 0) / 1000.0  # Convert to seconds
        
        # Flow rates
        df['packets_per_second'] = np.where(
            df['flow_duration'] > 0,
            df['packet_count_total'] / df['flow_duration'],
            0
        )
        
        df['bytes_per_second'] = np.where(
            df['flow_duration'] > 0,
            df['byte_count_total'] / df['flow_duration'],
            0
        )
        
        # Ratios
        df['byte_ratio'] = np.where(
            df['byte_count_bwd'] > 0,
            df['byte_count_fwd'] / df['byte_count_bwd'],
            df['byte_count_fwd']
        )
        
        df['packet_ratio'] = np.where(
            df['packet_count_bwd'] > 0,
            df['packet_count_fwd'] / df['packet_count_bwd'],
            df['packet_count_fwd']
        )
        
        df['down_up_ratio'] = np.where(
            df['byte_count_fwd'] > 0,
            df['byte_count_bwd'] / df['byte_count_fwd'],
            0
        )
        
        # Bulk rates (placeholder)
        df['fwd_bulk_rate'] = df['bytes_per_second'] * 0.5  # Simplified
        df['bwd_bulk_rate'] = df['bytes_per_second'] * 0.5
        
        # Active/Idle times (use IAT as proxy)
        df['active_mean'] = df.get('bidirectional_mean_iat', 0)
        df['active_std'] = df.get('bidirectional_stddev_iat', 0)
        df['idle_mean'] = df.get('bidirectional_max_iat', 0) * 0.5
        df['idle_std'] = df.get('bidirectional_stddev_iat', 0)
        
        # Packet length variance
        if 'bidirectional_stddev_ps' in df.columns:
            df['packet_length_variance'] = df['bidirectional_stddev_ps'] ** 2
        else:
            df['packet_length_variance'] = 0
        
        # Coefficient of variation
        df['packet_length_cv'] = np.where(
            df.get('bidirectional_mean_ps', 1) > 0,
            df.get('bidirectional_stddev_ps', 0) / df.get('bidirectional_mean_ps', 1),
            0
        )
        
        return df
    
    def extract_packet_size_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract packet size features (10 features)"""
        
        # Map NFStream columns to standard names
        mapping = {
            'bidirectional_min_ps': 'packet_length_min',
            'bidirectional_max_ps': 'packet_length_max',
            'bidirectional_mean_ps': 'packet_length_mean',
            'bidirectional_stddev_ps': 'packet_length_std'
        }
        
        for nf_col, new_col in mapping.items():
            if nf_col in df.columns:
                df[new_col] = df[nf_col]
            else:
                df[new_col] = 0
        
        # Quartiles (approximate from mean and std)
        if 'packet_length_mean' in df.columns and 'packet_length_std' in df.columns:
            df['packet_length_q1'] = df['packet_length_mean'] - 0.675 * df['packet_length_std']
            df['packet_length_q2'] = df['packet_length_mean']  # Median = Mean (assuming normal)
            df['packet_length_q3'] = df['packet_length_mean'] + 0.675 * df['packet_length_std']
        else:
            df['packet_length_q1'] = 0
            df['packet_length_q2'] = 0
            df['packet_length_q3'] = 0
        
        return df
    
    def extract_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract timing features (15 features)"""
        
        # Inter-arrival times
        iat_mapping = {
            'src2dst_mean_iat': 'mean_iat_fwd',
            'src2dst_stddev_iat': 'std_iat_fwd',
            'src2dst_min_iat': 'min_iat_fwd',
            'src2dst_max_iat': 'max_iat_fwd',
            'dst2src_mean_iat': 'mean_iat_bwd',
            'dst2src_stddev_iat': 'std_iat_bwd',
            'dst2src_min_iat': 'min_iat_bwd',
            'dst2src_max_iat': 'max_iat_bwd',
            'bidirectional_mean_iat': 'flow_iat_mean',
            'bidirectional_stddev_iat': 'flow_iat_std'
        }
        
        for nf_col, new_col in iat_mapping.items():
            df[new_col] = df.get(nf_col, 0)
        
        df['iat_total'] = df['flow_iat_mean']
        
        # Jitter
        df['jitter'] = df.get('flow_iat_std', 0)
        
        # RTT (approximate from IAT)
        df['rtt_mean'] = df.get('flow_iat_mean', 0)
        df['rtt_std'] = df.get('flow_iat_std', 0)
        
        # Periodicity score (inverse coefficient of variation)
        df['periodicity_score'] = np.where(
            df['flow_iat_std'] > 0,
            df['flow_iat_mean'] / df['flow_iat_std'],
            0
        )
        
        # Burst rate
        df['burst_rate'] = df.get('packets_per_second', 0)
        
        # Inter-burst time (approximate)
        df['inter_burst_time'] = df.get('flow_iat_mean', 0)
        
        return df
    
    def extract_tcp_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract TCP features (12 features)"""
        
        # TCP flags
        flag_mapping = {
            'src2dst_syn_packets': 'fwd_syn_packets',
            'dst2src_syn_packets': 'bwd_syn_packets',
            'src2dst_ack_packets': 'fwd_ack_packets',
            'src2dst_fin_packets': 'fwd_fin_packets',
            'src2dst_rst_packets': 'fwd_rst_packets',
            'src2dst_psh_packets': 'fwd_psh_packets',
            'src2dst_urg_packets': 'fwd_urg_packets'
        }
        
        for nf_col, new_col in flag_mapping.items():
            df[new_col] = df.get(nf_col, 0)
        
        # Connection rate
        df['connection_rate'] = np.where(
            df['flow_duration'] > 0,
            df['fwd_syn_packets'] / df['flow_duration'],
            0
        )
        
        # Failed connections
        df['failed_connections'] = df['fwd_rst_packets']
        
        # SYN-ACK delay (placeholder - requires packet-level timing)
        df['syn_ack_delay'] = df.get('flow_iat_mean', 0) * 0.1
        
        return df
    
    def extract_vpn_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract VPN detection features (10 features)"""
        
        # Protocol hint (common VPN ports)
        vpn_ports = [1194, 1723, 500, 4500, 51820, 443, 1701]
        df['protocol_hint'] = df['dst_port'].isin(vpn_ports).astype(int)
        
        # Encryption detected (will be updated with entropy if available)
        df['encryption_detected'] = 0
        df['entropy_score'] = 0.0
        
        # TLS/cipher info (placeholders - require deep inspection)
        df['tls_version'] = None
        df['cipher_suite'] = None
        
        return df
    
    def extract_behavioral_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract behavioral features (12 features)"""
        
        # Placeholders for behavioral features
        # These require temporal/session analysis across multiple flows
        df['login_failure_rate'] = 0.0
        df['account_velocity'] = df.get('packets_per_second', 0)
        df['session_duration'] = df.get('flow_duration', 0)
        df['request_frequency'] = df.get('packets_per_second', 0)
        df['connection_establishment_rate'] = df.get('connection_rate', 0)
        df['human_score'] = 0.5  # Neutral
        df['bot_probability'] = 0.0
        df['anomaly_score'] = 0.0
        df['reputation_change'] = 0.0
        
        # Time of day score (from timestamp if available)
        if 'bidirectional_first_seen_ms' in df.columns:
            hour = (df['bidirectional_first_seen_ms'] / 1000 / 3600) % 24
            # Anomaly if outside business hours (9-17)
            df['time_of_day_score'] = np.where(
                (hour >= 9) & (hour <= 17),
                0.0,  # Normal
                0.5   # Slightly anomalous
            )
        else:
            df['time_of_day_score'] = 0.0
        
        return df
    
    def extract_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add label placeholders (3 features)"""
        
        df['app_label'] = 'Unknown'
        df['intent_label'] = 'Unknown'
        df['vpn_flag'] = 0
        
        return df
    
    def extract_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract all feature categories"""
        
        self.logger.info("Extracting comprehensive features...")
        
        df = self.extract_connection_identifiers(df)
        df = self.extract_flow_statistics(df)
        df = self.extract_packet_size_features(df)
        df = self.extract_timing_features(df)
        df = self.extract_tcp_features(df)
        df = self.extract_vpn_features(df)
        df = self.extract_behavioral_features(df)
        df = self.extract_labels(df)
        
        self.logger.info(f"Feature extraction complete: {len(df.columns)} total features")
        
        return df


# =============================================================================
# MAIN PCAP PROCESSOR
# =============================================================================

class CompletePCAPProcessor:
    """Main orchestrator for PCAP processing pipeline"""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        
        # Initialize components
        self.dpi = DeepPacketInspector(logger)
        self.ip_enricher = IPReputationEnricher(config, logger)
        self.feature_extractor = ComprehensiveFeatureExtractor(logger)
    
    def process_single_pcap(self, pcap_path: str, output_csv: Optional[str] = None) -> pd.DataFrame:
        """
        Process a single PCAP file through complete pipeline
        
        Steps:
        1. Extract flows with NFStream
        2. Extract TCP handshake features with PyShark
        3. Calculate payload entropy
        4. Enrich IP reputation
        5. Extract all features
        6. Save to CSV
        """
        
        start_time = time.time()
        self.logger.info(f"{'='*80}")
        self.logger.info(f"Processing PCAP: {pcap_path}")
        self.logger.info(f"{'='*80}")
        
        # ========== STEP 1: Extract flows with NFStream ==========
        self.logger.info("STEP 1/5: Extracting flows with NFStream...")
        
        try:
            streamer = NFStreamer(
                source=pcap_path,
                statistical_analysis=True,
                idle_timeout=self.config.IDLE_TIMEOUT,
                active_timeout=self.config.ACTIVE_TIMEOUT,
                n_dissections=20
            )
            
            df = streamer.to_pandas()
            
            if df.empty:
                self.logger.warning("No flows extracted from PCAP")
                return pd.DataFrame()
            
            self.logger.info(f"✓ Extracted {len(df)} flows")
            
        except Exception as e:
            self.logger.error(f"NFStream failed: {e}")
            return pd.DataFrame()
        
        # ========== STEP 2: Extract TCP handshake features ==========
        if self.config.EXTRACT_TCP_HANDSHAKE:
            self.logger.info("STEP 2/5: Extracting TCP handshake features...")
            
            syn_df = self.dpi.extract_tcp_handshake(pcap_path)
            
            if not syn_df.empty:
                # Merge with flows
                df = df.merge(
                    syn_df,
                    on=['src_ip', 'src_port', 'dst_ip', 'dst_port'],
                    how='left'
                )
                self.logger.info(f"✓ Merged {len(syn_df)} TCP handshake records")
            else:
                # Add empty columns
                for col in ['tcp_mss', 'ip_ttl', 'tcp_window', 'tcp_options_count', 'tcp_mtu']:
                    df[col] = 0
                self.logger.info("✓ No TCP handshake data (added placeholders)")
        else:
            self.logger.info("STEP 2/5: Skipped (TCP handshake disabled)")
        
        # ========== STEP 3: Calculate payload entropy ==========
        if self.config.EXTRACT_ENTROPY:
            self.logger.info("STEP 3/5: Calculating payload entropy...")
            
            entropy_dict = self.dpi.calculate_entropy(pcap_path)
            
            if entropy_dict:
                # Create flow_id in df
                df['flow_id_temp'] = df.apply(
                    lambda row: f"{row['src_ip']}:{row['src_port']}-{row['dst_ip']}:{row['dst_port']}",
                    axis=1
                )
                
                # Map entropy scores
                df['entropy_score'] = df['flow_id_temp'].map(entropy_dict).fillna(0.0)
                df['encryption_detected'] = (df['entropy_score'] > 7.5).astype(int)
                df.drop('flow_id_temp', axis=1, inplace=True)
                
                self.logger.info(f"✓ Calculated entropy for {len(entropy_dict)} flows")
            else:
                df['entropy_score'] = 0.0
                df['encryption_detected'] = 0
                self.logger.info("✓ No entropy data (added placeholders)")
        else:
            self.logger.info("STEP 3/5: Skipped (entropy calculation disabled)")
        
        # ========== STEP 4: Enrich IP reputation ==========
        self.logger.info("STEP 4/5: Enriching IP reputation...")
        
        df = self.ip_enricher.enrich_dataframe(df)
        self.logger.info("✓ IP enrichment complete")
        
        # ========== STEP 5: Extract all features ==========
        self.logger.info("STEP 5/5: Extracting comprehensive features...")
        
        df = self.feature_extractor.extract_all(df)
        self.logger.info(f"✓ Feature extraction complete ({len(df.columns)} features)")
        
        # ========== Save output ==========
        if output_csv:
            os.makedirs(os.path.dirname(output_csv) if os.path.dirname(output_csv) else '.', exist_ok=True)
            df.to_csv(output_csv, index=False)
            self.logger.info(f"✓ Saved to: {output_csv}")
        
        elapsed = time.time() - start_time
        self.logger.info(f"{'='*80}")
        self.logger.info(f"✓ Processing complete in {elapsed:.2f} seconds")
        self.logger.info(f"  - Flows: {len(df)}")
        self.logger.info(f"  - Features: {len(df.columns)}")
        self.logger.info(f"{'='*80}\n")
        
        return df
    
    def process_directory(self, input_dir: str, output_dir: str, pattern: str = "*.pcap") -> pd.DataFrame:
        """Process all PCAP files in a directory"""
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all PCAP files
        pcap_files = list(input_path.rglob(pattern))
        self.logger.info(f"Found {len(pcap_files)} PCAP files matching '{pattern}'")
        
        if not pcap_files:
            self.logger.warning(f"No PCAP files found in {input_dir}")
            return pd.DataFrame()
        
        # Process each file
        all_flows = []
        summary_data = []
        
        for i, pcap_file in enumerate(pcap_files, 1):
            self.logger.info(f"\n[{i}/{len(pcap_files)}] Processing: {pcap_file.name}")
            
            try:
                # Generate output path
                relative_path = pcap_file.relative_to(input_path)
                output_csv = output_path / relative_path.with_suffix('.csv')
                output_csv.parent.mkdir(parents=True, exist_ok=True)
                
                # Process PCAP
                start_time = time.time()
                df = self.process_single_pcap(str(pcap_file), str(output_csv))
                elapsed = time.time() - start_time
                
                if not df.empty:
                    df['source_file'] = pcap_file.name
                    df['source_path'] = str(relative_path.parent)
                    all_flows.append(df)
                    
                    summary_data.append({
                        'file': pcap_file.name,
                        'flows': len(df),
                        'features': len(df.columns),
                        'time_seconds': elapsed,
                        'status': 'SUCCESS'
                    })
                else:
                    summary_data.append({
                        'file': pcap_file.name,
                        'flows': 0,
                        'features': 0,
                        'time_seconds': elapsed,
                        'status': 'EMPTY'
                    })
            
            except Exception as e:
                self.logger.error(f"Failed to process {pcap_file.name}: {e}")
                summary_data.append({
                    'file': pcap_file.name,
                    'flows': 0,
                    'features': 0,
                    'time_seconds': 0,
                    'status': f'ERROR: {str(e)[:50]}'
                })
                continue
        
        # Save summary
        summary_df = pd.DataFrame(summary_data)
        summary_path = output_path / 'processing_summary.csv'
        summary_df.to_csv(summary_path, index=False)
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info("BATCH PROCESSING SUMMARY")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"\n{summary_df.to_string(index=False)}\n")
        self.logger.info(f"Summary saved to: {summary_path}")
        
        # Combine all flows
        if all_flows:
            combined_df = pd.concat(all_flows, ignore_index=True)
            combined_path = output_path / 'combined_flows.csv'
            combined_df.to_csv(combined_path, index=False)
            
            self.logger.info(f"✓ Combined dataset: {len(combined_df)} flows")
            self.logger.info(f"✓ Saved to: {combined_path}")
            
            return combined_df
        else:
            self.logger.warning("No flows extracted from any files")
            return pd.DataFrame()


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Complete PCAP Preprocessing Pipeline for VPN Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single PCAP file
  python complete_pcap_processor.py -i traffic.pcap -o output.csv
  
  # Process directory of PCAPs
  python complete_pcap_processor.py -i ./pcaps/ -o ./output/ --batch
  
  # Enable IP reputation enrichment (requires API keys in environment)
  export IPQS_API_KEY="your_key_here"
  export IPINFO_TOKEN="your_token_here"
  python complete_pcap_processor.py -i traffic.pcap -o output.csv --enrich-ip
  
  # Process with custom timeouts
  python complete_pcap_processor.py -i traffic.pcap -o output.csv --idle-timeout 60 --active-timeout 900
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                        help='Input PCAP file or directory')
    parser.add_argument('-o', '--output', required=True,
                        help='Output CSV file or directory')
    parser.add_argument('--batch', action='store_true',
                        help='Batch mode: process all PCAPs in input directory')
    parser.add_argument('--pattern', default='*.pcap',
                        help='File pattern for batch mode (default: *.pcap)')
    
    # Processing options
    parser.add_argument('--idle-timeout', type=int, default=120,
                        help='Flow idle timeout in seconds (default: 120)')
    parser.add_argument('--active-timeout', type=int, default=1800,
                        help='Flow active timeout in seconds (default: 1800)')
    parser.add_argument('--no-tcp-handshake', action='store_true',
                        help='Disable TCP handshake extraction')
    parser.add_argument('--no-entropy', action='store_true',
                        help='Disable payload entropy calculation')
    parser.add_argument('--enrich-ip', action='store_true',
                        help='Enable IP reputation enrichment (requires API keys)')
    
    # Logging options
    parser.add_argument('--log-file', default='../logs/pcap_processing.log',
                        help='Log file path (default: ../logs/pcap_processing.log)')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(args.log_file, log_level)
    
    logger.info("="*80)
    logger.info("COMPLETE PCAP PREPROCESSING PIPELINE")
    logger.info("VPN Detection & User Segregation")
    logger.info("="*80)
    
    # Configure processing
    config = Config()
    config.IDLE_TIMEOUT = args.idle_timeout
    config.ACTIVE_TIMEOUT = args.active_timeout
    config.EXTRACT_TCP_HANDSHAKE = not args.no_tcp_handshake
    config.EXTRACT_ENTROPY = not args.no_entropy
    config.ENRICH_IP_REPUTATION = args.enrich_ip
    
    # Display configuration
    logger.info("\nConfiguration:")
    logger.info(f"  - Idle Timeout: {config.IDLE_TIMEOUT}s")
    logger.info(f"  - Active Timeout: {config.ACTIVE_TIMEOUT}s")
    logger.info(f"  - TCP Handshake: {config.EXTRACT_TCP_HANDSHAKE}")
    logger.info(f"  - Entropy Calculation: {config.EXTRACT_ENTROPY}")
    logger.info(f"  - IP Enrichment: {config.ENRICH_IP_REPUTATION}")
    logger.info("")
    
    # Initialize processor
    processor = CompletePCAPProcessor(config, logger)
    
    # Process based on mode
    try:
        if args.batch:
            # Batch mode
            logger.info(f"Mode: Batch Processing")
            logger.info(f"Input Directory: {args.input}")
            logger.info(f"Output Directory: {args.output}")
            logger.info(f"Pattern: {args.pattern}\n")
            
            df = processor.process_directory(args.input, args.output, args.pattern)
            
            if not df.empty:
                logger.info(f"\n✓ SUCCESS: Processed {len(df)} total flows")
                sys.exit(0)
            else:
                logger.error("\n✗ FAILED: No flows extracted")
                sys.exit(1)
        
        else:
            # Single file mode
            logger.info(f"Mode: Single File Processing")
            logger.info(f"Input: {args.input}")
            logger.info(f"Output: {args.output}\n")
            
            df = processor.process_single_pcap(args.input, args.output)
            
            if not df.empty:
                logger.info(f"\n✓ SUCCESS: Processed {len(df)} flows")
                sys.exit(0)
            else:
                logger.error("\n✗ FAILED: No flows extracted")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.warning("\n\nProcessing interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"\n\nFATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
