"""
Feature Extraction Module for Network Traffic Analysis
Extracts comprehensive features from PCAP files and flow data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from scipy import stats
from scipy.stats import entropy
import warnings

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlowFeatureExtractor:
    """Extract statistical and behavioral features from network flows"""
    
    def __init__(self):
        self.feature_names = []
    
    def extract_flow_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract statistical features from flow data
        
        Args:
            df: DataFrame with basic flow information
            
        Returns:
            DataFrame with added statistical features
        """
        logger.info("Extracting flow statistics...")
        
        # Packet count features
        if 'bidirectional_packets' in df.columns:
            df['packet_count_total'] = df['bidirectional_packets']
            df['packet_count_fwd'] = df.get('src2dst_packets', df['bidirectional_packets'] / 2)
            df['packet_count_bwd'] = df.get('dst2src_packets', df['bidirectional_packets'] / 2)
        
        # Byte count features
        if 'bidirectional_bytes' in df.columns:
            df['byte_count_total'] = df['bidirectional_bytes']
            df['byte_count_fwd'] = df.get('src2dst_bytes', df['bidirectional_bytes'] / 2)
            df['byte_count_bwd'] = df.get('dst2src_bytes', df['bidirectional_bytes'] / 2)
        
        # Flow duration
        if 'bidirectional_duration_ms' in df.columns:
            df['flow_duration'] = df['bidirectional_duration_ms'] / 1000.0  # Convert to seconds
            
            # Flow rate features
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
        
        # Byte ratio
        df['byte_ratio'] = np.where(
            df['byte_count_bwd'] > 0,
            df['byte_count_fwd'] / df['byte_count_bwd'],
            df['byte_count_fwd']
        )
        
        # Packet ratio
        df['packet_ratio'] = np.where(
            df['packet_count_bwd'] > 0,
            df['packet_count_fwd'] / df['packet_count_bwd'],
            df['packet_count_fwd']
        )
        
        logger.info(f"Extracted {len([c for c in df.columns if c.startswith(('packet_', 'byte_', 'flow_'))])} flow features")
        return df
    
    def extract_packet_size_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract packet size statistics"""
        logger.info("Extracting packet size features...")
        
        # Packet length statistics
        size_features = [
            'bidirectional_min_ps',
            'bidirectional_max_ps',
            'bidirectional_mean_ps',
            'bidirectional_stddev_ps'
        ]
        
        for feat in size_features:
            if feat in df.columns:
                new_name = feat.replace('bidirectional_', 'packet_length_').replace('_ps', '')
                df[new_name] = df[feat]
        
        # Packet length variance
        if 'packet_length_stddev' in df.columns:
            df['packet_length_variance'] = df['packet_length_stddev'] ** 2
        
        # Coefficient of variation
        if 'packet_length_mean' in df.columns and 'packet_length_stddev' in df.columns:
            df['packet_length_cv'] = np.where(
                df['packet_length_mean'] > 0,
                df['packet_length_stddev'] / df['packet_length_mean'],
                0
            )
        
        logger.info(f"Extracted {len([c for c in df.columns if 'packet_length' in c])} packet size features")
        return df
    
    def extract_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract inter-arrival time and timing features"""
        logger.info("Extracting timing features...")
        
        # Inter-arrival time statistics
        iat_features = [
            'bidirectional_min_iat',
            'bidirectional_max_iat',
            'bidirectional_mean_iat',
            'bidirectional_stddev_iat'
        ]
        
        for feat in iat_features:
            if feat in df.columns:
                new_name = feat.replace('bidirectional_', '').replace('_iat', '_iat_total')
                df[new_name] = df[feat]
        
        # Forward and backward IAT
        for direction in ['src2dst', 'dst2src']:
            prefix = 'fwd' if direction == 'src2dst' else 'bwd'
            for stat in ['min', 'max', 'mean', 'stddev']:
                col = f'{direction}_{stat}_iat'
                if col in df.columns:
                    df[f'iat_{stat}_{prefix}'] = df[col]
        
        # Jitter (variance in IAT)
        if 'stddev_iat_total' in df.columns:
            df['jitter'] = df['stddev_iat_total']
        
        # Periodicity score (inverse of coefficient of variation)
        if 'mean_iat_total' in df.columns and 'stddev_iat_total' in df.columns:
            df['periodicity_score'] = np.where(
                df['stddev_iat_total'] > 0,
                df['mean_iat_total'] / df['stddev_iat_total'],
                0
            )
        
        logger.info(f"Extracted {len([c for c in df.columns if 'iat' in c or c in ['jitter', 'periodicity_score']])} timing features")
        return df
    
    def extract_tcp_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract TCP-specific features"""
        logger.info("Extracting TCP features...")
        
        # TCP flags
        flag_columns = [
            'src2dst_syn_packets', 'src2dst_ack_packets', 'src2dst_fin_packets',
            'src2dst_rst_packets', 'src2dst_psh_packets', 'src2dst_urg_packets',
            'dst2src_syn_packets', 'dst2src_ack_packets', 'dst2src_fin_packets',
            'dst2src_rst_packets', 'dst2src_psh_packets', 'dst2src_urg_packets'
        ]
        
        for col in flag_columns:
            if col in df.columns:
                new_name = col.replace('src2dst_', 'fwd_').replace('dst2src_', 'bwd_')
                df[new_name] = df[col]
        
        # Connection establishment rate
        if 'fwd_syn_packets' in df.columns and 'flow_duration' in df.columns:
            df['connection_rate'] = np.where(
                df['flow_duration'] > 0,
                df['fwd_syn_packets'] / df['flow_duration'],
                0
            )
        
        # Failed connections (RST packets)
        if 'fwd_rst_packets' in df.columns and 'bwd_rst_packets' in df.columns:
            df['failed_connections'] = df['fwd_rst_packets'] + df['bwd_rst_packets']
        
        logger.info(f"Extracted TCP-specific features")
        return df
    
    def extract_vpn_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract VPN detection features"""
        logger.info("Extracting VPN detection features...")
        
        # Protocol hints
        if 'protocol' in df.columns:
            # Common VPN ports
            df['protocol_hint'] = 0
            if 'dst_port' in df.columns:
                vpn_ports = [1194, 1723, 500, 4500, 51820]  # OpenVPN, PPTP, IPSec, WireGuard
                df.loc[df['dst_port'].isin(vpn_ports), 'protocol_hint'] = 1
        
        # Encryption detection (high entropy in payload)
        # This is a placeholder - actual implementation requires packet payload analysis
        df['encryption_detected'] = 0
        df['entropy_score'] = 0.0
        
        # Placeholder for MSS, MTU, TTL (requires deep packet inspection)
        df['mss'] = 0
        df['mtu'] = 0
        df['ttl'] = 0
        df['window_size'] = 0
        df['tcp_options_count'] = 0
        
        logger.info("VPN detection features added (placeholders for deep packet inspection)")
        return df
    
    def extract_behavioral_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract behavioral features"""
        logger.info("Extracting behavioral features...")
        
        # Burst patterns
        if 'packets_per_second' in df.columns:
            df['burst_rate'] = df['packets_per_second']
        
        # Session duration
        if 'flow_duration' in df.columns:
            df['session_duration'] = df['flow_duration']
        
        # Placeholder for behavioral features (require temporal analysis)
        df['login_failure_rate'] = 0.0
        df['account_velocity'] = 0.0
        df['human_score'] = 0.5  # Neutral score
        df['bot_probability'] = 0.0
        df['anomaly_score'] = 0.0
        
        logger.info("Behavioral features added")
        return df
    
    def extract_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract all features from flow data
        
        Args:
            df: Raw flow DataFrame
            
        Returns:
            DataFrame with all extracted features
        """
        logger.info(f"Starting feature extraction for {len(df)} flows...")
        
        # Extract features in sequence
        df = self.extract_flow_statistics(df)
        df = self.extract_packet_size_features(df)
        df = self.extract_timing_features(df)
        df = self.extract_tcp_features(df)
        df = self.extract_vpn_features(df)
        df = self.extract_behavioral_features(df)
        
        logger.info(f"Feature extraction complete. Total columns: {len(df.columns)}")
        return df


class PCAPFeatureExtractor:
    """Extract features directly from PCAP files using PyShark"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_tcp_handshake_features(self, pcap_path: str) -> Dict:
        """
        Extract TCP handshake features (MSS, TTL, Window Size)
        
        Args:
            pcap_path: Path to PCAP file
            
        Returns:
            Dictionary of handshake features per flow
        """
        try:
            import pyshark
            
            self.logger.info(f"Extracting TCP handshake features from {pcap_path}")
            
            cap = pyshark.FileCapture(pcap_path, display_filter='tcp.flags.syn==1')
            handshake_features = {}
            
            for pkt in cap:
                try:
                    if hasattr(pkt, 'tcp') and hasattr(pkt, 'ip'):
                        flow_key = f"{pkt.ip.src}:{pkt.tcp.srcport}-{pkt.ip.dst}:{pkt.tcp.dstport}"
                        
                        features = {
                            'mss': int(pkt.tcp.options_mss) if hasattr(pkt.tcp, 'options_mss') else 0,
                            'ttl': int(pkt.ip.ttl),
                            'window_size': int(pkt.tcp.window_size_value),
                            'tcp_options_count': len(pkt.tcp.options.split(',')) if hasattr(pkt.tcp, 'options') else 0
                        }
                        
                        handshake_features[flow_key] = features
                except Exception as e:
                    continue
            
            cap.close()
            self.logger.info(f"Extracted handshake features for {len(handshake_features)} flows")
            return handshake_features
            
        except ImportError:
            self.logger.warning("PyShark not available, skipping deep packet inspection")
            return {}
        except Exception as e:
            self.logger.error(f"Error extracting handshake features: {e}")
            return {}
    
    def calculate_payload_entropy(self, payload: bytes) -> float:
        """
        Calculate Shannon entropy of payload (detects encryption)
        
        Args:
            payload: Packet payload bytes
            
        Returns:
            Entropy value (0-8, where >7.5 indicates encryption)
        """
        if not payload or len(payload) == 0:
            return 0.0
        
        # Calculate byte frequency
        byte_counts = np.bincount(np.frombuffer(payload, dtype=np.uint8), minlength=256)
        probabilities = byte_counts / len(payload)
        
        # Calculate Shannon entropy
        return entropy(probabilities, base=2)


def create_flow_id(row: pd.Series) -> str:
    """Create unique flow identifier from 5-tuple"""
    return f"{row['src_ip']}:{row['src_port']}-{row['dst_ip']}:{row['dst_port']}-{row['protocol']}"


if __name__ == "__main__":
    # Example usage
    logger.info("Feature Extractor Module - Ready")
    logger.info("Import this module to use FlowFeatureExtractor or PCAPFeatureExtractor classes")
