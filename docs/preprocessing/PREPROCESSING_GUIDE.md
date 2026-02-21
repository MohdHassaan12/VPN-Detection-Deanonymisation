# Dataset Preprocessing Guide

## Overview
This guide covers the preprocessing pipeline for unifying multiple datasets (VNAT, ISCXVPN2016, CIC-IDS2017, USTC-TFC2016, UNSW, and custom university PCAPs) into a standardized CSV format for two-stage ML pipeline training.

## Objectives

### Two-Stage ML Pipeline
1. **Stage-1**: Application Classification (Browsing, Chat, VoIP, Video, C2, File Transfer)
2. **Stage-2**: Intent Classification (Benign vs. Malicious)

### Output
- Unified CSV dataset with rich features for high-accuracy model training
- Separate datasets for each stage with consistent feature engineering

---

## 1. Data Source Integration

| Dataset | Purpose | Type | Key Features |
|---------|---------|------|--------------|
| **VNAT (MIT)** | App-based classification | Labeled PCAPs | Flow-based and packet-level features for streaming, chat, VoIP, C2, file transfer |
| **ISCXVPN2016** | App-type within VPN/non-VPN | Labeled PCAPs | Flow duration, inter-arrival time, packet size statistics |
| **CIC-IDS2017** | Attack-level intent detection | Labeled PCAPs | Statistical, temporal, behavioral features for various attacks |
| **USTC-TFC2016** | Malware vs. Benign traffic | Labeled PCAPs | Application and malware traffic patterns |
| **UNSW-NB15** | Network intrusion detection | Labeled PCAPs | Modern attack types and normal activities |
| **University PCAPs + Logs** | Real-world test data | PCAP + Syslog | Custom traffic with metadata (IP, timestamps, event tags) |

---

## 2. Preprocessing Pipeline

### Step 1: Extract Flows from PCAPs
**Tool**: NFStream (recommended) or PyShark/Scapy

**Process**:
- Convert raw PCAP files into flow-level representations
- Extract bidirectional flow statistics
- Include timing and packet size distributions

**Output Features**:
```
flow_id, src_ip, dst_ip, src_port, dst_port, protocol,
packets_forward, packets_backward, bytes_forward, bytes_backward,
duration, mean_packet_size, std_packet_size,
mean_iat, std_iat, min_iat, max_iat
```

### Step 2: Add VPN-Specific Features
**Purpose**: Detect VPN usage and protocol fingerprints

**Features to Extract**:
- **MTU/MSS values**: From TCP SYN packets
- **TTL (Time-To-Live)**: IP header field
- **Window Size**: TCP window scaling
- **Protocol fingerprints**: OpenVPN, WireGuard, IPSec signatures
- **Certificate characteristics**: TLS handshake patterns
- **Entropy measures**: Encrypted traffic randomness

### Step 3: Derive Statistical & Temporal Features
**Categories**:

#### Packet Size Statistics
- Min, max, mean, standard deviation
- Variance, coefficient of variation
- Quartiles (Q1, Q2, Q3)

#### Flow Duration
- Total duration
- Active time vs. idle time
- Session persistence

#### Inter-Arrival Times (IAT)
- Mean, std, min, max IAT
- IAT variance and distribution
- Forward vs. backward IAT patterns

#### Byte Ratios
- Upload/download ratio
- Asymmetry index
- Payload size distribution

#### Periodicity Metrics
- Regularity of packet timing
- Burst patterns
- Jitter measurements

### Step 4: Integrate Behavioral Features
**From Log Data**:
- Login attempts and failure rates
- Session duration patterns
- Request frequency and velocity
- Connection establishment patterns

**From IP Intelligence**:
- IP type (Residential, Datacenter, Mobile, VPN provider)
- ASN reputation scoring
- Geolocation consistency
- Proxy/VPN likelihood scores

### Step 5: Normalize Labels

#### (A) Application Classification Dataset
**Sources**: VNAT + ISCXVPN2016 + USTC (Benign)

**Labels**:
```python
app_labels = [
    'Browsing',
    'Chat',
    'VoIP', 
    'Video_Streaming',
    'File_Transfer',
    'Email',
    'P2P',
    'Gaming',
    'C2_Communication'
]
```

**Additional Column**:
- `vpn_flag`: Binary (1 if VPN, 0 if non-VPN)

#### (B) Intent Classification Dataset
**Sources**: CIC-IDS2017 + USTC (Malware) + UNSW + Custom traffic

**Labels**:
```python
intent_labels = [
    'Benign',
    'Botnet',
    'BruteForce',
    'DDoS',
    'DoS',
    'Portscan',
    'Infiltration',
    'Web_Attack',
    'Credential_Stuffing',
    'C2_Communication',
    'Malware'
]
```

---

## 3. Data Cleaning & Fusion

### Duplicate Removal
- Remove duplicate flows across datasets
- Use flow 5-tuple + timestamp hashing

### Label Consistency
- Standardize label names across datasets
- Resolve overlapping classes
- Map similar categories to unified labels

### Class Balancing
- Analyze class distribution
- Apply SMOTE (Synthetic Minority Oversampling) for minority classes
- Consider undersampling for extreme majority classes

### Missing Value Handling
- Fill numerical features with 0 or median
- Create indicator columns for missing values
- Remove flows with >50% missing features

### Outlier Detection
- Use IQR method for statistical outliers
- Domain knowledge for valid ranges
- Z-score normalization for extreme values

---

## 4. Dataset Partitioning

| Purpose | Split | Usage |
|---------|-------|-------|
| **Training** | 70% | Train Stage-1 & Stage-2 models |
| **Validation** | 15% | Hyperparameter tuning, early stopping |
| **Testing** | 15% | Final evaluation (include university data) |

**Stratified Split**: Maintain class distribution across all splits

---

## 5. Feature Categories Summary

### IP Reputation Features (8 features)
```
ip_type, fraud_score, asn, asn_reputation,
vpn_probability, proxy_score, geolocation_risk, datacenter_flag
```

### Connection Fingerprint Features (10 features)
```
mss, mtu, ttl, window_size, tcp_options_count,
protocol_hint, encryption_detected, tls_version, cipher_suite, certificate_validity
```

### Flow Statistics Features (20 features)
```
packet_count_fwd, packet_count_bwd, byte_count_fwd, byte_count_bwd,
packet_length_min, packet_length_max, packet_length_mean, packet_length_std,
packet_length_variance, byte_ratio, flow_duration, active_mean, active_std,
idle_mean, idle_std, packets_per_second, bytes_per_second,
down_up_ratio, fwd_bulk_rate, bwd_bulk_rate
```

### Timing Features (15 features)
```
mean_iat_fwd, mean_iat_bwd, std_iat_fwd, std_iat_bwd,
min_iat_fwd, max_iat_fwd, iat_total, flow_iat_mean, flow_iat_std,
rtt_mean, rtt_std, jitter, periodicity_score, burst_rate, inter_burst_time
```

### Behavioral Features (12 features)
```
login_failure_rate, account_velocity, session_duration,
request_frequency, connection_establishment_rate, failed_connections,
syn_ack_delay, human_score, bot_probability, anomaly_score,
reputation_change, time_of_day_score
```

### Derived Labels
```
app_label (Stage-1 output), intent_label (Stage-2 target), vpn_flag
```

**Total**: ~65 features + labels

---

## 6. Tools & Libraries

### Core Processing
- **NFStream**: Fast flow extraction from PCAPs
- **PyShark**: Detailed packet inspection
- **Scapy**: Custom packet manipulation
- **dpkt**: Fast packet parsing

### Data Manipulation
- **Pandas**: DataFrame operations
- **Dask**: Large dataset processing
- **NumPy**: Numerical computations
- **Polars**: Ultra-fast DataFrame operations

### Machine Learning
- **Scikit-learn**: Preprocessing, feature selection, baseline models
- **XGBoost**: Gradient boosting for intent classification
- **TensorFlow/Keras**: CNN for application classification
- **Imbalanced-learn**: SMOTE and class balancing

### Visualization
- **Matplotlib**: Basic plotting
- **Seaborn**: Statistical visualizations
- **Plotly**: Interactive dashboards

### Storage & Management
- **CSV**: Training data export
- **Parquet**: Efficient columnar storage
- **MongoDB**: Flow log database
- **SQLite**: Lightweight metadata storage

---

## 7. Output Schema

### Unified_Dataset.csv Structure
```csv
# Connection Identifiers
flow_id, src_ip, dst_ip, src_port, dst_port, protocol, timestamp

# Connection Fingerprint
mss, mtu, ttl, window_size, tcp_options, protocol_hint

# Flow Statistics
packet_count, byte_count, duration, packet_length_mean, packet_length_std,
byte_ratio, packets_per_second, bytes_per_second

# Timing Features
mean_iat, std_iat, min_iat, max_iat, flow_periodicity, jitter, rtt

# IP Intelligence
fraud_score, ip_type, asn, vpn_probability, proxy_score

# Behavioral Features
login_failure_rate, account_velocity, human_score, bot_probability

# Labels
app_label, intent_label, vpn_flag
```

---

## 8. Quality Assurance

### Validation Checks
- ✅ No missing values in critical features
- ✅ All numerical features in valid ranges
- ✅ Label distribution documented
- ✅ No duplicate flows
- ✅ Consistent feature scaling
- ✅ Temporal ordering preserved for time-series analysis

### Documentation Requirements
- Feature description and importance
- Label mapping dictionary
- Dataset statistics and distributions
- Preprocessing parameters used
- Version control for datasets

---

## 9. Usage Examples

### Processing a Single Dataset
```bash
python preprocessing/scripts/process_vnat.py \
    --input_dir "LL MIT VNAT Dataset/" \
    --output_csv "preprocessing/outputs/vnat_processed.csv" \
    --log_file "preprocessing/logs/vnat.log"
```

### Merging All Datasets
```bash
python preprocessing/scripts/merge_datasets.py \
    --config preprocessing/configs/merge_config.yaml \
    --output preprocessing/outputs/Unified_Dataset.csv
```

### Generating Statistics
```bash
python preprocessing/scripts/dataset_statistics.py \
    --input preprocessing/outputs/Unified_Dataset.csv \
    --output_dir preprocessing/outputs/statistics/
```

---

## 10. Expected Results

### Final Outputs
1. **Unified_Dataset.csv**: Complete merged dataset (~1M+ flows)
2. **Stage1_App_Classification.csv**: Application classification training data
3. **Stage2_Intent_Classification.csv**: Intent classification training data
4. **train.csv, val.csv, test.csv**: Stratified splits
5. **feature_importance.csv**: Feature statistics and correlations
6. **label_mapping.json**: Label encoding dictionary
7. **preprocessing_report.html**: Complete preprocessing statistics

### Quality Metrics
- Class balance ratio: <5:1 after SMOTE
- Missing values: <1%
- Feature correlation: <0.9 (no multicollinearity)
- Duplicate flows: 0
- Label consistency: 100%

---

## Next Steps
1. Run individual dataset processors
2. Validate feature extraction quality
3. Merge datasets with conflict resolution
4. Perform EDA (Exploratory Data Analysis)
5. Split and export final training datasets
6. Begin model training pipeline

## References
- NFStream Documentation: https://www.nfstream.org/
- ISCXVPN2016 Dataset: https://www.unb.ca/cic/datasets/vpn.html
- CIC-IDS2017 Dataset: https://www.unb.ca/cic/datasets/ids-2017.html
- USTC-TFC2016: https://github.com/yungshenglu/USTC-TFC2016

---

**Last Updated**: November 9, 2025
