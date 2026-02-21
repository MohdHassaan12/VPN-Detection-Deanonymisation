"""
Feature Alignment and Harmonization Script
Aligns features across CIC-IDS2017, FortiAnalyzer, and PCAP datasets to unified schema
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureAligner:
    """Align features across different datasets to unified schema"""
    
    # CIC-IDS2017 column mapping to unified schema
    CIC_COLUMN_MAPPING = {
        # Basic identifiers
        ' Source IP': 'src_ip',
        ' Destination IP': 'dst_ip',
        ' Source Port': 'src_port',
        ' Destination Port': 'dst_port',
        ' Protocol': 'protocol',
        
        # Temporal
        ' Timestamp': 'timestamp',
        ' Flow Duration': 'flow_duration',
        
        # Packet counts
        ' Total Fwd Packets': 'packet_count_fwd',
        ' Total Backward Packets': 'packet_count_bwd',
        'Total Fwd Packets': 'packet_count_fwd',
        'Total Backward Packets': 'packet_count_bwd',
        
        # Byte counts
        ' Fwd Packets Length Total': 'byte_count_fwd',
        ' Bwd Packets Length Total': 'byte_count_bwd',
        'Total Length of Fwd Packets': 'byte_count_fwd',
        ' Total Length of Bwd Packets': 'byte_count_bwd',
        
        # Packet length statistics
        ' Fwd Packet Length Max': 'packet_length_max_fwd',
        ' Fwd Packet Length Min': 'packet_length_min_fwd',
        ' Fwd Packet Length Mean': 'packet_length_mean_fwd',
        ' Fwd Packet Length Std': 'packet_length_std_fwd',
        'Fwd Packet Length Max': 'packet_length_max_fwd',
        'Fwd Packet Length Min': 'packet_length_min_fwd',
        'Fwd Packet Length Mean': 'packet_length_mean_fwd',
        'Fwd Packet Length Std': 'packet_length_std_fwd',
        
        ' Bwd Packet Length Max': 'packet_length_max_bwd',
        ' Bwd Packet Length Min': 'packet_length_min_bwd',
        ' Bwd Packet Length Mean': 'packet_length_mean_bwd',
        ' Bwd Packet Length Std': 'packet_length_std_bwd',
        'Bwd Packet Length Max': 'packet_length_max_bwd',
        'Bwd Packet Length Min': 'packet_length_min_bwd',
        'Bwd Packet Length Mean': 'packet_length_mean_bwd',
        'Bwd Packet Length Std': 'packet_length_std_bwd',
        
        # Rate features
        ' Flow Packets/s': 'packets_per_second',
        ' Flow Bytes/s': 'bytes_per_second',
        'Flow Packets/s': 'packets_per_second',
        'Flow Bytes/s': 'bytes_per_second',
        
        # IAT features
        ' Flow IAT Mean': 'mean_iat_total',
        ' Flow IAT Std': 'std_iat_total',
        ' Flow IAT Max': 'max_iat_total',
        ' Flow IAT Min': 'min_iat_total',
        'Flow IAT Mean': 'mean_iat_total',
        'Flow IAT Std': 'std_iat_total',
        'Flow IAT Max': 'max_iat_total',
        'Flow IAT Min': 'min_iat_total',
        
        ' Fwd IAT Mean': 'mean_iat_fwd',
        ' Fwd IAT Std': 'std_iat_fwd',
        ' Fwd IAT Max': 'max_iat_fwd',
        ' Fwd IAT Min': 'min_iat_fwd',
        'Fwd IAT Mean': 'mean_iat_fwd',
        'Fwd IAT Std': 'std_iat_fwd',
        'Fwd IAT Max': 'max_iat_fwd',
        'Fwd IAT Min': 'min_iat_fwd',
        
        ' Bwd IAT Mean': 'mean_iat_bwd',
        ' Bwd IAT Std': 'std_iat_bwd',
        ' Bwd IAT Max': 'max_iat_bwd',
        ' Bwd IAT Min': 'min_iat_bwd',
        'Bwd IAT Mean': 'mean_iat_bwd',
        'Bwd IAT Std': 'std_iat_bwd',
        'Bwd IAT Max': 'max_iat_bwd',
        'Bwd IAT Min': 'min_iat_bwd',
        
        # TCP flags
        ' FIN Flag Count': 'fin_flag_count',
        ' SYN Flag Count': 'syn_flag_count',
        ' RST Flag Count': 'rst_flag_count',
        ' PSH Flag Count': 'psh_flag_count',
        ' ACK Flag Count': 'ack_flag_count',
        ' URG Flag Count': 'urg_flag_count',
        'FIN Flag Count': 'fin_flag_count',
        'SYN Flag Count': 'syn_flag_count',
        'RST Flag Count': 'rst_flag_count',
        'PSH Flag Count': 'psh_flag_count',
        'ACK Flag Count': 'ack_flag_count',
        'URG Flag Count': 'urg_flag_count',
        
        # Active/Idle time
        ' Active Mean': 'active_mean',
        ' Active Std': 'active_std',
        ' Active Max': 'active_max',
        ' Active Min': 'active_min',
        'Active Mean': 'active_mean',
        'Active Std': 'active_std',
        'Active Max': 'active_max',
        'Active Min': 'active_min',
        
        ' Idle Mean': 'idle_mean',
        ' Idle Std': 'idle_std',
        ' Idle Max': 'idle_max',
        ' Idle Min': 'idle_min',
        'Idle Mean': 'idle_mean',
        'Idle Std': 'idle_std',
        'Idle Max': 'idle_max',
        'Idle Min': 'idle_min',
        
        # Ratio features
        ' Down/Up Ratio': 'down_up_ratio',
        'Down/Up Ratio': 'down_up_ratio',
        
        # Labels
        'intent_label': 'intent_label',
        'app_label': 'app_label',
        'vpn_flag': 'vpn_flag',
        'dataset_source': 'dataset_source',
    }
    
    # Core features that MUST exist in final dataset
    CORE_FEATURES = [
        # Flow identifiers
        'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol',
        
        # Temporal
        'timestamp', 'flow_duration',
        
        # Packet counts
        'packet_count_fwd', 'packet_count_bwd', 'packet_count_total',
        
        # Byte counts
        'byte_count_fwd', 'byte_count_bwd', 'byte_count_total',
        
        # Packet size statistics
        'packet_length_min', 'packet_length_max', 
        'packet_length_mean', 'packet_length_std', 'packet_length_variance',
        
        # IAT statistics
        'mean_iat_fwd', 'mean_iat_bwd', 'mean_iat_total',
        'std_iat_fwd', 'std_iat_bwd', 'std_iat_total',
        'min_iat_total', 'max_iat_total',
        
        # Rate features
        'packets_per_second', 'bytes_per_second',
        
        # Ratio features
        'byte_ratio', 'packet_ratio', 'down_up_ratio',
        
        # TCP flags
        'syn_flag_count', 'ack_flag_count', 'fin_flag_count',
        'rst_flag_count', 'psh_flag_count',
        
        # Active/Idle
        'active_mean', 'active_std', 'idle_mean', 'idle_std',
        
        # VPN detection features
        'ttl', 'window_size', 'mtu', 'mss',
        
        # Labels
        'app_label', 'intent_label', 'vpn_flag',
        
        # Metadata
        'dataset_source', 'source_file',
    ]
    
    def __init__(self):
        self.stats = {
            'datasets_processed': 0,
            'features_added': 0,
            'features_renamed': 0,
            'rows_processed': 0
        }
    
    def align_cic_ids_2017(self, df: pd.DataFrame) -> pd.DataFrame:
        """Align CIC-IDS2017 dataset to unified schema"""
        logger.info("Aligning CIC-IDS2017 dataset...")
        
        # Rename columns FIRST
        df = df.rename(columns=self.CIC_COLUMN_MAPPING)
        self.stats['features_renamed'] += len(self.CIC_COLUMN_MAPPING)
        
        # Now calculate derived features using the NEW column names
        if 'packet_count_total' not in df.columns:
            if 'packet_count_fwd' in df.columns and 'packet_count_bwd' in df.columns:
                df['packet_count_total'] = df['packet_count_fwd'] + df['packet_count_bwd']
        
        if 'byte_count_total' not in df.columns:
            if 'byte_count_fwd' in df.columns and 'byte_count_bwd' in df.columns:
                df['byte_count_total'] = df['byte_count_fwd'] + df['byte_count_bwd']
        
        # Calculate overall packet length statistics from fwd/bwd
        if 'packet_length_min' not in df.columns:
            if 'packet_length_min_fwd' in df.columns and 'packet_length_min_bwd' in df.columns:
                df['packet_length_min'] = df[['packet_length_min_fwd', 'packet_length_min_bwd']].min(axis=1)
        
        if 'packet_length_max' not in df.columns:
            if 'packet_length_max_fwd' in df.columns and 'packet_length_max_bwd' in df.columns:
                df['packet_length_max'] = df[['packet_length_max_fwd', 'packet_length_max_bwd']].max(axis=1)
        
        if 'packet_length_mean' not in df.columns:
            if 'packet_length_mean_fwd' in df.columns and 'packet_length_mean_bwd' in df.columns:
                # Weighted average of fwd and bwd means
                total_packets = df['packet_count_fwd'] + df['packet_count_bwd']
                df['packet_length_mean'] = (
                    (df['packet_length_mean_fwd'] * df['packet_count_fwd'] + 
                     df['packet_length_mean_bwd'] * df['packet_count_bwd']) / 
                    total_packets.replace(0, 1)
                )
        
        if 'packet_length_std' not in df.columns:
            if 'packet_length_std_fwd' in df.columns and 'packet_length_std_bwd' in df.columns:
                # Use average of fwd and bwd std
                df['packet_length_std'] = (df['packet_length_std_fwd'] + df['packet_length_std_bwd']) / 2
        
        if 'packet_length_variance' not in df.columns:
            if 'packet_length_std' in df.columns:
                df['packet_length_variance'] = df['packet_length_std'] ** 2
        
        # Calculate ratios
        if 'byte_ratio' not in df.columns:
            if 'byte_count_fwd' in df.columns and 'byte_count_bwd' in df.columns:
                df['byte_ratio'] = df['byte_count_fwd'] / df['byte_count_bwd'].replace(0, 1)
        
        if 'packet_ratio' not in df.columns:
            if 'packet_count_fwd' in df.columns and 'packet_count_bwd' in df.columns:
                df['packet_ratio'] = df['packet_count_fwd'] / df['packet_count_bwd'].replace(0, 1)
        
        # Add timestamp if missing
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.NaT
        
        # Add source_file if missing
        if 'source_file' not in df.columns:
            df['source_file'] = 'cic_ids_2017'
        
        logger.info(f"CIC-IDS2017 aligned: {len(df)} rows, {len(df.columns)} features")
        
        return df
    
    def align_fortianalyzer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Align FortiAnalyzer dataset (already mostly aligned)"""
        logger.info("Aligning FortiAnalyzer dataset...")
        
        # FortiAnalyzer is already mostly aligned, just ensure derived features exist
        if 'packet_count_total' not in df.columns:
            df['packet_count_total'] = df['packet_count_fwd'] + df['packet_count_bwd']
        
        if 'byte_count_total' not in df.columns:
            df['byte_count_total'] = df['byte_count_fwd'] + df['byte_count_bwd']
        
        logger.info(f"FortiAnalyzer aligned: {len(df)} rows, {len(df.columns)} features")
        
        return df
    
    def align_pcap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Align PCAP dataset (already mostly aligned)"""
        logger.info("Aligning PCAP dataset...")
        
        # PCAP data is already aligned from our Scapy processor
        # Just ensure all derived features exist
        if 'packet_count_total' not in df.columns:
            df['packet_count_total'] = df['packet_count_fwd'] + df['packet_count_bwd']
        
        if 'byte_count_total' not in df.columns:
            df['byte_count_total'] = df['byte_count_fwd'] + df['byte_count_bwd']
        
        logger.info(f"PCAP aligned: {len(df)} rows, {len(df.columns)} features")
        
        return df
    
    def add_missing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add missing core features with appropriate defaults"""
        logger.info("Adding missing core features...")
        
        initial_cols = len(df.columns)
        
        for feature in self.CORE_FEATURES:
            if feature not in df.columns:
                # Determine default value based on feature type
                if feature.endswith('_count') or feature.endswith('_total'):
                    default = 0
                elif feature in ['ttl', 'window_size', 'mtu', 'mss']:
                    default = -1  # -1 indicates unknown
                elif feature in ['vpn_flag', 'encryption_detected']:
                    default = -1  # -1 = unknown, 0 = no, 1 = yes
                elif feature == 'timestamp':
                    default = pd.NaT
                elif feature in ['app_label', 'intent_label', 'source_file', 'protocol_hint']:
                    default = 'Unknown'
                elif feature == 'dataset_source':
                    default = df['dataset_source'].iloc[0] if 'dataset_source' in df.columns else 'Unknown'
                else:
                    default = 0.0
                
                df[feature] = default
                self.stats['features_added'] += 1
        
        added_features = len(df.columns) - initial_cols
        logger.info(f"Added {added_features} missing features")
        
        return df
    
    def standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types across features"""
        logger.info("Standardizing data types...")
        
        # Integer features
        int_features = [
            'src_port', 'dst_port', 'protocol',
            'packet_count_fwd', 'packet_count_bwd', 'packet_count_total',
            'byte_count_fwd', 'byte_count_bwd', 'byte_count_total',
            'syn_flag_count', 'ack_flag_count', 'fin_flag_count',
            'rst_flag_count', 'psh_flag_count',
            'ttl', 'window_size', 'mtu', 'mss', 'vpn_flag'
        ]
        
        for col in int_features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Float features
        float_features = [
            'flow_duration', 'packet_length_min', 'packet_length_max',
            'packet_length_mean', 'packet_length_std', 'packet_length_variance',
            'mean_iat_fwd', 'mean_iat_bwd', 'mean_iat_total',
            'std_iat_fwd', 'std_iat_bwd', 'std_iat_total',
            'min_iat_total', 'max_iat_total',
            'packets_per_second', 'bytes_per_second',
            'byte_ratio', 'packet_ratio', 'down_up_ratio',
            'active_mean', 'active_std', 'idle_mean', 'idle_std'
        ]
        
        for col in float_features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
        
        # String features
        string_features = ['src_ip', 'dst_ip', 'app_label', 'intent_label', 
                          'dataset_source', 'source_file']
        
        for col in string_features:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', 'Unknown')
        
        # Timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        logger.info("Data types standardized")
        
        return df
    
    def reorder_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reorder columns for consistency"""
        logger.info("Reordering columns...")
        
        # Define column order
        column_order = [
            # Identifiers
            'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol',
            
            # Temporal
            'timestamp', 'flow_duration',
            
            # Packet counts
            'packet_count_fwd', 'packet_count_bwd', 'packet_count_total',
            
            # Byte counts
            'byte_count_fwd', 'byte_count_bwd', 'byte_count_total',
            
            # Packet size statistics
            'packet_length_min', 'packet_length_max', 
            'packet_length_mean', 'packet_length_std', 'packet_length_variance',
            
            # IAT statistics
            'mean_iat_fwd', 'mean_iat_bwd', 'mean_iat_total',
            'std_iat_fwd', 'std_iat_bwd', 'std_iat_total',
            'min_iat_total', 'max_iat_total',
            
            # Rate features
            'packets_per_second', 'bytes_per_second',
            
            # Ratio features
            'byte_ratio', 'packet_ratio', 'down_up_ratio',
            
            # TCP flags
            'syn_flag_count', 'ack_flag_count', 'fin_flag_count',
            'rst_flag_count', 'psh_flag_count',
            
            # Active/Idle
            'active_mean', 'active_std', 'idle_mean', 'idle_std',
            
            # VPN detection
            'ttl', 'window_size', 'mtu', 'mss',
            
            # Labels
            'app_label', 'intent_label', 'vpn_flag',
            
            # Metadata
            'dataset_source', 'source_file',
        ]
        
        # Get existing columns in order, then append any remaining columns
        existing_ordered = [col for col in column_order if col in df.columns]
        remaining = [col for col in df.columns if col not in column_order]
        
        final_order = existing_ordered + remaining
        
        df = df[final_order]
        
        logger.info(f"Columns reordered: {len(final_order)} total columns")
        
        return df
    
    def process_dataset(self, input_path: str, dataset_type: str, output_path: str) -> pd.DataFrame:
        """Process and align a single dataset"""
        logger.info(f"Processing {dataset_type} dataset from {input_path}")
        
        # Load dataset
        df = pd.read_csv(input_path)
        initial_rows = len(df)
        initial_cols = len(df.columns)
        
        logger.info(f"Loaded: {initial_rows:,} rows, {initial_cols} columns")
        
        # Apply dataset-specific alignment
        if dataset_type == 'cic_ids_2017':
            df = self.align_cic_ids_2017(df)
        elif dataset_type == 'fortianalyzer':
            df = self.align_fortianalyzer(df)
        elif dataset_type == 'pcap':
            df = self.align_pcap(df)
        else:
            logger.warning(f"Unknown dataset type: {dataset_type}")
        
        # Add missing features
        df = self.add_missing_features(df)
        
        # Standardize data types
        df = self.standardize_data_types(df)
        
        # Reorder columns
        df = self.reorder_columns(df)
        
        # Save aligned dataset
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        self.stats['datasets_processed'] += 1
        self.stats['rows_processed'] += len(df)
        
        logger.info(f"✓ Aligned dataset saved: {output_path}")
        logger.info(f"  Final: {len(df):,} rows, {len(df.columns)} columns")
        
        return df
    
    def generate_report(self, output_dir: str):
        """Generate alignment report"""
        report = {
            'alignment_statistics': self.stats,
            'core_features_count': len(self.CORE_FEATURES),
            'core_features': self.CORE_FEATURES,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        report_path = os.path.join(output_dir, 'alignment_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✓ Alignment report saved: {report_path}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Align features across datasets")
    parser.add_argument("--cic-ids", required=True, help="Path to CIC-IDS2017 CSV")
    parser.add_argument("--fortianalyzer", required=True, help="Path to FortiAnalyzer CSV")
    parser.add_argument("--pcap", required=True, help="Path to PCAP flows CSV")
    parser.add_argument("--output-dir", "-o", required=True, help="Output directory for aligned datasets")
    
    args = parser.parse_args()
    
    aligner = FeatureAligner()
    
    logger.info("="*70)
    logger.info("FEATURE ALIGNMENT PIPELINE")
    logger.info("="*70)
    
    # Process each dataset
    datasets = [
        (args.cic_ids, 'cic_ids_2017', 'cic_ids_2017_aligned.csv'),
        (args.fortianalyzer, 'fortianalyzer', 'university_fortianalyzer_aligned.csv'),
        (args.pcap, 'pcap', 'university_pcap_aligned.csv'),
    ]
    
    aligned_dfs = []
    
    for input_path, dataset_type, output_filename in datasets:
        output_path = os.path.join(args.output_dir, output_filename)
        df = aligner.process_dataset(input_path, dataset_type, output_path)
        aligned_dfs.append(df)
    
    # Generate report
    aligner.generate_report(args.output_dir)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("ALIGNMENT COMPLETE")
    logger.info("="*70)
    logger.info(f"Datasets processed: {aligner.stats['datasets_processed']}")
    logger.info(f"Total rows processed: {aligner.stats['rows_processed']:,}")
    logger.info(f"Features renamed: {aligner.stats['features_renamed']}")
    logger.info(f"Features added: {aligner.stats['features_added']}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
