"""
FortiAnalyzer Log Processor
Processes FortiGate firewall logs and converts them to unified flow format
"""

import os
import sys
import argparse
import logging
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import glob

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FortiAnalyzerProcessor:
    """Process FortiAnalyzer/FortiGate logs"""
    
    # Application to unified label mapping
    APP_LABEL_MAPPING = {
        # Browsing / Web
        'DNS': 'Browsing',
        'HTTP': 'Browsing',
        'HTTPS': 'Browsing',
        'QUIC': 'Browsing',
        'SSL': 'Browsing',
        
        # File Transfer
        'SMB': 'File_Transfer',
        'FTP': 'File_Transfer',
        'SFTP': 'File_Transfer',
        'FTPS': 'File_Transfer',
        'SSH': 'File_Transfer',
        
        # Email
        'SMTP': 'Email',
        'IMAP': 'Email',
        'POP3': 'Email',
        'IMAPS': 'Email',
        'POP3S': 'Email',
        
        # VoIP / Communication
        'SIP': 'VoIP',
        'STUN': 'VoIP',
        'udp/3478': 'VoIP',  # STUN/TURN
        'tcp/3478': 'VoIP',
        
        # Enterprise Apps
        'LDAP': 'Enterprise_App',
        'LDAP_UDP': 'Enterprise_App',
        'LDAPS': 'Enterprise_App',
        'Kerberos': 'Enterprise_App',
        'NTP': 'Enterprise_App',
        
        # Unknown/Other
        'udp/443': 'Unknown',  # Could be QUIC or VPN
        'tcp/443': 'Browsing',
    }
    
    # Intent label mapping based on action and threat indicators
    INTENT_MAPPING = {
        'deny': 'Suspicious',
        'blocked': 'Malicious',
    }
    
    def __init__(self):
        self.processed_flows = []
        self.stats = {
            'total_lines': 0,
            'parsed_lines': 0,
            'failed_lines': 0,
            'unique_flows': 0
        }
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single FortiAnalyzer log line
        Format: key1=value1 key2="value with spaces" key3=value3
        """
        if not line.strip() or line.startswith('#'):
            return None
        
        fields = {}
        
        # Regex pattern to match key=value or key="value with spaces"
        pattern = r'(\w+)=(?:"([^"]*)"|([^\s]+))'
        matches = re.findall(pattern, line)
        
        for match in matches:
            key = match[0]
            # Use quoted value if present, otherwise unquoted value
            value = match[1] if match[1] else match[2]
            fields[key] = value
        
        return fields if fields else None
    
    def map_fields_to_unified(self, fields: Dict) -> Dict:
        """Map FortiAnalyzer fields to unified schema"""
        unified = {}
        
        # Flow identifiers
        unified['src_ip'] = fields.get('srcip', '')
        unified['dst_ip'] = fields.get('dstip', '')
        unified['src_port'] = int(fields.get('srcport', 0)) if fields.get('srcport', '').isdigit() else 0
        unified['dst_port'] = int(fields.get('dstport', 0)) if fields.get('dstport', '').isdigit() else 0
        
        # Protocol
        proto = fields.get('proto', '0')
        unified['protocol'] = int(proto) if proto.isdigit() else 0
        
        # Timestamp
        date = fields.get('date', '')
        time = fields.get('time', '')
        if date and time:
            try:
                unified['timestamp'] = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
            except:
                unified['timestamp'] = pd.NaT
        else:
            unified['timestamp'] = pd.NaT
        
        # Traffic metrics
        unified['byte_count_fwd'] = int(fields.get('sentbyte', 0)) if fields.get('sentbyte', '').isdigit() else 0
        unified['byte_count_bwd'] = int(fields.get('rcvdbyte', 0)) if fields.get('rcvdbyte', '').isdigit() else 0
        unified['packet_count_fwd'] = int(fields.get('sentpkt', 0)) if fields.get('sentpkt', '').isdigit() else 0
        unified['packet_count_bwd'] = int(fields.get('rcvdpkt', 0)) if fields.get('rcvdpkt', '').isdigit() else 0
        
        # Flow duration
        duration = fields.get('duration', '0')
        unified['flow_duration'] = int(duration) if duration.isdigit() else 0
        
        # Calculate total counts
        unified['byte_count_total'] = unified['byte_count_fwd'] + unified['byte_count_bwd']
        unified['packet_count_total'] = unified['packet_count_fwd'] + unified['packet_count_bwd']
        
        # Calculate derived metrics
        if unified['flow_duration'] > 0:
            unified['packets_per_second'] = unified['packet_count_total'] / unified['flow_duration']
            unified['bytes_per_second'] = unified['byte_count_total'] / unified['flow_duration']
        else:
            unified['packets_per_second'] = 0
            unified['bytes_per_second'] = 0
        
        # Calculate ratios
        if unified['byte_count_bwd'] > 0:
            unified['byte_ratio'] = unified['byte_count_fwd'] / unified['byte_count_bwd']
            unified['down_up_ratio'] = unified['byte_count_bwd'] / unified['byte_count_fwd']
        else:
            unified['byte_ratio'] = 0
            unified['down_up_ratio'] = 0
        
        if unified['packet_count_bwd'] > 0:
            unified['packet_ratio'] = unified['packet_count_fwd'] / unified['packet_count_bwd']
        else:
            unified['packet_ratio'] = 0
        
        # Calculate mean packet size
        if unified['packet_count_total'] > 0:
            unified['packet_length_mean'] = unified['byte_count_total'] / unified['packet_count_total']
        else:
            unified['packet_length_mean'] = 0
        
        # Application information
        service = fields.get('service', '')
        app = fields.get('app', '')
        
        # Use app field if available, otherwise service
        app_name = app if app and app not in ['tcp', 'udp'] else service
        
        # Map to unified application label
        unified['app_label'] = self.APP_LABEL_MAPPING.get(app_name, 'Unknown')
        unified['service_name'] = app_name  # Keep original for reference
        
        # Security context
        action = fields.get('action', 'accept')
        crlevel = fields.get('crlevel', '')
        threats = fields.get('threats', '')
        
        # Determine intent label
        if action == 'deny' or crlevel in ['high', 'critical'] or threats:
            unified['intent_label'] = 'Suspicious'
        else:
            unified['intent_label'] = 'Benign'
        
        # Additional context fields
        unified['user'] = fields.get('user', 'Unknown')
        unified['group'] = fields.get('group', 'Unknown')
        unified['src_country'] = fields.get('srccountry', 'Unknown')
        unified['dst_country'] = fields.get('dstcountry', 'Unknown')
        unified['policy_name'] = fields.get('policyname', 'Unknown')
        unified['action'] = action
        
        # VPN detection (initially unknown)
        unified['vpn_flag'] = -1  # -1 = unknown
        
        # Metadata
        unified['dataset_source'] = 'University_FortiAnalyzer'
        unified['source_file'] = fields.get('_source_file', 'unknown')
        
        # Session ID for potential duplicate detection
        unified['session_id'] = fields.get('sessionid', '')
        
        return unified
    
    def process_log_file(self, file_path: str) -> pd.DataFrame:
        """Process a single FortiAnalyzer log file"""
        logger.info(f"Processing log file: {file_path}")
        
        flows = []
        source_filename = Path(file_path).name
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    self.stats['total_lines'] += 1
                    
                    # Parse log line
                    fields = self.parse_log_line(line)
                    
                    if fields:
                        # Add source file info
                        fields['_source_file'] = source_filename
                        
                        # Map to unified schema
                        unified_flow = self.map_fields_to_unified(fields)
                        
                        # Only keep flows with valid IPs and non-zero traffic
                        if (unified_flow['src_ip'] and unified_flow['dst_ip'] and 
                            unified_flow['byte_count_total'] > 0):
                            flows.append(unified_flow)
                            self.stats['parsed_lines'] += 1
                    else:
                        self.stats['failed_lines'] += 1
                    
                    # Progress logging every 10000 lines
                    if line_num % 10000 == 0:
                        logger.info(f"Processed {line_num} lines, extracted {len(flows)} flows")
        
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return pd.DataFrame()
        
        if flows:
            df = pd.DataFrame(flows)
            logger.info(f"Extracted {len(df)} flows from {file_path}")
            return df
        else:
            logger.warning(f"No flows extracted from {file_path}")
            return pd.DataFrame()
    
    def process_multiple_files(self, input_pattern: str, output_csv: str) -> pd.DataFrame:
        """Process multiple log files matching a pattern"""
        
        # Find all matching files
        if '*' in input_pattern:
            files = glob.glob(input_pattern)
        else:
            files = [input_pattern] if os.path.exists(input_pattern) else []
        
        if not files:
            logger.error(f"No files found matching: {input_pattern}")
            return pd.DataFrame()
        
        logger.info(f"Found {len(files)} log file(s) to process")
        
        all_flows = []
        
        for file_path in files:
            df = self.process_log_file(file_path)
            if not df.empty:
                all_flows.append(df)
        
        if all_flows:
            # Combine all dataframes
            combined_df = pd.concat(all_flows, ignore_index=True)
            logger.info(f"Combined dataset: {len(combined_df)} flows")
            
            # Remove duplicates based on session_id
            if 'session_id' in combined_df.columns:
                initial_count = len(combined_df)
                combined_df = combined_df.drop_duplicates(subset=['session_id'], keep='first')
                removed = initial_count - len(combined_df)
                logger.info(f"Removed {removed} duplicate sessions")
            
            self.stats['unique_flows'] = len(combined_df)
            
            # Show statistics
            logger.info("\n=== Processing Statistics ===")
            logger.info(f"Total log lines: {self.stats['total_lines']}")
            logger.info(f"Successfully parsed: {self.stats['parsed_lines']}")
            logger.info(f"Failed to parse: {self.stats['failed_lines']}")
            logger.info(f"Unique flows: {self.stats['unique_flows']}")
            
            # Show label distribution
            logger.info("\n=== Application Label Distribution ===")
            print(combined_df['app_label'].value_counts().head(10))
            
            logger.info("\n=== Intent Label Distribution ===")
            print(combined_df['intent_label'].value_counts())
            
            logger.info("\n=== Top Services ===")
            print(combined_df['service_name'].value_counts().head(10))
            
            logger.info("\n=== User Groups ===")
            print(combined_df['group'].value_counts().head(10))
            
            # Save to CSV
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            combined_df.to_csv(output_csv, index=False)
            logger.info(f"\n✓ Saved to {output_csv}")
            
            return combined_df
        else:
            logger.error("No flows extracted from any files")
            return pd.DataFrame()
    
    def add_missing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add missing features with default values for unified schema"""
        
        # Features that we don't have in FortiAnalyzer logs
        missing_features = {
            'packet_length_min': 0,
            'packet_length_max': 0,
            'packet_length_std': 0,
            'packet_length_variance': 0,
            'mean_iat_fwd': 0,
            'mean_iat_bwd': 0,
            'mean_iat_total': 0,
            'std_iat_fwd': 0,
            'std_iat_bwd': 0,
            'std_iat_total': 0,
            'min_iat_total': 0,
            'max_iat_total': 0,
            'syn_flag_count': 0,
            'ack_flag_count': 0,
            'fin_flag_count': 0,
            'rst_flag_count': 0,
            'psh_flag_count': 0,
            'active_mean': 0,
            'active_std': 0,
            'idle_mean': 0,
            'idle_std': 0,
            'mtu': -1,
            'mss': -1,
            'ttl': -1,
            'window_size': -1,
            'tcp_options_count': 0,
            'protocol_hint': 'Unknown',
            'encryption_detected': -1,
            'entropy_score': -1.0,
        }
        
        for feature, default_value in missing_features.items():
            if feature not in df.columns:
                df[feature] = default_value
        
        return df


def main():
    parser = argparse.ArgumentParser(description="Process FortiAnalyzer/FortiGate Logs")
    parser.add_argument("--input", "-i", required=True, 
                       help="Input log file or pattern (e.g., 'logs/*.log' or '../fortianalyzer-traffic-*.log')")
    parser.add_argument("--output", "-o", required=True, 
                       help="Output CSV file path")
    parser.add_argument("--add-missing", action='store_true',
                       help="Add missing features with default values for unified schema")
    
    args = parser.parse_args()
    
    processor = FortiAnalyzerProcessor()
    df = processor.process_multiple_files(args.input, args.output)
    
    if not df.empty:
        # Add missing features if requested
        if args.add_missing:
            logger.info("\nAdding missing features for unified schema...")
            df = processor.add_missing_features(df)
            df.to_csv(args.output, index=False)
            logger.info(f"✓ Updated {args.output} with {len(df.columns)} features")
        
        logger.info(f"\n✓ Successfully processed {len(df)} flows")
        logger.info(f"✓ Output: {args.output}")
    else:
        logger.error("\n✗ Processing failed - no flows extracted")
        sys.exit(1)


if __name__ == "__main__":
    main()
