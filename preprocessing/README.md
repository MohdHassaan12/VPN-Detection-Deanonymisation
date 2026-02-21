# Preprocessing Pipeline - Quick Start Guide

## Overview
This preprocessing pipeline unifies multiple network traffic datasets (VNAT, ISCXVPN2016, CIC-IDS2017, USTC-TFC2016, UNSW, and custom PCAPs) into standardized CSV format for ML training.

## Setup

### 1. Install Dependencies
```bash
cd preprocessing
pip install -r requirements.txt
```

### 2. Verify Installation
```bash
python -c "import nfstream; print('NFStream OK')"
python -c "import pandas; print('Pandas OK')"
```

---

## Processing Individual Datasets

### Process CIC-IDS2017 (Already in Parquet)
```bash
python scripts/process_cicids2017.py \
    --input ../CIC-IDS2017/ \
    --output outputs/cic_ids_2017.csv
```

### Process USTC-TFC2016 (PCAP files)
```bash
# Process all (benign + malware)
python scripts/process_ustc.py \
    --input ../USTC-TFC2016-master/ \
    --output outputs/ \
    --type all

# Or process separately
python scripts/process_ustc.py --input ../USTC-TFC2016-master/ --output outputs/ --type benign
python scripts/process_ustc.py --input ../USTC-TFC2016-master/ --output outputs/ --type malware
```

### Process Custom PCAP Files
```bash
# Single PCAP file
python scripts/pcap_to_flow.py \
    --input path/to/file.pcap \
    --output outputs/processed_flow.csv

# Directory of PCAPs
python scripts/pcap_to_flow.py \
    --input path/to/pcap/directory/ \
    --output outputs/processed_flows/ \
    --pattern "*.pcap"
```

---

## Merging Datasets

### 1. Update Configuration
Edit `configs/merge_config.yaml` to specify:
- Dataset paths
- Label mappings
- Feature selection
- Preprocessing parameters

### 2. Run Merger
```bash
python scripts/merge_datasets.py \
    --config configs/merge_config.yaml
```

This will create:
- `outputs/Unified_Dataset.csv` - Complete merged dataset
- `outputs/Stage1_App_Classification.csv` - Application classification data
- `outputs/Stage2_Intent_Classification.csv` - Intent classification data
- `outputs/train.csv`, `val.csv`, `test.csv` - Train/validation/test splits

---

## Generate Statistics & Visualizations

```bash
python scripts/dataset_statistics.py \
    --input outputs/Unified_Dataset.csv \
    --output-dir outputs/statistics/
```

Generates:
- Label distribution plots
- Feature correlation heatmaps
- Flow statistics visualizations
- Summary report (JSON)

---

## Complete Pipeline Example

```bash
# Step 1: Process CIC-IDS2017
echo "Processing CIC-IDS2017..."
python scripts/process_cicids2017.py \
    -i ../CIC-IDS2017/ \
    -o outputs/cic_ids_2017.csv

# Step 2: Process USTC-TFC2016
echo "Processing USTC-TFC2016..."
python scripts/process_ustc.py \
    -i ../USTC-TFC2016-master/ \
    -o outputs/ \
    --type all

# Step 3: Merge datasets
echo "Merging datasets..."
python scripts/merge_datasets.py \
    -c configs/merge_config.yaml

# Step 4: Generate statistics
echo "Generating statistics..."
python scripts/dataset_statistics.py \
    -i outputs/Unified_Dataset.csv \
    -o outputs/statistics/

echo "✓ Pipeline complete! Check outputs/ directory"
```

---

## Output Structure

```
preprocessing/
├── outputs/
│   ├── Unified_Dataset.csv              # Complete merged dataset
│   ├── Stage1_App_Classification.csv    # Application classification
│   ├── Stage2_Intent_Classification.csv # Intent classification
│   ├── train.csv                        # Training set (70%)
│   ├── val.csv                          # Validation set (15%)
│   ├── test.csv                         # Test set (15%)
│   ├── cic_ids_2017.csv                # Processed CIC-IDS2017
│   ├── ustc_combined.csv               # Processed USTC-TFC2016
│   ├── label_mapping.json              # Label encoding map
│   ├── feature_statistics.csv          # Feature stats
│   └── statistics/                     # Visualizations & reports
│       ├── label_distributions.png
│       ├── feature_correlations.png
│       ├── flow_statistics.png
│       └── summary_report.json
├── logs/
│   └── preprocessing.log               # Processing logs
└── configs/
    └── merge_config.yaml               # Configuration file
```

---

## Troubleshooting

### NFStream Installation Issues
If NFStream fails to install:
```bash
# macOS with Homebrew
brew install libpcap

# Then try again
pip install nfstream
```

### PyShark Not Available
PyShark is optional for deep packet inspection. If not available, VPN features will use placeholders.

### Memory Issues with Large Files
For large datasets, use Dask or process in chunks:
```python
# Modify in merge_datasets.py
use_dask: true
chunk_size: 10000
```

---

## Configuration Options

### NFStream Parameters (in merge_config.yaml)
```yaml
nfstream:
  idle_timeout: 120        # Flow idle timeout (seconds)
  active_timeout: 1800     # Flow active timeout (seconds)
  statistical_analysis: true
  decode_tunnels: false
```

### Data Cleaning
```yaml
cleaning:
  remove_duplicates: true
  missing_value_threshold: 0.5  # Remove rows with >50% missing
  outlier_method: "IQR"
  outlier_factor: 3.0
```

### Class Balancing (SMOTE)
```yaml
balancing:
  method: "SMOTE"
  target_ratio: 0.2
  k_neighbors: 5
```

---

## Next Steps

After preprocessing:
1. ✅ **Unified dataset created** → Ready for model training
2. ✅ **Features extracted** → ~65 features per flow
3. ✅ **Labels standardized** → Consistent across datasets
4. ✅ **Train/val/test split** → Stratified 70/15/15

Proceed to:
- **Stage-1 Model**: Application classification (CNN)
- **Stage-2 Model**: Intent classification (XGBoost/RandomForest)

---

## Support & Documentation

- **Full Guide**: `docs/preprocessing/PREPROCESSING_GUIDE.md`
- **Feature Extraction**: `scripts/feature_extractor.py`
- **Configuration**: `configs/merge_config.yaml`
- **Logs**: `logs/preprocessing.log`

---

**Last Updated**: November 9, 2025
