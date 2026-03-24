import os
import argparse
import pandas as pd
import csv
from scapy.all import rdpcap
import binascii

def packet_to_hex_tokens(packet, max_len=128):
    """
    Convert a scapy packet to a space-separated string of hex bytes (tokens)
    expected by ET-BERT's vocabulary.
    Filters out Ethernet/IP headers mostly by taking the raw payload or full packet bytes.
    """
    raw_bytes = bytes(packet)
    hex_str = binascii.hexlify(raw_bytes).decode('utf-8')
    
    # Split into byte-level tokens (every 2 hex characters = 1 byte)
    tokens = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
    
    # Truncate to max sequence length
    tokens = tokens[:max_len]
    
    return " ".join(tokens)

def prepare_dataset(pcap_dir, output_tsv, label_map=None, max_seq_len=128):
    """
    Reads PCAPs from a directory structure where each subfolder is a class,
    and converts them to ET-BERT fine-tuning TSV format.
    """
    print(f"Preparing dataset from {pcap_dir}...")
    dataset = []
    
    if label_map is None:
        # Auto-discover labels based on subdirectory names
        subdirs = [d for d in os.listdir(pcap_dir) if os.path.isdir(os.path.join(pcap_dir, d))]
        label_map = {name: idx for idx, name in enumerate(sorted(subdirs))}
    
    print(f"Label Mapping: {label_map}")
    
    for class_name, label_idx in label_map.items():
        class_dir = os.path.join(pcap_dir, class_name)
        if not os.path.exists(class_dir):
            continue
            
        for file in os.listdir(class_dir):
            if file.endswith('.pcap') or file.endswith('.pcapng'):
                filepath = os.path.join(class_dir, file)
                try:
                    packets = rdpcap(filepath)
                    for pkt in packets:
                        tokens = packet_to_hex_tokens(pkt, max_len=max_seq_len)
                        dataset.append([label_idx, tokens])
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    
    print(f"Generated {len(dataset)} samples. Saving to {output_tsv}...")
    
    os.makedirs(os.path.dirname(output_tsv), exist_ok=True)
    with open(output_tsv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['label', 'text_a'])
        writer.writerows(dataset)
        
    print("Data preparation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ET-BERT Data Preparation")
    parser.add_argument("--pcap_dir", type=str, required=True, help="Directory containing PCAP files grouped by class folders")
    parser.add_argument("--output_tsv", type=str, required=True, help="Path to save the generated TSV file")
    parser.add_argument("--max_seq_len", type=int, default=128, help="Maximum sequence length of packet bytes")
    
    args = parser.parse_args()
    prepare_dataset(args.pcap_dir, args.output_tsv, max_seq_len=args.max_seq_len)
