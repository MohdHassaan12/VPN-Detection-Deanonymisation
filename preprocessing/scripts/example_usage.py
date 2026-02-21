#!/usr/bin/env python3
"""
Example Usage of Complete PCAP Preprocessing Pipeline

This script demonstrates different ways to use the pipeline.
"""

import sys
from pathlib import Path

# Import the processor
from complete_pcap_processor import (
    Config,
    CompletePCAPProcessor,
    setup_logging
)


def example_1_single_file():
    """Example 1: Process a single PCAP file"""
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Processing Single PCAP File")
    print("="*80)
    
    # Setup
    logger = setup_logging(log_file='../logs/example_1.log')
    config = Config()
    processor = CompletePCAPProcessor(config, logger)
    
    # Process PCAP
    pcap_file = "../../USTC-TFC2016-master/Benign/Gmail.pcap"
    output_file = "../outputs/example_1_gmail.csv"
    
    if not Path(pcap_file).exists():
        print(f"⚠️  PCAP file not found: {pcap_file}")
        print("   Please update the path to an existing PCAP file.")
        return
    
    df = processor.process_single_pcap(pcap_file, output_file)
    
    if not df.empty:
        print(f"\n✓ Success! Processed {len(df)} flows")
        print(f"✓ Output saved to: {output_file}")
        print(f"\nFirst 5 rows:")
        print(df[['flow_id', 'packet_count_total', 'byte_count_total', 'flow_duration']].head())
    else:
        print("\n✗ Failed to process PCAP")


def example_2_batch_processing():
    """Example 2: Process multiple PCAP files"""
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Batch Processing Multiple PCAPs")
    print("="*80)
    
    # Setup
    logger = setup_logging(log_file='../logs/example_2.log')
    config = Config()
    config.EXTRACT_ENTROPY = False  # Disable for faster processing
    processor = CompletePCAPProcessor(config, logger)
    
    # Process directory
    input_dir = "../../USTC-TFC2016-master/Benign/"
    output_dir = "../outputs/example_2_batch/"
    
    if not Path(input_dir).exists():
        print(f"⚠️  Directory not found: {input_dir}")
        print("   Please update the path to an existing directory.")
        return
    
    df = processor.process_directory(input_dir, output_dir, pattern="*.pcap")
    
    if not df.empty:
        print(f"\n✓ Success! Processed {len(df)} total flows")
        print(f"✓ Output directory: {output_dir}")
        print(f"\nFlow statistics:")
        print(df[['source_file', 'packet_count_total', 'byte_count_total']].groupby('source_file').agg({
            'packet_count_total': 'sum',
            'byte_count_total': 'sum'
        }))
    else:
        print("\n✗ No flows extracted")


def example_3_fast_mode():
    """Example 3: Fast processing mode (no deep packet inspection)"""
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Fast Processing Mode")
    print("="*80)
    
    # Setup with minimal features
    logger = setup_logging(log_file='../logs/example_3.log')
    config = Config()
    config.EXTRACT_TCP_HANDSHAKE = False  # Disable
    config.EXTRACT_ENTROPY = False         # Disable
    config.ENRICH_IP_REPUTATION = False    # Disable
    
    processor = CompletePCAPProcessor(config, logger)
    
    # Process PCAP
    pcap_file = "../../USTC-TFC2016-master/Benign/Gmail.pcap"
    output_file = "../outputs/example_3_fast.csv"
    
    if not Path(pcap_file).exists():
        print(f"⚠️  PCAP file not found: {pcap_file}")
        return
    
    import time
    start = time.time()
    df = processor.process_single_pcap(pcap_file, output_file)
    elapsed = time.time() - start
    
    if not df.empty:
        print(f"\n✓ Success! Processed {len(df)} flows in {elapsed:.2f} seconds")
        print(f"✓ Average: {len(df)/elapsed:.1f} flows/second")
    else:
        print("\n✗ Failed to process PCAP")


def example_4_analyze_results():
    """Example 4: Analyze extracted features"""
    
    print("\n" + "="*80)
    print("EXAMPLE 4: Analyzing Extracted Features")
    print("="*80)
    
    import pandas as pd
    
    # Load processed data
    csv_file = "../outputs/example_1_gmail.csv"
    
    if not Path(csv_file).exists():
        print(f"⚠️  CSV file not found: {csv_file}")
        print("   Run Example 1 first to generate the data.")
        return
    
    df = pd.read_csv(csv_file)
    
    print(f"\n📊 Dataset Overview:")
    print(f"   - Total Flows: {len(df)}")
    print(f"   - Total Features: {len(df.columns)}")
    print(f"   - Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    print(f"\n📈 Flow Statistics:")
    print(f"   - Total Packets: {df['packet_count_total'].sum():,}")
    print(f"   - Total Bytes: {df['byte_count_total'].sum():,}")
    print(f"   - Avg Flow Duration: {df['flow_duration'].mean():.2f} seconds")
    print(f"   - Avg Packets per Flow: {df['packet_count_total'].mean():.1f}")
    
    print(f"\n🔍 VPN Indicators:")
    if 'encryption_detected' in df.columns:
        encrypted = df['encryption_detected'].sum()
        print(f"   - Encrypted Flows: {encrypted} ({encrypted/len(df)*100:.1f}%)")
    
    if 'protocol_hint' in df.columns:
        vpn_ports = df['protocol_hint'].sum()
        print(f"   - VPN Port Usage: {vpn_ports} flows ({vpn_ports/len(df)*100:.1f}%)")
    
    print(f"\n📋 Top 10 Destination Ports:")
    print(df['dst_port'].value_counts().head(10))
    
    print(f"\n🎯 Feature Completeness:")
    missing = df.isnull().sum().sort_values(ascending=False).head(10)
    if missing.sum() > 0:
        print(missing)
    else:
        print("   ✓ No missing values!")


def main():
    """Run all examples"""
    
    print("\n" + "="*80)
    print("COMPLETE PCAP PREPROCESSING PIPELINE - EXAMPLES")
    print("="*80)
    print("\nThese examples demonstrate different usage patterns.")
    print("Choose an example to run:\n")
    print("  1. Process single PCAP file")
    print("  2. Batch process multiple PCAPs")
    print("  3. Fast mode (minimal features)")
    print("  4. Analyze extracted features")
    print("  5. Run all examples")
    print("  0. Exit")
    
    try:
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == '1':
            example_1_single_file()
        elif choice == '2':
            example_2_batch_processing()
        elif choice == '3':
            example_3_fast_mode()
        elif choice == '4':
            example_4_analyze_results()
        elif choice == '5':
            example_1_single_file()
            example_2_batch_processing()
            example_3_fast_mode()
            example_4_analyze_results()
        elif choice == '0':
            print("\nExiting...")
            sys.exit(0)
        else:
            print(f"\n❌ Invalid choice: {choice}")
            sys.exit(1)
        
        print("\n" + "="*80)
        print("✓ Example completed successfully!")
        print("="*80 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
