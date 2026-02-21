"""
Dataset Statistics and Visualization Generator
Generates comprehensive statistics and visualizations for preprocessed datasets
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


class DatasetStatistics:
    """Generate statistics and visualizations for datasets"""
    
    def __init__(self, input_csv: str, output_dir: str):
        self.input_csv = input_csv
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Loading dataset: {input_csv}")
        self.df = pd.read_csv(input_csv)
        logger.info(f"Dataset shape: {self.df.shape}")
    
    def generate_basic_stats(self) -> dict:
        """Generate basic dataset statistics"""
        logger.info("Generating basic statistics...")
        
        stats = {
            'total_records': len(self.df),
            'total_features': len(self.df.columns),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024**2,
            'missing_values': self.df.isnull().sum().sum(),
            'duplicate_records': self.df.duplicated().sum()
        }
        
        # Data types
        stats['data_types'] = self.df.dtypes.value_counts().to_dict()
        
        return stats
    
    def analyze_labels(self):
        """Analyze label distributions"""
        logger.info("Analyzing label distributions...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # App label distribution
        if 'app_label' in self.df.columns:
            app_counts = self.df['app_label'].value_counts()
            axes[0, 0].bar(range(len(app_counts)), app_counts.values)
            axes[0, 0].set_xticks(range(len(app_counts)))
            axes[0, 0].set_xticklabels(app_counts.index, rotation=45, ha='right')
            axes[0, 0].set_title('Application Label Distribution')
            axes[0, 0].set_ylabel('Count')
        
        # Intent label distribution
        if 'intent_label' in self.df.columns:
            intent_counts = self.df['intent_label'].value_counts()
            axes[0, 1].bar(range(len(intent_counts)), intent_counts.values)
            axes[0, 1].set_xticks(range(len(intent_counts)))
            axes[0, 1].set_xticklabels(intent_counts.index, rotation=45, ha='right')
            axes[0, 1].set_title('Intent Label Distribution')
            axes[0, 1].set_ylabel('Count')
        
        # VPN flag distribution
        if 'vpn_flag' in self.df.columns:
            vpn_counts = self.df['vpn_flag'].value_counts()
            axes[1, 0].pie(vpn_counts.values, labels=['Non-VPN', 'VPN'], autopct='%1.1f%%')
            axes[1, 0].set_title('VPN vs Non-VPN Traffic')
        
        # Dataset source distribution
        if 'dataset_source' in self.df.columns:
            source_counts = self.df['dataset_source'].value_counts()
            axes[1, 1].barh(range(len(source_counts)), source_counts.values)
            axes[1, 1].set_yticks(range(len(source_counts)))
            axes[1, 1].set_yticklabels(source_counts.index)
            axes[1, 1].set_title('Dataset Source Distribution')
            axes[1, 1].set_xlabel('Count')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'label_distributions.png', dpi=300, bbox_inches='tight')
        logger.info(f"✓ Saved: label_distributions.png")
        plt.close()
    
    def analyze_features(self):
        """Analyze feature distributions"""
        logger.info("Analyzing feature distributions...")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        # Feature correlation heatmap
        if len(numeric_cols) > 0:
            # Select subset of features for correlation (too many features = unreadable)
            feature_subset = numeric_cols[:30] if len(numeric_cols) > 30 else numeric_cols
            
            corr_matrix = self.df[feature_subset].corr()
            
            plt.figure(figsize=(14, 12))
            sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0, 
                       square=True, linewidths=0.5)
            plt.title('Feature Correlation Heatmap (Top 30 Features)')
            plt.tight_layout()
            plt.savefig(self.output_dir / 'feature_correlations.png', dpi=300, bbox_inches='tight')
            logger.info(f"✓ Saved: feature_correlations.png")
            plt.close()
    
    def analyze_flow_statistics(self):
        """Analyze flow-level statistics"""
        logger.info("Analyzing flow statistics...")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        
        # Packet count distribution
        if 'packet_count_total' in self.df.columns:
            axes[0, 0].hist(self.df['packet_count_total'].clip(upper=1000), bins=50, edgecolor='black')
            axes[0, 0].set_title('Packet Count Distribution')
            axes[0, 0].set_xlabel('Packets')
            axes[0, 0].set_ylabel('Frequency')
        
        # Byte count distribution
        if 'byte_count_total' in self.df.columns:
            axes[0, 1].hist(np.log10(self.df['byte_count_total'] + 1), bins=50, edgecolor='black')
            axes[0, 1].set_title('Byte Count Distribution (log scale)')
            axes[0, 1].set_xlabel('log10(Bytes)')
            axes[0, 1].set_ylabel('Frequency')
        
        # Flow duration distribution
        if 'flow_duration' in self.df.columns:
            axes[0, 2].hist(self.df['flow_duration'].clip(upper=300), bins=50, edgecolor='black')
            axes[0, 2].set_title('Flow Duration Distribution')
            axes[0, 2].set_xlabel('Duration (seconds)')
            axes[0, 2].set_ylabel('Frequency')
        
        # Packet size distribution
        if 'packet_length_mean' in self.df.columns:
            axes[1, 0].hist(self.df['packet_length_mean'].clip(upper=2000), bins=50, edgecolor='black')
            axes[1, 0].set_title('Mean Packet Size Distribution')
            axes[1, 0].set_xlabel('Bytes')
            axes[1, 0].set_ylabel('Frequency')
        
        # IAT distribution
        if 'mean_iat_total' in self.df.columns:
            axes[1, 1].hist(np.log10(self.df['mean_iat_total'] + 1), bins=50, edgecolor='black')
            axes[1, 1].set_title('Mean IAT Distribution (log scale)')
            axes[1, 1].set_xlabel('log10(IAT)')
            axes[1, 1].set_ylabel('Frequency')
        
        # Byte ratio distribution
        if 'byte_ratio' in self.df.columns:
            axes[1, 2].hist(self.df['byte_ratio'].clip(upper=10), bins=50, edgecolor='black')
            axes[1, 2].set_title('Byte Ratio Distribution')
            axes[1, 2].set_xlabel('Ratio (Fwd/Bwd)')
            axes[1, 2].set_ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'flow_statistics.png', dpi=300, bbox_inches='tight')
        logger.info(f"✓ Saved: flow_statistics.png")
        plt.close()
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        logger.info("Generating summary report...")
        
        report = {
            'basic_stats': self.generate_basic_stats(),
            'label_distributions': {},
            'feature_statistics': {},
            'data_quality': {}
        }
        
        # Label distributions
        if 'app_label' in self.df.columns:
            report['label_distributions']['app_labels'] = self.df['app_label'].value_counts().to_dict()
        
        if 'intent_label' in self.df.columns:
            report['label_distributions']['intent_labels'] = self.df['intent_label'].value_counts().to_dict()
        
        if 'vpn_flag' in self.df.columns:
            report['label_distributions']['vpn_distribution'] = self.df['vpn_flag'].value_counts().to_dict()
        
        # Feature statistics
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        report['feature_statistics']['numeric_features'] = len(numeric_cols)
        report['feature_statistics']['categorical_features'] = len(self.df.select_dtypes(include=['object']).columns)
        
        # Data quality
        report['data_quality']['missing_values_per_column'] = self.df.isnull().sum().to_dict()
        report['data_quality']['duplicate_rows'] = int(self.df.duplicated().sum())
        
        # Save report
        report_path = self.output_dir / 'summary_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✓ Saved: summary_report.json")
        
        return report
    
    def generate_all(self):
        """Generate all statistics and visualizations"""
        logger.info("="*60)
        logger.info("Generating Dataset Statistics and Visualizations")
        logger.info("="*60)
        
        # Generate visualizations
        self.analyze_labels()
        self.analyze_features()
        self.analyze_flow_statistics()
        
        # Generate summary report
        report = self.generate_summary_report()
        
        logger.info("="*60)
        logger.info("✓ Statistics Generation Complete!")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("="*60)
        
        # Print summary
        print("\n" + "="*60)
        print("DATASET SUMMARY")
        print("="*60)
        print(f"Total Records: {report['basic_stats']['total_records']:,}")
        print(f"Total Features: {report['basic_stats']['total_features']}")
        print(f"Memory Usage: {report['basic_stats']['memory_usage_mb']:.2f} MB")
        print(f"Missing Values: {report['basic_stats']['missing_values']}")
        print(f"Duplicate Records: {report['basic_stats']['duplicate_records']}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Generate Dataset Statistics")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file")
    parser.add_argument("--output-dir", "-o", required=True, help="Output directory for statistics")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    stats_generator = DatasetStatistics(args.input, args.output_dir)
    stats_generator.generate_all()


if __name__ == "__main__":
    main()
