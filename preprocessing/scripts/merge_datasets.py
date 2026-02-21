"""
Phase 2: Dataset Merger and Preprocessor
Merges aligned datasets with label normalization and creates final unified dataset
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json
from sklearn.model_selection import train_test_split
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase2Merger:
    """Phase 2: Merge aligned datasets and create unified dataset"""
    
    # Label normalization mappings
    INTENT_LABEL_MAPPING = {
        # CIC-IDS2017 labels (with day names)
        'DoS Wednesday': 'DoS',
        'DDoS Friday': 'DDoS',
        'Benign Monday': 'Benign',
        'Botnet Friday': 'Botnet',
        'Infiltration Thursday': 'Infiltration',
        'WebAttacks Thursday': 'Web_Attack',
        'Portscan Friday': 'Portscan',
        
        # Already normalized
        'Benign': 'Benign',
        'DoS': 'DoS',
        'DDoS': 'DDoS',
        'Botnet': 'Botnet',
        'BruteForce': 'BruteForce',
        'Portscan': 'Portscan',
        'Infiltration': 'Infiltration',
        'Web_Attack': 'Web_Attack',
        'Suspicious': 'Suspicious',
        'Malicious': 'Malicious',
        'Unknown': 'Unknown',
    }
    
    def __init__(self):
        self.stats = {
            'initial_rows': 0,
            'after_merge': 0,
            'after_dedup': 0,
            'after_cleaning': 0,
            'duplicates_removed': 0,
            'outliers_removed': 0,
            'null_rows_removed': 0,
        }
    
    def load_aligned_datasets(self, aligned_dir: str) -> Dict[str, pd.DataFrame]:
        """Load all aligned datasets from Phase 1"""
        logger.info("="*70)
        logger.info("PHASE 2: DATASET MERGING PIPELINE")
        logger.info("="*70)
        logger.info(f"\nLoading aligned datasets from {aligned_dir}...")
        
        datasets = {}
        aligned_path = Path(aligned_dir)
        
        # Load CIC-IDS2017
        cic_path = aligned_path / "cic_ids_2017_aligned.csv"
        if cic_path.exists():
            logger.info(f"Loading CIC-IDS2017...")
            datasets['cic_ids_2017'] = pd.read_csv(cic_path)
            logger.info(f"  ✓ Loaded: {len(datasets['cic_ids_2017']):,} rows")
        else:
            logger.warning(f"  ✗ Not found: {cic_path}")
        
        # Load FortiAnalyzer
        forti_path = aligned_path / "university_fortianalyzer_aligned.csv"
        if forti_path.exists():
            logger.info(f"Loading FortiAnalyzer...")
            datasets['fortianalyzer'] = pd.read_csv(forti_path)
            logger.info(f"  ✓ Loaded: {len(datasets['fortianalyzer']):,} rows")
        else:
            logger.warning(f"  ✗ Not found: {forti_path}")
        
        # Load PCAP
        pcap_path = aligned_path / "university_pcap_aligned.csv"
        if pcap_path.exists():
            logger.info(f"Loading University PCAP...")
            datasets['pcap'] = pd.read_csv(pcap_path)
            logger.info(f"  ✓ Loaded: {len(datasets['pcap']):,} rows")
        else:
            logger.warning(f"  ✗ Not found: {pcap_path}")
        
        if not datasets:
            logger.error("No datasets loaded! Please run Phase 1 first.")
            sys.exit(1)
        
        total_rows = sum(len(df) for df in datasets.values())
        self.stats['initial_rows'] = total_rows
        logger.info(f"\n✓ Loaded {len(datasets)} datasets with {total_rows:,} total rows")
        
        return datasets
    
    def normalize_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize intent labels across datasets"""
        logger.info("\nNormalizing labels...")
        
        if 'intent_label' in df.columns:
            initial_labels = df['intent_label'].unique()
            logger.info(f"  Initial labels: {sorted(initial_labels)}")
            
            # Apply mapping
            df['intent_label'] = df['intent_label'].map(
                lambda x: self.INTENT_LABEL_MAPPING.get(x, x)
            )
            
            final_labels = df['intent_label'].unique()
            logger.info(f"  Normalized labels: {sorted(final_labels)}")
            logger.info(f"  Label distribution:")
            for label, count in df['intent_label'].value_counts().items():
                logger.info(f"    {label}: {count:,} ({count/len(df)*100:.1f}%)")
        
        return df
    
    def merge_datasets(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Merge all datasets vertically"""
        logger.info("\n" + "="*70)
        logger.info("STEP 1: MERGING DATASETS")
        logger.info("="*70)
        
        all_dfs = []
        
        for name, df in datasets.items():
            logger.info(f"\nProcessing {name}:")
            logger.info(f"  Rows: {len(df):,}")
            logger.info(f"  Columns: {len(df.columns)}")
            
            # Normalize labels
            df = self.normalize_labels(df)
            all_dfs.append(df)
        
        # Concatenate vertically
        logger.info(f"\nConcatenating {len(all_dfs)} datasets...")
        merged_df = pd.concat(all_dfs, ignore_index=True)
        
        self.stats['after_merge'] = len(merged_df)
        logger.info(f"✓ Merged dataset: {len(merged_df):,} rows, {len(merged_df.columns)} columns")
        
        return merged_df
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate flows"""
        logger.info("\n" + "="*70)
        logger.info("STEP 2: REMOVING DUPLICATES")
        logger.info("="*70)
        
        initial_count = len(df)
        
        # Method 1: Based on flow 5-tuple
        if all(col in df.columns for col in ['src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol']):
            logger.info("Removing duplicates based on 5-tuple (src_ip, dst_ip, src_port, dst_port, protocol)...")
            
            # Create flow signature
            df['_flow_sig'] = (
                df['src_ip'].astype(str) + ':' + df['src_port'].astype(str) + '-' +
                df['dst_ip'].astype(str) + ':' + df['dst_port'].astype(str) + '-' +
                df['protocol'].astype(str)
            )
            
            df = df.drop_duplicates(subset=['_flow_sig'], keep='first')
            df = df.drop(columns=['_flow_sig'])
        else:
            logger.info("5-tuple columns not found, using full row duplicate detection...")
            df = df.drop_duplicates(keep='first')
        
        removed_count = initial_count - len(df)
        self.stats['duplicates_removed'] = removed_count
        self.stats['after_dedup'] = len(df)
        
        logger.info(f"✓ Removed {removed_count:,} duplicate flows ({removed_count/initial_count*100:.2f}%)")
        logger.info(f"✓ Remaining: {len(df):,} flows")
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
        """Handle missing values"""
        logger.info("\n" + "="*70)
        logger.info("STEP 3: HANDLING MISSING VALUES")
        logger.info("="*70)
        
        initial_count = len(df)
        
        # Check missing values
        missing_summary = df.isnull().sum()
        missing_cols = missing_summary[missing_summary > 0]
        
        if len(missing_cols) > 0:
            logger.info(f"Found {len(missing_cols)} columns with missing values:")
            for col, count in missing_cols.items():
                logger.info(f"  {col}: {count:,} ({count/len(df)*100:.1f}%)")
        else:
            logger.info("✓ No missing values found!")
        
        # Remove rows with too many missing values
        missing_ratio = df.isnull().sum(axis=1) / len(df.columns)
        rows_to_remove = (missing_ratio > threshold).sum()
        
        if rows_to_remove > 0:
            logger.info(f"\nRemoving {rows_to_remove:,} rows with >{threshold*100}% missing values...")
            df = df[missing_ratio <= threshold]
        
        # Fill remaining missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        categorical_columns = df.select_dtypes(include=['object']).columns
        
        # Fill numeric with 0
        for col in numeric_columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna(0)
        
        # Fill categorical with 'Unknown'
        for col in categorical_columns:
            if df[col].isnull().any():
                df[col] = df[col].fillna('Unknown')
        
        removed = initial_count - len(df)
        self.stats['null_rows_removed'] = removed
        
        logger.info(f"✓ Missing values handled. Rows removed: {removed:,}")
        logger.info(f"✓ Remaining: {len(df):,} flows")
        
        return df
    
    def remove_outliers(self, df: pd.DataFrame, factor: float = 3.0) -> pd.DataFrame:
        """Remove outliers using IQR method"""
        logger.info("\n" + "="*70)
        logger.info("STEP 4: REMOVING OUTLIERS")
        logger.info("="*70)
        
        initial_count = len(df)
        
        # Select numeric columns (exclude IDs, ports, flags)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        cols_to_check = [
            col for col in numeric_cols 
            if col not in ['src_port', 'dst_port', 'protocol', 'vpn_flag', 
                          'ttl', 'window_size', 'mtu', 'mss']
            and not col.endswith('_count')
            and not col.endswith('_flag')
        ]
        
        logger.info(f"Checking {len(cols_to_check)} columns for outliers (IQR factor={factor})...")
        
        for col in cols_to_check:
            if df[col].std() == 0:  # Skip constant columns
                continue
            
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            if IQR == 0:  # Skip if no variance
                continue
            
            lower_bound = Q1 - factor * IQR
            upper_bound = Q3 + factor * IQR
            
            outliers_before = len(df)
            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
            outliers_removed = outliers_before - len(df)
            
            if outliers_removed > 0:
                logger.info(f"  {col}: removed {outliers_removed:,} outliers")
        
        removed_count = initial_count - len(df)
        self.stats['outliers_removed'] = removed_count
        self.stats['after_cleaning'] = len(df)
        
        logger.info(f"✓ Removed {removed_count:,} outlier rows ({removed_count/initial_count*100:.2f}%)")
        logger.info(f"✓ Remaining: {len(df):,} flows")
        
        return df
    
    def validate_data_quality(self, df: pd.DataFrame):
        """Validate final data quality"""
        logger.info("\n" + "="*70)
        logger.info("STEP 5: DATA QUALITY VALIDATION")
        logger.info("="*70)
        
        # Check 1: No missing values in critical columns
        critical_cols = ['src_ip', 'dst_ip', 'protocol', 'intent_label']
        missing_critical = df[critical_cols].isnull().sum()
        
        logger.info("\n✓ Critical columns check:")
        for col in critical_cols:
            if col in df.columns:
                missing = missing_critical[col] if col in missing_critical.index else 0
                status = "✓ OK" if missing == 0 else f"✗ {missing} missing"
                logger.info(f"  {col}: {status}")
        
        # Check 2: Valid port ranges
        if 'src_port' in df.columns and 'dst_port' in df.columns:
            invalid_ports = ((df['src_port'] < 0) | (df['src_port'] > 65535) |
                           (df['dst_port'] < 0) | (df['dst_port'] > 65535)).sum()
            logger.info(f"\n✓ Port ranges: {invalid_ports} invalid (should be 0)")
        
        # Check 3: Protocol values
        if 'protocol' in df.columns:
            valid_protocols = df['protocol'].isin([1, 6, 17]).sum()
            logger.info(f"✓ Protocols: {valid_protocols:,} valid TCP/UDP/ICMP ({valid_protocols/len(df)*100:.1f}%)")
        
        # Check 4: Label distribution
        if 'intent_label' in df.columns:
            logger.info(f"\n✓ Intent label distribution:")
            for label, count in df['intent_label'].value_counts().items():
                logger.info(f"  {label}: {count:,} ({count/len(df)*100:.1f}%)")
        
        if 'app_label' in df.columns:
            non_unknown = (df['app_label'] != 'Unknown').sum()
            logger.info(f"\n✓ Application labels: {non_unknown:,} known ({non_unknown/len(df)*100:.1f}%)")
    
    def create_stage_datasets(self, df: pd.DataFrame, output_dir: str):
        """Create Stage-1 and Stage-2 datasets"""
        logger.info("\n" + "="*70)
        logger.info("STEP 6: CREATING STAGE-SPECIFIC DATASETS")
        logger.info("="*70)
        
        # Stage 1: Application Classification (only flows with known app_label)
        stage1_df = df[df['app_label'] != 'Unknown'].copy()
        logger.info(f"\n✓ Stage-1 (Application Classification):")
        logger.info(f"  Total flows: {len(stage1_df):,}")
        logger.info(f"  Percentage of total: {len(stage1_df)/len(df)*100:.1f}%")
        logger.info(f"  Application labels:")
        for label, count in stage1_df['app_label'].value_counts().items():
            logger.info(f"    {label}: {count:,}")
        
        stage1_path = Path(output_dir) / "Stage1_App_Classification.csv"
        stage1_df.to_csv(stage1_path, index=False)
        logger.info(f"  Saved: {stage1_path}")
        
        # Stage 2: Intent Classification (all flows)
        stage2_df = df.copy()
        logger.info(f"\n✓ Stage-2 (Intent Classification):")
        logger.info(f"  Total flows: {len(stage2_df):,}")
        logger.info(f"  Intent labels:")
        for label, count in stage2_df['intent_label'].value_counts().items():
            logger.info(f"    {label}: {count:,}")
        
        stage2_path = Path(output_dir) / "Stage2_Intent_Classification.csv"
        stage2_df.to_csv(stage2_path, index=False)
        logger.info(f"  Saved: {stage2_path}")
        
        return stage1_df, stage2_df
    
    def split_dataset(self, df: pd.DataFrame, label_col: str, output_dir: str):
        """Split dataset into train/val/test"""
        logger.info("\n" + "="*70)
        logger.info("STEP 7: TRAIN/VAL/TEST SPLIT")
        logger.info("="*70)
        
        logger.info(f"\nSplitting on '{label_col}' with stratification...")
        logger.info(f"Split ratio: 70% train / 15% val / 15% test")
        
        # First split: train vs (val + test)
        train_df, temp_df = train_test_split(
            df, 
            test_size=0.3, 
            stratify=df[label_col],
            random_state=42
        )
        
        # Second split: val vs test
        val_df, test_df = train_test_split(
            temp_df,
            test_size=0.5,
            stratify=temp_df[label_col],
            random_state=42
        )
        
        logger.info(f"\n✓ Split complete:")
        logger.info(f"  Train: {len(train_df):,} flows ({len(train_df)/len(df)*100:.1f}%)")
        logger.info(f"  Val:   {len(val_df):,} flows ({len(val_df)/len(df)*100:.1f}%)")
        logger.info(f"  Test:  {len(test_df):,} flows ({len(test_df)/len(df)*100:.1f}%)")
        
        # Save splits
        train_path = Path(output_dir) / "train.csv"
        val_path = Path(output_dir) / "val.csv"
        test_path = Path(output_dir) / "test.csv"
        
        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)
        
        logger.info(f"\n✓ Saved splits:")
        logger.info(f"  {train_path}")
        logger.info(f"  {val_path}")
        logger.info(f"  {test_path}")
        
        return train_df, val_df, test_df
    
    def generate_report(self, df: pd.DataFrame, output_dir: str):
        """Generate final processing report"""
        logger.info("\n" + "="*70)
        logger.info("GENERATING FINAL REPORT")
        logger.info("="*70)
        
        report = {
            'processing_timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'final_dataset': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'features': list(df.columns),
                'data_quality': {
                    'missing_values': df.isnull().sum().to_dict(),
                    'data_types': df.dtypes.astype(str).to_dict(),
                }
            },
            'label_distributions': {
                'intent_labels': df['intent_label'].value_counts().to_dict() if 'intent_label' in df.columns else {},
                'app_labels': df['app_label'].value_counts().to_dict() if 'app_label' in df.columns else {},
                'vpn_flags': df['vpn_flag'].value_counts().to_dict() if 'vpn_flag' in df.columns else {},
            }
        }
        
        report_path = Path(output_dir) / "phase2_merge_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✓ Report saved: {report_path}")
        
        return report
    
    def process(self, aligned_dir: str, output_dir: str, skip_outliers: bool = False):
        """Main Phase 2 processing pipeline"""
        
        # Load aligned datasets
        datasets = self.load_aligned_datasets(aligned_dir)
        
        # Merge datasets
        merged_df = self.merge_datasets(datasets)
        
        # Remove duplicates
        merged_df = self.remove_duplicates(merged_df)
        
        # Handle missing values
        merged_df = self.handle_missing_values(merged_df)
        
        # Remove outliers (optional)
        if not skip_outliers:
            merged_df = self.remove_outliers(merged_df, factor=3.0)
        else:
            logger.info("\n⚠️  Skipping outlier removal (--skip-outliers flag)")
            self.stats['after_cleaning'] = len(merged_df)
        
        # Validate data quality
        self.validate_data_quality(merged_df)
        
        # Save unified dataset
        unified_path = Path(output_dir) / "Unified_Dataset.csv"
        logger.info(f"\n✓ Saving unified dataset: {unified_path}")
        merged_df.to_csv(unified_path, index=False)
        logger.info(f"  Size: {len(merged_df):,} rows × {len(merged_df.columns)} columns")
        
        # Create stage-specific datasets
        stage1_df, stage2_df = self.create_stage_datasets(merged_df, output_dir)
        
        # Split Stage-2 dataset
        train_df, val_df, test_df = self.split_dataset(stage2_df, 'intent_label', output_dir)
        
        # Generate report
        self.generate_report(merged_df, output_dir)
        
        # Print final summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final summary"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 2 COMPLETE - FINAL SUMMARY")
        logger.info("="*70)
        logger.info(f"\n✓ Processing Statistics:")
        logger.info(f"  Initial rows:              {self.stats['initial_rows']:,}")
        logger.info(f"  After merge:               {self.stats['after_merge']:,}")
        logger.info(f"  After deduplication:       {self.stats['after_dedup']:,}")
        logger.info(f"  After cleaning:            {self.stats['after_cleaning']:,}")
        logger.info(f"\n  Duplicates removed:        {self.stats['duplicates_removed']:,}")
        logger.info(f"  Null rows removed:         {self.stats['null_rows_removed']:,}")
        logger.info(f"  Outliers removed:          {self.stats['outliers_removed']:,}")
        logger.info(f"\n  Data retention:            {self.stats['after_cleaning']/self.stats['initial_rows']*100:.1f}%")
        logger.info("\n" + "="*70)
        logger.info("✓ All datasets ready for model training!")
        logger.info("="*70)


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Merge Aligned Datasets")
    parser.add_argument("--aligned-dir", default="outputs/aligned", 
                       help="Directory containing aligned datasets")
    parser.add_argument("--output-dir", "-o", default="outputs",
                       help="Output directory for merged datasets")
    parser.add_argument("--skip-outliers", action='store_true',
                       help="Skip outlier removal step")
    
    args = parser.parse_args()
    
    # Validate paths
    if not os.path.exists(args.aligned_dir):
        logger.error(f"Aligned directory not found: {args.aligned_dir}")
        logger.error("Please run Phase 1 (feature alignment) first!")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run Phase 2
    merger = Phase2Merger()
    merger.process(args.aligned_dir, args.output_dir, args.skip_outliers)


if __name__ == "__main__":
    main()
