import os
import argparse
import numpy as np
import csv

def convert_npy_to_tsv(npy_x_path, npy_y_path, output_tsv):
    print(f"Loading {npy_x_path} and {npy_y_path}...")
    try:
        x_data = np.load(npy_x_path, allow_pickle=True)
        y_data = np.load(npy_y_path, allow_pickle=True)
    except Exception as e:
        print(f"Error loading numpy files: {e}")
        return
        
    if len(x_data) != len(y_data):
        print("Mismatch in X and Y lengths!")
        return
        
    print(f"Loaded {len(x_data)} samples. Writing to {output_tsv}...")
    
    os.makedirs(os.path.dirname(output_tsv), exist_ok=True)
    
    with open(output_tsv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['label', 'text_a'])
        
        for i in range(len(x_data)):
            # Ensure label is int and text is string
            label = int(y_data[i])
            text = str(x_data[i])
            writer.writerow([label, text])
            
    print(f"Finished writing {output_tsv}")

def main():
    parser = argparse.ArgumentParser(description="Convert ET-BERT numpy datasets to TSV")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing x_payload_*.npy and y_*.npy files")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save TSV files")
    args = parser.parse_args()
    
    splits = ['train', 'valid', 'test']
    
    for split in splits:
        x_file = os.path.join(args.input_dir, f'x_payload_{split}.npy')
        y_file = os.path.join(args.input_dir, f'y_{split}.npy')
        out_file = os.path.join(args.output_dir, f'{split}_dataset.tsv')
        
        if os.path.exists(x_file) and os.path.exists(y_file):
            convert_npy_to_tsv(x_file, y_file, out_file)
        else:
            print(f"Warning: Missing files for {split} split. Looked for {x_file} and {y_file}")

if __name__ == "__main__":
    main()
