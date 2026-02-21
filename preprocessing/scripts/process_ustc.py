"""
USTC-TFC2016 Dataset Processor
Processes both Benign (application) and Malware traffic
"""

import os
import sys
import argparse
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List
from pcap_to_flow import PCAPProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class USTCTFC2016Processor:
    """Process USTC-TFC2016 dataset"""
    
    # Benign application mapping
    BENIGN_APP_MAPPING = {
        'BitTorrent': 'P2P',
        'Facetime': 'VoIP',
        'FTP': 'File_Transfer',
        'Gmail': 'Email',
        'MySQL': 'Browsing',
        'Outlook': 'Email',
        'Skype': 'VoIP',
        'SMB': 'File_Transfer',
        'Weibo': 'Chat',
        'WorldOfWarcraft': 'Gaming'
    }
    
    # Malware type mapping
    MALWARE_MAPPING = {
        'Cridex': 'Malware',
        'Geodo': 'Malware',
        'Htbot': 'Botnet',
        'Miuref': 'Malware',
        'Neris': 'Botnet',
        'Nsis-ay': 'Malware',
        'Shifu': 'Malware',
        'Tinba': 'Malware',
        'Virut': 'Malware',
        'Zeus': 'Malware'
    }
    
    def __init__(self):
        self.pcap_processor = PCAPProcessor()
    
    def process_benign_traffic(self, input_dir: str, output_csv: str) -> pd.DataFrame:
        """
        Process benign application traffic
        
        Args:
            input_dir: USTC-TFC2016-master/Benign directory
            output_csv: Output CSV file
            
        Returns:
            Processed DataFrame
        """
        logger.info("Processing USTC-TFC2016 Benign Traffic...")
        
        benign_path = Path(input_dir) / "Benign"
        if not benign_path.exists():
            benign_path = Path(input_dir)
        
        all_flows = []
        
        # Process each application's PCAP files
        for app_name, app_label in self.BENIGN_APP_MAPPING.items():
            logger.info(f"Processing {app_name}...")
            
            # Find PCAP files for this application
            pcap_files = list(benign_path.glob(f"{app_name}*.pcap"))
            pcap_files.extend(list(benign_path.glob(f"{app_name}/*.pcap")))
            
            for pcap_file in pcap_files:
                df = self.pcap_processor.process_pcap(str(pcap_file))
                
                if not df.empty:
                    # Add labels
                    df['app_label'] = app_label
                    df['intent_label'] = 'Benign'
                    df['application_name'] = app_name
                    df['dataset_source'] = 'USTC-TFC2016'
                    df['vpn_flag'] = 0
                    
                    all_flows.append(df)
                    logger.info(f"  ✓ {app_name}: {len(df)} flows")
        
        if all_flows:
            combined_df = pd.concat(all_flows, ignore_index=True)
            logger.info(f"Total benign flows: {len(combined_df)}")
            
            # Save
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            combined_df.to_csv(output_csv, index=False)
            logger.info(f"✓ Saved to {output_csv}")
            
            return combined_df
        else:
            logger.warning("No benign flows processed")
            return pd.DataFrame()
    
    def process_malware_traffic(self, input_dir: str, output_csv: str) -> pd.DataFrame:
        """
        Process malware traffic
        
        Args:
            input_dir: USTC-TFC2016-master/Malware directory
            output_csv: Output CSV file
            
        Returns:
            Processed DataFrame
        """
        logger.info("Processing USTC-TFC2016 Malware Traffic...")
        
        malware_path = Path(input_dir) / "Malware"
        if not malware_path.exists():
            malware_path = Path(input_dir)
        
        all_flows = []
        
        # Process each malware type
        for malware_name, intent_label in self.MALWARE_MAPPING.items():
            logger.info(f"Processing {malware_name}...")
            
            # Find PCAP files for this malware
            pcap_files = list(malware_path.glob(f"{malware_name}*.pcap"))
            
            for pcap_file in pcap_files:
                df = self.pcap_processor.process_pcap(str(pcap_file))
                
                if not df.empty:
                    # Add labels
                    df['app_label'] = 'Unknown'
                    df['intent_label'] = intent_label
                    df['malware_name'] = malware_name
                    df['dataset_source'] = 'USTC-TFC2016'
                    df['vpn_flag'] = 0
                    
                    all_flows.append(df)
                    logger.info(f"  ✓ {malware_name}: {len(df)} flows")
        
        if all_flows:
            combined_df = pd.concat(all_flows, ignore_index=True)
            logger.info(f"Total malware flows: {len(combined_df)}")
            
            # Save
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            combined_df.to_csv(output_csv, index=False)
            logger.info(f"✓ Saved to {output_csv}")
            
            return combined_df
        else:
            logger.warning("No malware flows processed")
            return pd.DataFrame()
    
    def process_all(self, input_dir: str, output_dir: str) -> Dict[str, pd.DataFrame]:
        """
        Process both benign and malware traffic
        
        Args:
            input_dir: USTC-TFC2016-master directory
            output_dir: Output directory
            
        Returns:
            Dictionary with 'benign' and 'malware' DataFrames
        """
        results = {}
        
        # Process benign
        benign_output = os.path.join(output_dir, "ustc_benign.csv")
        results['benign'] = self.process_benign_traffic(input_dir, benign_output)
        
        # Process malware
        malware_output = os.path.join(output_dir, "ustc_malware.csv")
        results['malware'] = self.process_malware_traffic(input_dir, malware_output)
        
        # Combine both
        if not results['benign'].empty or not results['malware'].empty:
            combined = pd.concat([results['benign'], results['malware']], ignore_index=True)
            combined_output = os.path.join(output_dir, "ustc_combined.csv")
            combined.to_csv(combined_output, index=False)
            logger.info(f"✓ Combined dataset saved: {combined_output}")
            results['combined'] = combined
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Process USTC-TFC2016 Dataset")
    parser.add_argument("--input", "-i", required=True, help="Input directory (USTC-TFC2016-master)")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--type", choices=['benign', 'malware', 'all'], default='all',
                       help="Type of traffic to process")
    
    args = parser.parse_args()
    
    processor = USTCTFC2016Processor()
    
    if args.type == 'benign':
        output_csv = os.path.join(args.output, "ustc_benign.csv")
        df = processor.process_benign_traffic(args.input, output_csv)
    elif args.type == 'malware':
        output_csv = os.path.join(args.output, "ustc_malware.csv")
        df = processor.process_malware_traffic(args.input, output_csv)
    else:
        results = processor.process_all(args.input, args.output)
        df = results.get('combined', pd.DataFrame())
    
    if not df.empty:
        logger.info(f"✓ Successfully processed {len(df)} records")
    else:
        logger.error("✗ Processing failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
