"""
PCAP to Flow Converter using NFStream
Converts PCAP files to flow-level CSV with statistical features
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
from tqdm import tqdm

try:
    from nfstream import NFStreamer
except ImportError:
    print("ERROR: NFStream not installed. Install with: pip install nfstream")
    sys.exit(1)

from feature_extractor import FlowFeatureExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PCAPProcessor:
    """Process PCAP files and extract flow features"""
    
    def __init__(self, idle_timeout: int = 120, active_timeout: int = 1800):
        self.idle_timeout = idle_timeout
        self.active_timeout = active_timeout
        self.feature_extractor = FlowFeatureExtractor()
    
    def process_pcap(self, pcap_path: str, output_csv: Optional[str] = None) -> pd.DataFrame:
        """
        Process a single PCAP file
        
        Args:
            pcap_path: Path to PCAP file
            output_csv: Optional output CSV path
            
        Returns:
            DataFrame with extracted flows
        """
        logger.info(f"Processing PCAP: {pcap_path}")
        
        try:
            # Extract flows using NFStream
            streamer = NFStreamer(
                source=pcap_path,
                decode_tunnels=False,
                statistical_analysis=True,
                idle_timeout=self.idle_timeout,
                active_timeout=self.active_timeout,
                n_dissections=20
            )
            
            # Convert to DataFrame
            logger.info("Converting flows to DataFrame...")
            df = streamer.to_pandas()
            
            if df.empty:
                logger.warning(f"No flows extracted from {pcap_path}")
                return pd.DataFrame()
            
            logger.info(f"Extracted {len(df)} flows from {pcap_path}")
            
            # Add basic flow identifiers
            df['flow_id'] = df.apply(
                lambda row: f"{row['src_ip']}:{row['src_port']}-{row['dst_ip']}:{row['dst_port']}-{row['protocol']}",
                axis=1
            )
            
            # Extract additional features
            df = self.feature_extractor.extract_all_features(df)
            
            # Save to CSV if output path provided
            if output_csv:
                os.makedirs(os.path.dirname(output_csv), exist_ok=True)
                df.to_csv(output_csv, index=False)
                logger.info(f"Saved to {output_csv}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing {pcap_path}: {e}")
            return pd.DataFrame()
    
    def process_directory(self, input_dir: str, output_dir: str, pattern: str = "*.pcap") -> pd.DataFrame:
        """
        Process all PCAP files in a directory
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            pattern: File pattern to match (default: *.pcap)
            
        Returns:
            Combined DataFrame of all flows
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all PCAP files
        pcap_files = list(input_path.rglob(pattern))
        logger.info(f"Found {len(pcap_files)} PCAP files in {input_dir}")
        
        all_flows = []
        
        for pcap_file in tqdm(pcap_files, desc="Processing PCAPs"):
            # Generate output filename
            relative_path = pcap_file.relative_to(input_path)
            output_csv = output_path / relative_path.with_suffix('.csv')
            output_csv.parent.mkdir(parents=True, exist_ok=True)
            
            # Process PCAP
            df = self.process_pcap(str(pcap_file), str(output_csv))
            
            if not df.empty:
                # Add source file information
                df['source_file'] = str(pcap_file.name)
                df['source_path'] = str(relative_path.parent)
                all_flows.append(df)
        
        # Combine all flows
        if all_flows:
            combined_df = pd.concat(all_flows, ignore_index=True)
            logger.info(f"Total flows extracted: {len(combined_df)}")
            
            # Save combined dataset
            combined_path = output_path / "combined_flows.csv"
            combined_df.to_csv(combined_path, index=False)
            logger.info(f"Combined dataset saved to {combined_path}")
            
            return combined_df
        else:
            logger.warning("No flows extracted from any files")
            return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description="Convert PCAP to Flow CSV")
    parser.add_argument("--input", "-i", required=True, help="Input PCAP file or directory")
    parser.add_argument("--output", "-o", required=True, help="Output CSV file or directory")
    parser.add_argument("--idle-timeout", type=int, default=120, help="Idle timeout in seconds")
    parser.add_argument("--active-timeout", type=int, default=1800, help="Active timeout in seconds")
    parser.add_argument("--pattern", default="*.pcap", help="File pattern for directory mode")
    
    args = parser.parse_args()
    
    processor = PCAPProcessor(
        idle_timeout=args.idle_timeout,
        active_timeout=args.active_timeout
    )
    
    # Check if input is file or directory
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single file mode
        logger.info("Processing single PCAP file...")
        df = processor.process_pcap(args.input, args.output)
        
        if not df.empty:
            logger.info(f"✓ Successfully processed {len(df)} flows")
            logger.info(f"✓ Output: {args.output}")
        else:
            logger.error("✗ Failed to process PCAP")
            sys.exit(1)
    
    elif input_path.is_dir():
        # Directory mode
        logger.info("Processing directory of PCAP files...")
        df = processor.process_directory(args.input, args.output, args.pattern)
        
        if not df.empty:
            logger.info(f"✓ Successfully processed {len(df)} total flows")
            logger.info(f"✓ Output directory: {args.output}")
        else:
            logger.error("✗ No flows extracted")
            sys.exit(1)
    
    else:
        logger.error(f"Input path does not exist: {args.input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
