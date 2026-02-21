"""
CIC-IDS2017 Dataset Processor
Processes pre-labeled Parquet files and standardizes labels for intent classification
"""

import os
import sys
import argparse
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CICIDS2017Processor:
    """Process CIC-IDS2017 dataset"""
    
    # Label mapping for standardization
    LABEL_MAPPING = {
        'BENIGN': 'Benign',
        'Benign': 'Benign',
        'Bot': 'Botnet',
        'DDoS': 'DDoS',
        'DoS Hulk': 'DoS',
        'DoS GoldenEye': 'DoS',
        'DoS slowloris': 'DoS',
        'DoS Slowhttptest': 'DoS',
        'FTP-Patator': 'BruteForce',
        'SSH-Patator': 'BruteForce',
        'PortScan': 'Portscan',
        'Infiltration': 'Infiltration',
        'Web Attack – Brute Force': 'Web_Attack',
        'Web Attack – XSS': 'Web_Attack',
        'Web Attack – Sql Injection': 'Web_Attack',
        'Heartbleed': 'Web_Attack'
    }
    
    def __init__(self):
        self.processed_flows = []
    
    def process_parquet_file(self, file_path: str) -> pd.DataFrame:
        """
        Process a single Parquet file from CIC-IDS2017
        
        Args:
            file_path: Path to Parquet file
            
        Returns:
            Processed DataFrame
        """
        logger.info(f"Processing {file_path}")
        
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"Loaded {len(df)} records from {file_path}")
            
            # Get label from filename
            filename = Path(file_path).stem
            if '-no-metadata' in filename:
                label = filename.replace('-no-metadata', '').replace('-', ' ')
            else:
                label = filename
            
            # Map label
            if label in self.LABEL_MAPPING:
                df['intent_label'] = self.LABEL_MAPPING[label]
            else:
                df['intent_label'] = label
                logger.warning(f"Unmapped label: {label}")
            
            # Add metadata
            df['dataset_source'] = 'CIC-IDS2017'
            df['vpn_flag'] = 0  # No VPN in this dataset
            df['app_label'] = 'Unknown'  # Application unknown
            
            # Standardize column names
            df = self._standardize_columns(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return pd.DataFrame()
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to match unified schema"""
        
        # Column mapping (CIC-IDS2017 format to unified format)
        column_mapping = {
            ' Source IP': 'src_ip',
            ' Destination IP': 'dst_ip',
            ' Source Port': 'src_port',
            ' Destination Port': 'dst_port',
            ' Protocol': 'protocol',
            ' Flow Duration': 'flow_duration',
            ' Total Fwd Packets': 'packet_count_fwd',
            ' Total Backward Packets': 'packet_count_bwd',
            'Total Length of Fwd Packets': 'byte_count_fwd',
            ' Total Length of Bwd Packets': 'byte_count_bwd',
            ' Fwd Packet Length Mean': 'packet_length_mean',
            ' Fwd Packet Length Std': 'packet_length_std',
            ' Flow Packets/s': 'packets_per_second',
            ' Flow Bytes/s': 'bytes_per_second',
            ' Flow IAT Mean': 'mean_iat_total',
            ' Flow IAT Std': 'std_iat_total',
            'Fwd IAT Mean': 'mean_iat_fwd',
            ' Bwd IAT Mean': 'mean_iat_bwd',
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)
        
        return df
    
    def process_directory(self, input_dir: str, output_csv: str) -> pd.DataFrame:
        """
        Process all Parquet files in CIC-IDS2017 directory
        
        Args:
            input_dir: Input directory containing Parquet files
            output_csv: Output CSV file path
            
        Returns:
            Combined DataFrame
        """
        input_path = Path(input_dir)
        parquet_files = list(input_path.glob("*-no-metadata.parquet"))
        
        logger.info(f"Found {len(parquet_files)} Parquet files in {input_dir}")
        
        all_data = []
        
        for pq_file in parquet_files:
            df = self.process_parquet_file(str(pq_file))
            if not df.empty:
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Combined dataset: {len(combined_df)} records")
            
            # Show label distribution
            logger.info("\nLabel Distribution:")
            print(combined_df['intent_label'].value_counts())
            
            # Save to CSV
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            combined_df.to_csv(output_csv, index=False)
            logger.info(f"✓ Saved to {output_csv}")
            
            return combined_df
        else:
            logger.error("No data processed")
            return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="Process CIC-IDS2017 Dataset")
    parser.add_argument("--input", "-i", required=True, help="Input directory (CIC-IDS2017)")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file")
    
    args = parser.parse_args()
    
    processor = CICIDS2017Processor()
    df = processor.process_directory(args.input, args.output)
    
    if not df.empty:
        logger.info(f"✓ Successfully processed {len(df)} records")
    else:
        logger.error("✗ Processing failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
