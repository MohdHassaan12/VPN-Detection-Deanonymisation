# Data Preprocessing Documentation

## Overview
Complete preprocessing system for unifying multiple network traffic datasets into standardized CSV format for ML training.

## Quick Links
- **[Preprocessing Guide](PREPROCESSING_GUIDE.md)** - Complete methodology and pipeline
- **[Feature Reference](FEATURE_REFERENCE.md)** - All 65+ features explained
- **[Quick Start](../../preprocessing/README.md)** - Get started in 5 minutes

## What's Included

### 1. Dataset Processors
Individual processors for each dataset:
- ✅ **CIC-IDS2017** - Pre-labeled Parquet files → CSV
- ✅ **USTC-TFC2016** - PCAP files → Labeled flows (Benign + Malware)
- ✅ **VNAT** - Application-based traffic (Coming soon)
- ✅ **ISCXVPN2016** - VPN/non-VPN traffic (Coming soon)
- ✅ **UNSW-NB15** - Network intrusion data (Coming soon)
- ✅ **Custom PCAPs** - University captured traffic

### 2. Feature Extraction
Comprehensive feature engineering:
- **65+ features** extracted per flow
- Flow statistics (packet counts, bytes, duration)
- Timing features (IAT, jitter, periodicity)
- TCP features (flags, connection patterns)
- VPN detection features (MSS, TTL, entropy)
- Behavioral features (login attempts, bot detection)
- IP intelligence (reputation, geolocation) - Optional

### 3. Data Fusion
Unified preprocessing pipeline:
- Label standardization across datasets
- Duplicate removal
- Missing value handling
- Outlier detection (IQR method)
- Class balancing (SMOTE)
- Train/val/test splitting (70/15/15)

### 4. Output Datasets
Ready-to-use training data:
- **Unified_Dataset.csv** - All datasets merged
- **Stage1_App_Classification.csv** - Application classification (9 classes)
- **Stage2_Intent_Classification.csv** - Intent classification (11 classes)
- **train.csv, val.csv, test.csv** - Stratified splits

## Pipeline Architecture

```
Raw Data Sources
│
├── CIC-IDS2017/*.parquet ──────┐
├── USTC-TFC2016/*.pcap ────────┤
├── VNAT/*.pcap ────────────────┤
├── ISCXVPN2016/*.pcap ─────────┤
└── Custom/*.pcap ──────────────┤
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Flow Extraction      │
                    │  (NFStream/PyShark)   │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Feature Engineering  │
                    │  (65+ features)       │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Label Standardization│
                    │  (App + Intent)       │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Data Cleaning        │
                    │  (Duplicates, Missing)│
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Dataset Merge        │
                    │  (All sources unified)│
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Train/Val/Test Split │
                    │  (Stratified 70/15/15)│
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Ready for Training!  │
                    │  Stage-1 & Stage-2    │
                    └───────────────────────┘
```

## Usage

### Quick Start
```bash
cd preprocessing
./run_pipeline.sh
```

### Step-by-Step
```bash
# 1. Process individual datasets
python scripts/process_cicids2017.py -i ../CIC-IDS2017/ -o outputs/cic.csv
python scripts/process_ustc.py -i ../USTC-TFC2016-master/ -o outputs/ --type all

# 2. Merge all datasets
python scripts/merge_datasets.py -c configs/merge_config.yaml

# 3. Generate statistics
python scripts/dataset_statistics.py -i outputs/Unified_Dataset.csv -o outputs/statistics/
```

## Output Format

### CSV Schema
```csv
flow_id,src_ip,dst_ip,src_port,dst_port,protocol,
packet_count_fwd,packet_count_bwd,byte_count_fwd,byte_count_bwd,
flow_duration,packets_per_second,bytes_per_second,byte_ratio,
packet_length_min,packet_length_max,packet_length_mean,packet_length_std,
mean_iat_fwd,mean_iat_bwd,jitter,periodicity_score,
mss,mtu,ttl,window_size,entropy_score,protocol_hint,
fraud_score,vpn_probability,ip_type,
connection_rate,failed_connections,bot_probability,
app_label,intent_label,vpn_flag
```

### Label Mappings

**Application Labels (Stage-1)**:
- Browsing
- Chat
- VoIP
- Video_Streaming
- File_Transfer
- Email
- P2P
- Gaming
- C2_Communication

**Intent Labels (Stage-2)**:
- Benign
- Botnet
- BruteForce
- DDoS
- DoS
- Portscan
- Infiltration
- Web_Attack
- Credential_Stuffing
- C2_Communication
- Malware

## File Structure

```
preprocessing/
├── README.md                    # Quick start guide
├── run_pipeline.sh             # Master execution script
├── requirements.txt            # Python dependencies
├── configs/
│   └── merge_config.yaml       # Configuration file
├── scripts/
│   ├── feature_extractor.py    # Feature engineering
│   ├── pcap_to_flow.py        # PCAP → Flow converter
│   ├── process_cicids2017.py  # CIC-IDS2017 processor
│   ├── process_ustc.py        # USTC-TFC2016 processor
│   ├── merge_datasets.py      # Dataset merger
│   └── dataset_statistics.py  # Statistics generator
├── outputs/                    # Generated datasets
└── logs/                       # Processing logs
```

## Quality Metrics

After preprocessing, expect:
- ✅ **No duplicate flows** (100% uniqueness)
- ✅ **<1% missing values** in critical features
- ✅ **Balanced classes** (<5:1 ratio after SMOTE)
- ✅ **Consistent labels** across all datasets
- ✅ **Feature correlation** <0.9 (no multicollinearity)

## Validation Checklist

Before training models:
- [ ] All datasets processed successfully
- [ ] Feature extraction complete (65+ features)
- [ ] Labels standardized and mapped correctly
- [ ] No duplicate flows remaining
- [ ] Missing values handled appropriately
- [ ] Train/val/test splits created
- [ ] Statistics report reviewed
- [ ] Label distributions balanced

## Next Steps

1. **Review Statistics**
   - Check `outputs/statistics/summary_report.json`
   - Analyze label distributions
   - Verify feature correlations

2. **Begin Model Training**
   - Stage-1: Application Classification (CNN)
   - Stage-2: Intent Classification (XGBoost/RF)

3. **Iterate**
   - Adjust feature engineering if needed
   - Fine-tune class balancing
   - Add more datasets

## Support

- **Issues**: Check `logs/preprocessing.log`
- **Configuration**: Edit `configs/merge_config.yaml`
- **Documentation**: See `PREPROCESSING_GUIDE.md`

---

**Last Updated**: November 9, 2025
