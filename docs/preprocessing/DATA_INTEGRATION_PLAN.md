# Data Integration and Preprocessing Plan

## Executive Summary

This document outlines the complete strategy for preprocessing and merging three distinct network traffic datasets into a unified CSV format for training the VPN detection and user segregation system. Each dataset has different formats, features, and purposes - this plan addresses how to harmonize them into a cohesive training dataset.

---

## 1. Dataset Overview

### 1.1 MIT LL VNAT Dataset
**Status**: 🔴 **NOT FOUND IN WORKSPACE** (Empty directory)

**Expected Format**: PCAP files with labeled application traffic
**Purpose**: Application classification (Stage 1)
**Expected Labels**: Streaming, Chat, VoIP, File Transfer, Browsing, C2 Communication
**VPN Status**: Contains both VPN and non-VPN traffic
**Expected Features**: Packet-level and flow-level features

**Action Required**: 
- Verify dataset location or download from MIT Lincoln Laboratory
- Expected structure: Separate PCAP files per application type
- Typical size: 20-40 GB

---

### 1.2 CIC-IDS2017 Dataset
**Status**: ✅ **AVAILABLE** (7 Parquet files)

**Format**: Pre-processed Parquet files with flow-level features
**Purpose**: Intent classification (Stage 2) - Attack detection
**Available Files**:
- `Benign-Monday-no-metadata.parquet` - Normal traffic
- `Botnet-Friday-no-metadata.parquet` - Botnet C2 traffic
- `DDoS-Friday-no-metadata.parquet` - DDoS attacks
- `DoS-Wednesday-no-metadata.parquet` - DoS attacks
- `Infiltration-Thursday-no-metadata.parquet` - Infiltration attacks
- `Portscan-Friday-no-metadata.parquet` - Port scanning
- `WebAttacks-Thursday-no-metadata.parquet` - Web attacks

**Features**: ~80 flow-based features including:
- Packet counts (forward/backward)
- Byte counts (forward/backward)
- Flow duration
- Inter-arrival times (IAT)
- Packet length statistics
- Flow rate metrics
- TCP flags
- Subflow features

**VPN Status**: No VPN traffic (direct network captures)
**Label Type**: Multi-class attack classification

---

### 1.3 University Network Data
**Status**: ✅ **AVAILABLE** (PCAP + FortiAnalyzer logs)

**Format**: Mixed (PCAP files + Structured log files)

**PCAP Files** (Network Data - University/):
- 8 PCAP files from different dates in October
- Filename pattern: `{date}thOct{day}.pcapng`
- Additional: `wifidata.pcapng`
- Nmap scan results (text files)

**Log Files** (Root directory):
- `fortianalyzer-traffic-forward-2025_11_03.log`
- `fortianalyzer-traffic-local-2025_11_03.log`

**Log Format**: FortiGate firewall logs with key-value pairs
**Available Fields**:
```
date, time, srcip, dstip, srcport, dstport, proto, 
service, app, appcat, user, group, action, policyid,
sentbyte, rcvdbyte, sentpkt, rcvdpkt, duration,
srccountry, dstcountry, srcintf, dstintf,
srcgeoid, dstgeoid, policyname, vwlname
```

**Purpose**: Real-world test data with context
**VPN Status**: Unknown (requires detection)
**Label Type**: Unlabeled (can use for testing/validation)

---

## 2. Feature Schema Comparison

### 2.1 CIC-IDS2017 Features (Sample)
Based on the available parquet files, the dataset includes:

**Flow Identifiers**:
- Source IP, Destination IP
- Source Port, Destination Port
- Protocol

**Packet Statistics**:
- Total Fwd Packets, Total Backward Packets
- Total Length of Fwd Packets, Total Length of Bwd Packets
- Fwd Packet Length (Min/Max/Mean/Std)
- Bwd Packet Length (Min/Max/Mean/Std)

**Timing Features**:
- Flow Duration
- Flow IAT Mean/Std/Min/Max
- Fwd IAT Mean/Std/Min/Max
- Bwd IAT Mean/Std/Min/Max

**Rate Features**:
- Flow Packets/s
- Flow Bytes/s

**TCP Features**:
- FIN Flag Count, SYN Flag Count, RST Flag Count
- PSH Flag Count, ACK Flag Count, URG Flag Count
- Down/Up Ratio

**Subflow Features**:
- Subflow Fwd Packets, Subflow Bwd Packets
- Subflow Fwd Bytes, Subflow Bwd Bytes

**Active/Idle**:
- Active Mean/Std/Min/Max
- Idle Mean/Std/Min/Max

---

### 2.2 FortiAnalyzer Log Features

**Connection Metadata**:
- `srcip`, `dstip`, `srcport`, `dstport`, `proto`
- `tranip`, `transip`, `tranport`, `transport` (NAT info)

**Traffic Metrics**:
- `sentbyte`, `rcvdbyte` (bidirectional byte counts)
- `sentpkt`, `rcvdpkt` (bidirectional packet counts)
- `duration` (session duration in seconds)

**Application Layer**:
- `service` (e.g., LDAP_UDP, DNS, SMB)
- `app` (detected application)
- `appcat` (application category)

**Security Context**:
- `action` (accept/deny/start)
- `policyid`, `policyname`
- `user`, `group` (authenticated users)
- `authserver` (authentication source)

**Geolocation**:
- `srccountry`, `dstcountry`
- `srccity`, `dstcity`
- `srcgeoid`, `dstgeoid`

**Network Context**:
- `srcintf`, `dstintf` (interfaces)
- `vwlname` (SD-WAN virtual link)
- `shapingpolicyname` (QoS policy)

**Threat Intelligence** (when applicable):
- `crscore` (threat score)
- `craction` (action taken)
- `crlevel` (threat level)
- `threats`, `threattyps`

---

### 2.3 VNAT Dataset Features (Expected)

**When VNAT dataset is available**, it will provide:

**Packet-Level Features**:
- Packet sizes per flow
- Packet directions (bidirectional)
- Packet timing sequences

**Flow-Level Features**:
- Total packets/bytes per flow
- Flow duration
- Average packet size
- Packet inter-arrival times

**Application Labels**:
- Video streaming (e.g., YouTube, Netflix)
- Chat applications (e.g., Skype, WhatsApp)
- VoIP (e.g., Skype calls)
- File transfer (e.g., FTP, SFTP)
- Web browsing
- C2 communication (Command & Control)

**VPN Labels**:
- Binary flag indicating VPN usage
- Potential VPN protocol indicators

---

## 3. Unified Feature Schema

### 3.1 Core Features (Required for all datasets)

```python
UNIFIED_SCHEMA = {
    # Flow Identifiers (5-tuple)
    'flow_id': 'string',              # Generated: src:port-dst:port-proto
    'src_ip': 'string',
    'dst_ip': 'string',
    'src_port': 'int',
    'dst_port': 'int',
    'protocol': 'int',                # 6=TCP, 17=UDP
    
    # Temporal Information
    'timestamp': 'datetime',
    'flow_duration': 'float',         # seconds
    
    # Packet Statistics (Bidirectional)
    'packet_count_fwd': 'int',
    'packet_count_bwd': 'int',
    'packet_count_total': 'int',
    'byte_count_fwd': 'int',
    'byte_count_bwd': 'int',
    'byte_count_total': 'int',
    
    # Packet Size Statistics
    'packet_length_min': 'float',
    'packet_length_max': 'float',
    'packet_length_mean': 'float',
    'packet_length_std': 'float',
    'packet_length_variance': 'float',
    
    # Timing Statistics (Inter-Arrival Time)
    'mean_iat_fwd': 'float',
    'mean_iat_bwd': 'float',
    'mean_iat_total': 'float',
    'std_iat_fwd': 'float',
    'std_iat_bwd': 'float',
    'std_iat_total': 'float',
    'min_iat_total': 'float',
    'max_iat_total': 'float',
    
    # Rate Features
    'packets_per_second': 'float',
    'bytes_per_second': 'float',
    
    # Ratio Features
    'byte_ratio': 'float',            # fwd/bwd ratio
    'packet_ratio': 'float',          # fwd/bwd ratio
    'down_up_ratio': 'float',
    
    # TCP Features (when applicable)
    'syn_flag_count': 'int',
    'ack_flag_count': 'int',
    'fin_flag_count': 'int',
    'rst_flag_count': 'int',
    'psh_flag_count': 'int',
    
    # Active/Idle Time
    'active_mean': 'float',
    'active_std': 'float',
    'idle_mean': 'float',
    'idle_std': 'float',
    
    # Labels (Target Variables)
    'app_label': 'string',            # Application type (Stage 1)
    'intent_label': 'string',         # Benign/Attack type (Stage 2)
    'vpn_flag': 'int',                # 0=No VPN, 1=VPN, -1=Unknown
    
    # Metadata
    'dataset_source': 'string',       # VNAT/CIC-IDS2017/University
    'source_file': 'string',          # Original filename
}
```

---

### 3.2 Extended Features (Dataset-Specific)

**From FortiAnalyzer Logs**:
```python
FORTIANALYZER_FEATURES = {
    'service': 'string',              # Detected service
    'app': 'string',                  # Application name
    'user': 'string',                 # Authenticated user
    'group': 'string',                # User group
    'action': 'string',               # accept/deny/start
    'src_country': 'string',
    'dst_country': 'string',
    'src_city': 'string',
    'dst_city': 'string',
    'policy_name': 'string',
    'threat_score': 'float',          # When available
}
```

**VPN Detection Features** (to be extracted):
```python
VPN_FEATURES = {
    'mtu': 'int',                     # Maximum Transmission Unit
    'mss': 'int',                     # Maximum Segment Size
    'ttl': 'int',                     # Time To Live
    'window_size': 'int',             # TCP window
    'tcp_options_count': 'int',
    'protocol_hint': 'string',        # OpenVPN/WireGuard/IPSec
    'encryption_detected': 'int',     # Binary flag
    'entropy_score': 'float',         # Payload randomness
}
```

---

## 4. Data Preprocessing Pipeline

### 4.1 Phase 1: Individual Dataset Processing

#### Step 1.1: Process CIC-IDS2017 (✅ Ready)

**Script**: `preprocessing/scripts/process_cicids2017.py`

**Process**:
1. Read each parquet file
2. Extract label from filename
3. Map to standardized intent labels
4. Add metadata columns
5. Standardize column names to unified schema
6. Output: `outputs/cic_ids_2017.csv`

**Label Mapping**:
```python
CIC_LABEL_MAPPING = {
    'Benign': 'Benign',
    'Bot': 'Botnet',
    'DDoS': 'DDoS',
    'DoS Hulk': 'DoS',
    'DoS GoldenEye': 'DoS',
    'DoS slowloris': 'DoS',
    'DoS Slowhttptest': 'DoS',
    'FTP-Patator': 'BruteForce',
    'SSH-Patator': 'BruteForce',
    'PortScan': 'Portscan',
    'Infiltration': 'Infiltration',
    'Web Attack – Brute Force': 'Web_Attack',
    'Web Attack – XSS': 'Web_Attack',
    'Web Attack – Sql Injection': 'Web_Attack',
    'Heartbleed': 'Web_Attack'
}
```

**Derived Fields**:
- `app_label` = 'Unknown' (no app info in CIC-IDS2017)
- `vpn_flag` = 0 (no VPN usage)
- `dataset_source` = 'CIC-IDS2017'

**Command**:
```bash
python preprocessing/scripts/process_cicids2017.py \
    --input "../CIC-IDS2017/" \
    --output "outputs/cic_ids_2017.csv"
```

---

#### Step 1.2: Process University PCAP Files

**Script**: `preprocessing/scripts/pcap_to_flow.py`

**Process**:
1. Use NFStream to extract flows from PCAP files
2. Calculate statistical features
3. Extract VPN detection features (MTU, TTL, etc.)
4. Add geolocation context (if available)
5. Output: `outputs/university_pcap_flows.csv`

**Features Extracted**:
- All core flow statistics from NFStream
- TCP/UDP specific features
- Timing and rate calculations
- Protocol fingerprinting

**Command**:
```bash
python preprocessing/scripts/pcap_to_flow.py \
    --input "../Network Data - University/" \
    --output "outputs/university_pcap/" \
    --pattern "*.pcapng"
```

**Expected Output**: Individual CSV per PCAP + combined file

---

#### Step 1.3: Process FortiAnalyzer Logs

**Script**: `preprocessing/scripts/process_fortianalyzer.py` (TO BE CREATED)

**Process**:
1. Parse key-value log format
2. Extract relevant fields
3. Calculate flow statistics from byte/packet counts
4. Derive rate metrics from duration
5. Map application names to standard categories
6. Output: `outputs/university_fortianalyzer.csv`

**Parsing Strategy**:
```python
def parse_fortianalyzer_log(log_line):
    """
    Parse FortiAnalyzer log format:
    key1=value1 key2=value2 key3="value with spaces"
    """
    fields = {}
    # Regex pattern for key=value pairs
    pattern = r'(\w+)=(?:"([^"]*)"|([^\s]+))'
    matches = re.findall(pattern, log_line)
    
    for match in matches:
        key = match[0]
        value = match[1] if match[1] else match[2]
        fields[key] = value
    
    return fields
```

**Field Mapping**:
```python
FORTIANALYZER_MAPPING = {
    'srcip': 'src_ip',
    'dstip': 'dst_ip',
    'srcport': 'src_port',
    'dstport': 'dst_port',
    'proto': 'protocol',
    'sentbyte': 'byte_count_fwd',
    'rcvdbyte': 'byte_count_bwd',
    'sentpkt': 'packet_count_fwd',
    'rcvdpkt': 'packet_count_bwd',
    'duration': 'flow_duration',
    'service': 'service',
    'app': 'app',
    'user': 'user',
    'group': 'group',
    'action': 'action',
}
```

**Derived Features**:
```python
def derive_features(row):
    """Calculate features from log data"""
    row['packet_count_total'] = row['packet_count_fwd'] + row['packet_count_bwd']
    row['byte_count_total'] = row['byte_count_fwd'] + row['byte_count_bwd']
    
    if row['flow_duration'] > 0:
        row['packets_per_second'] = row['packet_count_total'] / row['flow_duration']
        row['bytes_per_second'] = row['byte_count_total'] / row['flow_duration']
    else:
        row['packets_per_second'] = 0
        row['bytes_per_second'] = 0
    
    if row['byte_count_bwd'] > 0:
        row['byte_ratio'] = row['byte_count_fwd'] / row['byte_count_bwd']
    else:
        row['byte_ratio'] = 0
    
    return row
```

**Label Assignment**:
- `intent_label` = 'Unknown' (requires manual labeling or anomaly detection)
- `app_label` = Map from 'app' field (e.g., DNS → 'Browsing', SMB → 'File_Transfer')
- `vpn_flag` = -1 (unknown, to be detected)

**Command**:
```bash
python preprocessing/scripts/process_fortianalyzer.py \
    --input "../fortianalyzer-traffic-*.log" \
    --output "outputs/university_fortianalyzer.csv"
```

---

#### Step 1.4: Process VNAT Dataset (Pending)

**Script**: `preprocessing/scripts/process_vnat.py` (TO BE CREATED)

**Prerequisites**:
1. Locate or download VNAT dataset
2. Verify directory structure
3. Confirm label format

**Expected Process**:
1. Identify PCAP files by application category
2. Extract flows using NFStream
3. Label flows based on directory/filename
4. Extract VPN-specific features
5. Output: `outputs/vnat_processed.csv`

**Expected Labels**:
```python
VNAT_APP_LABELS = {
    'streaming': 'Video_Streaming',
    'chat': 'Chat',
    'voip': 'VoIP',
    'file_transfer': 'File_Transfer',
    'browsing': 'Browsing',
    'c2': 'C2_Communication',
}
```

**Command** (when ready):
```bash
python preprocessing/scripts/process_vnat.py \
    --input "../LL MIT VNAT Dataset/" \
    --output "outputs/vnat_processed.csv"
```

---

### 4.2 Phase 2: Feature Harmonization

After processing individual datasets, each will have different feature sets. We need to harmonize them.

#### Step 2.1: Feature Alignment

**Script**: `preprocessing/scripts/align_features.py`

**Process**:
1. Load all processed CSV files
2. Identify common features
3. Add missing features with defaults
4. Standardize data types
5. Validate ranges

**Missing Feature Handling**:
```python
FEATURE_DEFAULTS = {
    # Statistical features (use 0 or calculated from available data)
    'packet_length_min': 0,
    'packet_length_max': 0,
    'packet_length_mean': 0,
    'packet_length_std': 0,
    'packet_length_variance': 0,
    
    # Timing features (use 0 if not available)
    'mean_iat_fwd': 0,
    'mean_iat_bwd': 0,
    'std_iat_fwd': 0,
    'std_iat_bwd': 0,
    
    # VPN features (use -1 for unknown)
    'mtu': -1,
    'mss': -1,
    'ttl': -1,
    'window_size': -1,
    'encryption_detected': -1,
    
    # Labels (use 'Unknown' if not available)
    'app_label': 'Unknown',
    'intent_label': 'Unknown',
    'vpn_flag': -1,
}
```

**Calculated Features**:
Some features can be derived from others:
```python
def calculate_missing_features(df):
    """Calculate features from available data"""
    
    # Calculate total counts if not present
    if 'packet_count_total' not in df.columns:
        df['packet_count_total'] = df['packet_count_fwd'] + df['packet_count_bwd']
    
    if 'byte_count_total' not in df.columns:
        df['byte_count_total'] = df['byte_count_fwd'] + df['byte_count_bwd']
    
    # Calculate ratios
    if 'byte_ratio' not in df.columns:
        df['byte_ratio'] = df['byte_count_fwd'] / df['byte_count_bwd'].replace(0, 1)
    
    # Calculate rates
    if 'packets_per_second' not in df.columns:
        df['packets_per_second'] = df['packet_count_total'] / df['flow_duration'].replace(0, 1)
    
    if 'bytes_per_second' not in df.columns:
        df['bytes_per_second'] = df['byte_count_total'] / df['flow_duration'].replace(0, 1)
    
    # Calculate mean packet size (if statistics not available)
    if 'packet_length_mean' not in df.columns:
        df['packet_length_mean'] = df['byte_count_total'] / df['packet_count_total'].replace(0, 1)
    
    return df
```

---

#### Step 2.2: Feature Engineering

**Add Derived Features**:
```python
def engineer_additional_features(df):
    """Create additional features for better model performance"""
    
    # Time-based features
    if 'timestamp' in df.columns:
        df['hour_of_day'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Flow asymmetry
    df['flow_asymmetry'] = abs(df['packet_count_fwd'] - df['packet_count_bwd']) / df['packet_count_total']
    
    # Protocol encoding
    df['is_tcp'] = (df['protocol'] == 6).astype(int)
    df['is_udp'] = (df['protocol'] == 17).astype(int)
    
    # Port categories
    df['src_port_category'] = df['src_port'].apply(categorize_port)
    df['dst_port_category'] = df['dst_port'].apply(categorize_port)
    
    # Burst detection
    if 'packet_count_total' in df.columns and 'flow_duration' in df.columns:
        df['burst_score'] = (df['packet_count_total'] / df['flow_duration'].replace(0, 1)) / \
                           (df['packet_count_total'].mean() / df['flow_duration'].mean())
    
    return df

def categorize_port(port):
    """Categorize port numbers"""
    if port < 1024:
        return 'system'
    elif port < 49152:
        return 'registered'
    else:
        return 'dynamic'
```

---

### 4.3 Phase 3: Dataset Merging

**Script**: `preprocessing/scripts/merge_datasets.py` (EXISTING)

**Process**:
1. Load all aligned datasets
2. Concatenate vertically
3. Remove duplicates
4. Handle missing values
5. Remove outliers
6. Balance classes (if needed)
7. Create stage-specific datasets

**Duplicate Detection**:
```python
def detect_duplicates(df):
    """
    Detect duplicate flows across datasets
    Use 5-tuple + timestamp (rounded to nearest second)
    """
    df['flow_signature'] = (
        df['src_ip'].astype(str) + ':' + df['src_port'].astype(str) + '-' +
        df['dst_ip'].astype(str) + ':' + df['dst_port'].astype(str) + '-' +
        df['protocol'].astype(str) + '-' +
        pd.to_datetime(df['timestamp']).dt.floor('1s').astype(str)
    )
    
    duplicates = df[df.duplicated(subset=['flow_signature'], keep=False)]
    
    if len(duplicates) > 0:
        logger.warning(f"Found {len(duplicates)} duplicate flows")
        # Keep first occurrence
        df = df.drop_duplicates(subset=['flow_signature'], keep='first')
    
    df = df.drop(columns=['flow_signature'])
    return df
```

**Missing Value Strategy**:
```python
def handle_missing_values(df, threshold=0.5):
    """
    Handle missing values:
    1. Remove rows with >50% missing values
    2. Fill numeric features with 0 or median
    3. Fill categorical with 'Unknown'
    """
    # Remove rows with too many missing values
    missing_ratio = df.isnull().sum(axis=1) / len(df.columns)
    df = df[missing_ratio <= threshold]
    
    # Numeric features: fill with 0 (or median for some)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if col in ['mtu', 'mss', 'ttl', 'window_size']:
            # Use -1 for unknown infrastructure features
            df[col].fillna(-1, inplace=True)
        elif col in ['vpn_flag', 'encryption_detected']:
            # Use -1 for unknown binary flags
            df[col].fillna(-1, inplace=True)
        else:
            # Use 0 for statistical features
            df[col].fillna(0, inplace=True)
    
    # Categorical features: fill with 'Unknown'
    categorical_cols = df.select_dtypes(include=['object']).columns
    df[categorical_cols] = df[categorical_cols].fillna('Unknown')
    
    return df
```

**Outlier Removal**:
```python
def remove_outliers_iqr(df, columns, factor=3.0):
    """
    Remove outliers using IQR method
    """
    initial_count = len(df)
    
    for col in columns:
        if col not in df.columns:
            continue
        
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR
        
        df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
    
    removed = initial_count - len(df)
    logger.info(f"Removed {removed} outlier rows ({removed/initial_count*100:.2f}%)")
    
    return df
```

---

### 4.4 Phase 4: Dataset Splitting

**Stage-1 Dataset (Application Classification)**:
```python
def create_stage1_dataset(df):
    """
    Create Stage-1 dataset for application classification
    Only include flows with known app_label
    """
    stage1_df = df[df['app_label'] != 'Unknown'].copy()
    
    logger.info(f"Stage-1 Dataset: {len(stage1_df)} flows")
    logger.info(f"Application distribution:\n{stage1_df['app_label'].value_counts()}")
    
    # Check class balance
    class_counts = stage1_df['app_label'].value_counts()
    imbalance_ratio = class_counts.max() / class_counts.min()
    
    if imbalance_ratio > 5:
        logger.warning(f"Class imbalance detected: {imbalance_ratio:.2f}:1")
        logger.info("Consider applying SMOTE or class weights")
    
    return stage1_df
```

**Stage-2 Dataset (Intent Classification)**:
```python
def create_stage2_dataset(df):
    """
    Create Stage-2 dataset for intent classification
    Include all flows, use Unknown as a class if needed
    """
    stage2_df = df.copy()
    
    # Option 1: Remove Unknown labels
    # stage2_df = stage2_df[stage2_df['intent_label'] != 'Unknown']
    
    # Option 2: Keep Unknown as "Unclassified" class
    stage2_df['intent_label'] = stage2_df['intent_label'].replace('Unknown', 'Unclassified')
    
    logger.info(f"Stage-2 Dataset: {len(stage2_df)} flows")
    logger.info(f"Intent distribution:\n{stage2_df['intent_label'].value_counts()}")
    
    return stage2_df
```

**Train/Val/Test Split**:
```python
def split_dataset(df, label_col, train_size=0.70, val_size=0.15, test_size=0.15, stratify=True):
    """
    Split dataset with stratification
    """
    assert train_size + val_size + test_size == 1.0, "Split ratios must sum to 1.0"
    
    # First split: train vs (val + test)
    if stratify:
        train_df, temp_df = train_test_split(
            df, 
            test_size=(val_size + test_size),
            stratify=df[label_col],
            random_state=42
        )
    else:
        train_df, temp_df = train_test_split(
            df, 
            test_size=(val_size + test_size),
            random_state=42
        )
    
    # Second split: val vs test
    val_ratio = val_size / (val_size + test_size)
    
    if stratify:
        val_df, test_df = train_test_split(
            temp_df,
            test_size=(1 - val_ratio),
            stratify=temp_df[label_col],
            random_state=42
        )
    else:
        val_df, test_df = train_test_split(
            temp_df,
            test_size=(1 - val_ratio),
            random_state=42
        )
    
    logger.info(f"Split complete:")
    logger.info(f"  Train: {len(train_df)} ({len(train_df)/len(df)*100:.1f}%)")
    logger.info(f"  Val:   {len(val_df)} ({len(val_df)/len(df)*100:.1f}%)")
    logger.info(f"  Test:  {len(test_df)} ({len(test_df)/len(df)*100:.1f}%)")
    
    return train_df, val_df, test_df
```

---

## 5. Implementation Roadmap

### Phase 1: Individual Dataset Processing (Week 1)

**Priority 1: CIC-IDS2017** ✅
```bash
# Already has script
python preprocessing/scripts/process_cicids2017.py \
    --input "../CIC-IDS2017/" \
    --output "outputs/cic_ids_2017.csv"
```

**Expected Output**: ~2.8M flows with 80+ features

---

**Priority 2: University FortiAnalyzer Logs** 🔴
```bash
# Need to create script
python preprocessing/scripts/process_fortianalyzer.py \
    --input "../fortianalyzer-traffic-*.log" \
    --output "outputs/university_fortianalyzer.csv"
```

**Tasks**:
1. ✅ Understand log format (DONE - key=value pairs)
2. ⬜ Create parsing script
3. ⬜ Map fields to unified schema
4. ⬜ Handle multi-line entries
5. ⬜ Extract all relevant fields
6. ⬜ Derive missing features

**Expected Output**: ~100K-500K flows (depends on log duration)

---

**Priority 3: University PCAP Files** 🔴
```bash
# Use existing script
python preprocessing/scripts/pcap_to_flow.py \
    --input "../Network Data - University/" \
    --output "outputs/university_pcap/" \
    --pattern "*.pcapng"
```

**Tasks**:
1. ⬜ Install pyarrow for CIC-IDS2017 processing
2. ⬜ Verify NFStream installation
3. ⬜ Process each PCAP file
4. ⬜ Extract VPN detection features
5. ⬜ Combine all university PCAPs

**Expected Output**: ~50K-200K flows per PCAP (depends on capture duration)

---

**Priority 4: VNAT Dataset** 🔴 ⚠️ **BLOCKED**
```bash
# Need dataset first
python preprocessing/scripts/process_vnat.py \
    --input "../LL MIT VNAT Dataset/" \
    --output "outputs/vnat_processed.csv"
```

**Blockers**:
1. Dataset not found in workspace
2. Need to locate or download from MIT Lincoln Laboratory
3. Verify access permissions

**Tasks**:
1. ⬜ Locate VNAT dataset
2. ⬜ Verify structure and format
3. ⬜ Create processing script
4. ⬜ Extract flows with app labels
5. ⬜ Extract VPN features

**Expected Output**: ~500K-1M flows with application labels

---

### Phase 2: Feature Harmonization (Week 2)

**Step 1: Feature Alignment**
```bash
python preprocessing/scripts/align_features.py \
    --input "outputs/*.csv" \
    --output "outputs/aligned/" \
    --schema "configs/unified_schema.yaml"
```

**Tasks**:
1. ⬜ Load all processed datasets
2. ⬜ Identify common features
3. ⬜ Add missing features with defaults
4. ⬜ Calculate derived features
5. ⬜ Validate data types and ranges
6. ⬜ Generate alignment report

---

**Step 2: Quality Assurance**
```bash
python preprocessing/scripts/validate_data.py \
    --input "outputs/aligned/" \
    --report "outputs/validation_report.html"
```

**Checks**:
- ✅ No null values in critical features
- ✅ Valid IP addresses
- ✅ Valid port ranges (0-65535)
- ✅ Valid protocol numbers
- ✅ Positive flow durations
- ✅ Consistent timestamp formats
- ✅ Label consistency

---

### Phase 3: Dataset Merging (Week 2-3)

**Step 1: Merge All Datasets**
```bash
python preprocessing/scripts/merge_datasets.py \
    --config "configs/merge_config.yaml" \
    --output "outputs/"
```

**Tasks**:
1. ⬜ Load all aligned datasets
2. ⬜ Concatenate vertically
3. ⬜ Remove duplicates
4. ⬜ Handle missing values
5. ⬜ Remove outliers
6. ⬜ Generate unified dataset

**Output**: `outputs/Unified_Dataset.csv`

---

**Step 2: Create Stage-Specific Datasets**
```bash
# Automatically done by merge_datasets.py
```

**Outputs**:
- `outputs/Stage1_App_Classification.csv` - For application classifier
- `outputs/Stage2_Intent_Classification.csv` - For intent classifier

---

**Step 3: Train/Val/Test Split**
```bash
# Automatically done by merge_datasets.py
```

**Outputs**:
- `outputs/train.csv` (70%)
- `outputs/val.csv` (15%)
- `outputs/test.csv` (15%)

---

### Phase 4: Analysis & Validation (Week 3)

**Step 1: Generate Statistics**
```bash
python preprocessing/scripts/dataset_statistics.py \
    --input "outputs/Unified_Dataset.csv" \
    --output-dir "outputs/statistics/"
```

**Reports**:
- Label distribution plots
- Feature correlation heatmap
- Class balance analysis
- Missing value report
- Outlier analysis
- Summary statistics

---

**Step 2: Feature Importance Analysis**
```bash
python preprocessing/scripts/feature_analysis.py \
    --input "outputs/Unified_Dataset.csv" \
    --output "outputs/feature_importance.csv"
```

**Analyses**:
- Mutual information scores
- Correlation with labels
- Feature variance
- Redundancy detection

---

## 6. Key Challenges & Solutions

### Challenge 1: Missing VNAT Dataset
**Impact**: Cannot create comprehensive Stage-1 training data

**Solutions**:
1. **Short-term**: Use USTC-TFC2016 benign apps as substitute
2. **Medium-term**: Use FortiAnalyzer app labels (DNS, SMB, etc.)
3. **Long-term**: Acquire VNAT or similar dataset (ISCXVPN2016)

**Mitigation**:
```python
# Use FortiAnalyzer app field for application labels
APP_MAPPING = {
    'DNS': 'Browsing',
    'HTTP': 'Browsing',
    'HTTPS': 'Browsing',
    'SMB': 'File_Transfer',
    'FTP': 'File_Transfer',
    'LDAP': 'Enterprise_App',
    'udp/3478': 'VoIP',  # STUN/TURN for VoIP
    # Add more mappings
}
```

---

### Challenge 2: Different Feature Granularity

**Problem**: 
- CIC-IDS2017: 80+ detailed features
- FortiAnalyzer logs: ~20 basic features
- PCAP files: Can extract any feature

**Solution**:
1. Define "core features" that all datasets must have
2. Mark dataset-specific features as optional
3. Use feature imputation for missing values
4. Create feature availability matrix

**Feature Availability Matrix**:
```python
FEATURE_AVAILABILITY = {
    'CIC-IDS2017': {
        'packet_stats': True,
        'timing_stats': True,
        'tcp_flags': True,
        'active_idle': True,
        'vpn_features': False,
        'application': False,
    },
    'FortiAnalyzer': {
        'packet_stats': True (limited),
        'timing_stats': False,
        'tcp_flags': False,
        'active_idle': False,
        'vpn_features': False,
        'application': True,
    },
    'PCAP': {
        'packet_stats': True,
        'timing_stats': True,
        'tcp_flags': True,
        'active_idle': True,
        'vpn_features': True,
        'application': False (requires labeling),
    }
}
```

---

### Challenge 3: Unlabeled University Data

**Problem**: University network data has no ground truth labels

**Solutions**:

**For Application Labels**:
1. Use FortiAnalyzer's application detection
2. Map service names to application categories
3. Use port numbers as hints (80/443 → Browsing)

**For Intent Labels**:
1. Use as **test-only** data
2. Apply trained model for pseudo-labeling
3. Manual labeling of suspicious flows
4. Use anomaly detection for validation

**For VPN Detection**:
1. Extract MTU/MSS from PCAPs
2. Analyze TTL patterns
3. Check for VPN protocol signatures (OpenVPN port 1194, etc.)
4. Cross-reference with known VPN IP ranges

---

### Challenge 4: Class Imbalance

**Problem**: Attack classes are typically <5% of total traffic

**Solutions**:

**1. SMOTE (Synthetic Minority Over-sampling)**:
```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(sampling_strategy='auto', k_neighbors=5, random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
```

**2. Class Weights**:
```python
from sklearn.utils.class_weight import compute_class_weight

class_weights = compute_class_weight(
    'balanced',
    classes=np.unique(y_train),
    y=y_train
)
```

**3. Stratified Sampling**:
```python
# Ensure all classes represented in train/val/test
train_test_split(X, y, stratify=y, random_state=42)
```

**4. Ensemble Methods**:
- Train separate models for rare classes
- Use balanced random forests

---

### Challenge 5: Feature Scaling

**Problem**: Features have vastly different scales (packet counts vs. IAT)

**Solutions**:

**1. Standard Scaling** (for most features):
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

**2. MinMax Scaling** (for bounded features):
```python
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)
```

**3. Robust Scaling** (for features with outliers):
```python
from sklearn.preprocessing import RobustScaler

scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)
```

**Apply After Splitting**:
```python
# Fit on training data only
scaler.fit(X_train)

# Transform all splits
X_train_scaled = scaler.transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Save scaler for inference
import joblib
joblib.dump(scaler, 'models/feature_scaler.pkl')
```

---

## 7. Expected Outputs

### 7.1 File Structure
```
preprocessing/outputs/
├── Unified_Dataset.csv                    # Complete merged dataset
├── Stage1_App_Classification.csv          # Application classification data
├── Stage2_Intent_Classification.csv       # Intent classification data
├── train.csv                              # Training set (70%)
├── val.csv                                # Validation set (15%)
├── test.csv                               # Test set (15%)
├── feature_importance.csv                 # Feature analysis
├── label_mapping.json                     # Label encoding
├── preprocessing_report.html              # Complete report
├── cic_ids_2017.csv                      # Processed CIC-IDS2017
├── university_fortianalyzer.csv          # Processed logs
├── university_pcap_flows.csv             # Processed PCAPs
├── vnat_processed.csv                    # Processed VNAT (when available)
└── statistics/
    ├── label_distributions.png
    ├── feature_correlations.png
    ├── class_balance.png
    ├── missing_values_report.csv
    └── summary_statistics.json
```

---

### 7.2 Dataset Statistics (Estimated)

**Unified Dataset**:
- **Total Flows**: 3-5 million (depending on VNAT availability)
- **Features**: 65-80 features
- **Labels**: 
  - 8-10 application classes
  - 10-12 intent classes
- **VPN Ratio**: 20-40% (if VNAT included)

**Stage-1 Dataset** (Application Classification):
- **Flows**: 500K-1.5M (only labeled apps)
- **Classes**: 8-10
- **Class Balance**: Varies by dataset (aim for <5:1 ratio)

**Stage-2 Dataset** (Intent Classification):
- **Flows**: 3-5M (all flows)
- **Classes**: 10-12
- **Benign/Attack Ratio**: ~90:10 (before balancing)

---

### 7.3 Quality Metrics

**Target Quality Metrics**:
- ✅ Missing values: <1%
- ✅ Duplicate flows: 0
- ✅ Invalid values: 0
- ✅ Feature correlation: <0.9 (avoid multicollinearity)
- ✅ Class imbalance: <5:1 (after SMOTE)
- ✅ Label consistency: 100%

---

## 8. Next Steps & Dependencies

### Immediate Actions (This Week)

1. **Install Required Dependencies**:
```bash
cd preprocessing
pip install -r requirements.txt

# Install pyarrow for parquet support
pip install pyarrow

# Verify NFStream
python -c "import nfstream; print('NFStream OK')"
```

2. **Process CIC-IDS2017**:
```bash
python scripts/process_cicids2017.py \
    --input "../CIC-IDS2017/" \
    --output "outputs/cic_ids_2017.csv"
```

3. **Create FortiAnalyzer Parser**:
- Create `scripts/process_fortianalyzer.py`
- Test on sample log lines
- Process full log files

4. **Process University PCAPs**:
```bash
python scripts/pcap_to_flow.py \
    --input "../Network Data - University/" \
    --output "outputs/university_pcap/" \
    --pattern "*.pcapng"
```

5. **Locate VNAT Dataset**:
- Check MIT Lincoln Laboratory website
- Check local backups
- Consider alternatives (ISCXVPN2016)

---

### Week 2 Actions

1. **Create Feature Alignment Script**
2. **Run Data Validation**
3. **Merge All Datasets**
4. **Generate Statistics**
5. **Create Stage-Specific Datasets**

---

### Week 3 Actions

1. **Feature Analysis**
2. **Class Balancing (SMOTE)**
3. **Final Validation**
4. **Documentation**
5. **Prepare for Model Training**

---

## 9. Risk Mitigation

### Risk 1: VNAT Dataset Unavailable
**Mitigation**: Use USTC benign apps + FortiAnalyzer labels
**Impact**: Lower Stage-1 accuracy, but still functional

### Risk 2: Memory Issues with Large Datasets
**Mitigation**: Use Dask for out-of-core processing
**Impact**: Slower processing, but scalable

### Risk 3: Feature Extraction Failures
**Mitigation**: Robust error handling, continue on failure
**Impact**: Some flows may be dropped, but pipeline continues

### Risk 4: Label Inconsistencies
**Mitigation**: Manual review of edge cases, clear mapping rules
**Impact**: May need re-labeling some flows

---

## 10. Success Criteria

### ✅ Pipeline Complete When:
1. All available datasets processed
2. Unified dataset created with 65+ features
3. Stage-1 and Stage-2 datasets prepared
4. Train/val/test splits created with stratification
5. Quality metrics met (>99% complete data)
6. Documentation and statistics generated
7. Data ready for model training

### ✅ Deliverables:
1. Unified_Dataset.csv
2. Stage-specific datasets (2)
3. Train/val/test splits (3)
4. Feature importance analysis
5. Preprocessing report
6. Label mapping JSON
7. This implementation guide

---

## Appendix A: Command Summary

```bash
# Step 1: Install dependencies
cd preprocessing
pip install -r requirements.txt
pip install pyarrow

# Step 2: Process CIC-IDS2017
python scripts/process_cicids2017.py -i ../CIC-IDS2017/ -o outputs/cic_ids_2017.csv

# Step 3: Process FortiAnalyzer logs (TO BE CREATED)
python scripts/process_fortianalyzer.py -i ../fortianalyzer-traffic-*.log -o outputs/university_fortianalyzer.csv

# Step 4: Process University PCAPs
python scripts/pcap_to_flow.py -i "../Network Data - University/" -o outputs/university_pcap/ --pattern "*.pcapng"

# Step 5: Process VNAT (when available)
python scripts/process_vnat.py -i "../LL MIT VNAT Dataset/" -o outputs/vnat_processed.csv

# Step 6: Merge all datasets
python scripts/merge_datasets.py -c configs/merge_config.yaml

# Step 7: Generate statistics
python scripts/dataset_statistics.py -i outputs/Unified_Dataset.csv -o outputs/statistics/
```

---

## Appendix B: Feature Reference

See: `docs/preprocessing/FEATURE_REFERENCE.md`

---

## Appendix C: Label Mappings

### Application Labels (Stage 1)
```python
APPLICATION_LABELS = [
    'Browsing',           # HTTP/HTTPS web browsing
    'Chat',               # Instant messaging (WhatsApp, Telegram, etc.)
    'VoIP',               # Voice over IP (Skype, Zoom audio)
    'Video_Streaming',    # YouTube, Netflix, etc.
    'File_Transfer',      # FTP, SFTP, SMB, etc.
    'Email',              # SMTP, IMAP, POP3
    'P2P',                # BitTorrent, eMule, etc.
    'Gaming',             # Online games
    'C2_Communication',   # Command & Control (malicious)
    'Unknown',            # Unclassified
]
```

### Intent Labels (Stage 2)
```python
INTENT_LABELS = [
    'Benign',             # Normal, legitimate traffic
    'Botnet',             # Botnet C2 communication
    'BruteForce',         # Password brute force attacks
    'DDoS',               # Distributed Denial of Service
    'DoS',                # Denial of Service
    'Portscan',           # Port scanning
    'Infiltration',       # Network infiltration attempts
    'Web_Attack',         # XSS, SQL injection, etc.
    'Credential_Stuffing',# Automated credential testing
    'Malware',            # Malware communication
    'Unknown',            # Unclassified
]
```

---

**Document Version**: 1.0  
**Last Updated**: November 10, 2025  
**Author**: Data Engineering Team  
**Status**: 🔴 In Progress - Pending VNAT dataset and FortiAnalyzer parser
