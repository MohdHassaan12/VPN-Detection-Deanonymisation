# VPN Detection & Deanonymisation - Complete Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Four-Layer Architecture](#four-layer-architecture)
3. [Data Pipeline](#data-pipeline)
4. [ML Models](#ml-models)
5. [Deployment Guide](#deployment-guide)
6. [Performance Targets](#performance-targets)
7. [Security & Ethics](#security--ethics)

---

## System Overview

**One-line summary**: A multi-layer, low-latency pipeline that (1) quickly filters obvious VPN/hosting traffic at the edge, (2) decrypts/inspects at the gateway when available, (3) classifies application type with a CNN (Packet-Block images) and then (4) scores intent (RandomForest / XGBoost) to apply a risk-based policy (Allow / Challenge / Block).

### Key Features
- **Two-stage ML pipeline**: App classification → Intent scoring
- **Adaptive policy engine**: Risk-based responses (ALLOW/CHALLENGE/BLOCK)
- **Low latency**: <200ms end-to-end (P99)
- **Privacy-respecting**: VPN usage alone is not blocking criteria
- **Scalable**: Kubernetes-native with HPA

---

## Four-Layer Architecture

### Layer 1: Edge Firewall (Fast Filter)
**Latency**: <10ms  
**Purpose**: Eliminate obvious threats before expensive ML processing

**Capabilities**:
- IP Intelligence Check (IPQualityScore/IPinfo API)
- MTU/MSS Fingerprinting (Passive TCP Analysis)
- Fast rule-based filtering

**Decision Logic**:
```python
if ip_fraud_score > 90:
    return BLOCK
elif ip_type == "datacenter" and known_bad_asn:
    return BLOCK
elif mtu_value < 1350:
    flag_as_vpn = True
    pass_to_ml_engine()
```

**Implementation**: NGINX + Lua or small Python microservice

---

### Layer 2: TLS Termination / Load Balancer
**Purpose**: Decrypt traffic for deep analysis

**Why This Architecture?**
- Traffic must be decrypted anyway for application
- Avoids complex encrypted traffic analysis
- Defeats TLS 1.3 and ECH obfuscation
- Lower computational cost

**Extracted Data**:
- Decrypted HTTP headers
- TLS fingerprints (before decryption)
- Application-layer payloads
- Connection metadata

**Implementation**: NGINX Plus, HAProxy, or AWS ALB

---

### Layer 3: ML Risk Scoring Engine (Two-Stage Pipeline)

#### Stage 1: Application Classifier
**Model**: CNN (Convolutional Neural Network)  
**Latency**: ~50ms  
**Input**: Packet-Block images (64×64×3 RGB) or flow statistics

**Encoding Scheme** (Packet-Block Images):
- **R channel**: Client→Server packet size (normalized 0-255)
- **G channel**: Server→Client packet size (normalized 0-255)  
- **B channel**: Inter-arrival time (normalized 0-255)
- Each packet → one pixel (sequential mapping)

**Output Classes** (8 categories):
1. BROWSING
2. CHAT
3. VOIP
4. VIDEO
5. FILE_TRANSFER
6. P2P
7. C2_CNC (Command & Control)
8. UNKNOWN

**Training Data**:
- VNAT (MIT Lincoln Lab) - 36GB, 5 app types + C2
- ISCXVPN2016 - 28GB, 7 app types
- USTC-TFC2016 - Benign + Malware applications

**Architecture** (Example CNN):
```
Input (64×64×3)
  ↓
Conv2D (32 filters, 3×3) + ReLU + MaxPool
  ↓
Conv2D (64 filters, 3×3) + ReLU + MaxPool
  ↓
Conv2D (128 filters, 3×3) + ReLU + MaxPool
  ↓
Flatten → Dense(256) + Dropout(0.5)
  ↓
Output Dense(8) + Softmax
```

---

#### Stage 2: Intent Classifier (Risk Scoring)
**Model**: XGBoost or Random Forest  
**Latency**: ~50ms  
**Input**: 25-feature vector

**Feature Vector Composition**:
```
[0-3]   IP Intelligence (is_vpn, is_proxy, is_datacenter, fraud_score)
[4-10]  Flow Statistics (duration, packets, bytes, IAT)
[11-13] Behavioral (human_score, login_failure_rate, account_velocity)
[14]    MTU Indicator (VPN detection)
[15-22] App Class (one-hot from Stage-1)
[23-24] App Confidence + Graph Anomaly Score
```

**Output**: Risk score 0-99

**Calibration**:
- Probability → Risk Score: `risk_score = int(probability * 99)`
- Threshold tuning based on business cost matrix

**Training Data**:
- CIC-IDS-2017 (Botnet, DDoS, DoS, Infiltration, Web Attacks)
- UNSW-NB15 (Diverse attack patterns)
- USTC-TFC2016 (Malware flows)
- Labeled VPN + non-VPN flows with attack labels

---

### Layer 4: Policy Engine
**Purpose**: Convert risk score to business action

**Policy Configuration**:
```yaml
Low Risk (0-20):
  action: ALLOW
  logging: minimal
  cache_ttl: 3600s

Medium Risk (21-60):
  action: CHALLENGE
  methods: [MFA, CAPTCHA, Email_Verification]
  logging: detailed
  cache_ttl: 300s

High Risk (61-99):
  action: BLOCK
  rate_limit: true
  alert: security_team
  logging: full
  cache_ttl: 60s
```

**Response Format**:
```json
{
  "request_id": "req_1699564321000",
  "risk_score": 45,
  "app_class": "BROWSING",
  "intent_class": "BENIGN",
  "action": "CHALLENGE",
  "reason": "Medium risk - additional verification required",
  "latency_ms": 87.3
}
```

---

## Data Pipeline

### Step 1: PCAP Collection
**Sources**:
- Live traffic capture (tcpdump, Wireshark)
- Network TAPs or SPAN ports
- VPN tunnel endpoints
- Existing datasets (VNAT, ISCXVPN2016, USTC, CIC-IDS)

### Step 2: Flow Extraction
**Tool**: NFStream or custom Scapy parser

**Configuration**:
```yaml
idle_timeout: 120s      # Flow idle timeout
active_timeout: 1800s   # Flow active timeout
min_packets: 3          # Minimum packets per flow
```

**Output**: CSV with ~65 flow features per flow

### Step 3: Packet-Block Image Generation
**Script**: `preprocessing/scripts/pcap_to_packetblock.py`

**Usage**:
```bash
python pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/Benign/ \
  --out-dir ./outputs/packetblock_images/ \
  --img-size 64 \
  --flow-timeout 60.0
```

**Output**:
- PNG images: `flow_<pcap>_<id>.png`
- Manifest CSV: Flow metadata + labels

### Step 4: Feature Engineering
**Flow Statistics** (auto-extracted):
- Packet counts (fwd/bwd)
- Byte counts (fwd/bwd)
- Packet sizes (min/mean/max/std)
- Inter-arrival times (IAT)
- Flow duration

**IP Intelligence** (API enrichment):
- is_vpn, is_proxy, is_tor
- ip_type (datacenter/residential)
- fraud_score (0-100)
- ASN, geolocation

**Behavioral Features** (session tracking):
- human_score (mouse/keyboard/JS biometrics)
- login_failure_rate (5min window)
- account_velocity (accounts attempted)
- device_fingerprint_mismatch

### Step 5: Label Mapping
**Datasets → Unified Labels**:
```python
# Application labels (Stage-1)
VNAT: {"chat", "voip", "streaming"} → {"CHAT", "VOIP", "VIDEO"}
ISCX: {"browsing", "email", "P2P"} → {"BROWSING", "CHAT", "P2P"}
USTC: {"BitTorrent", "FTP"} → {"P2P", "FILE_TRANSFER"}

# Intent labels (Stage-2)
CIC-IDS: {"BENIGN", "Bot", "DDoS", "DoS"} → {0, 1, 1, 1}
USTC: {"Benign/*", "Malware/*"} → {0, 1}
```

---

## ML Models

### Training Stage-1 (App Classifier)

**Dataset Preparation**:
```bash
# Generate Packet-Block images
cd preprocessing
python scripts/pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/ \
  --out-dir ./outputs/stage1_images/ \
  --img-size 64

# Split train/val/test (70/15/15)
python scripts/split_dataset.py \
  --input ./outputs/stage1_images/manifest.csv \
  --output ./outputs/stage1_splits/
```

**Model Training**:
```python
# model_training/stage1_app_classifier/train_cnn.py
import tensorflow as tf
from tensorflow.keras import layers, models

# Build CNN
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(64, 64, 3)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(8, activation='softmax')  # 8 app classes
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# Train
model.fit(train_ds, validation_data=val_ds, epochs=50)

# Save
model.save('./models/stage1/saved_model')
```

**Evaluation Metrics**:
- Per-class Precision/Recall/F1
- Confusion Matrix
- ROC-AUC (one-vs-rest)

---

### Training Stage-2 (Intent Classifier)

**Dataset Preparation**:
```bash
# Merge datasets with labels
python scripts/merge_datasets.py \
  --config configs/merge_config.yaml \
  --output ./outputs/Stage2_Intent_Classification.csv

# Feature engineering
python scripts/feature_extractor.py \
  --input ./outputs/Stage2_Intent_Classification.csv \
  --output ./outputs/stage2_features.csv
```

**Model Training**:
```python
# model_training/stage2_intent_classifier/train_xgboost.py
import xgboost as xgb
from sklearn.model_selection import train_test_split

# Load features
X = df[feature_columns]  # 25 features
y = df['is_malicious']   # 0=benign, 1=malicious

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15)

# Train XGBoost
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

params = {
    'objective': 'binary:logistic',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 200,
    'eval_metric': 'auc'
}

model = xgb.train(params, dtrain, num_boost_round=200,
                  evals=[(dtest, 'test')], early_stopping_rounds=20)

# Save
model.save_model('./models/stage2/model.xgb')
```

**Evaluation**:
- ROC-AUC, Precision-Recall curve
- False Positive Rate at fixed TPR (e.g., FPR@95%TPR)
- Confusion Matrix at different thresholds

---

## Deployment Guide

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Docker registry access
- GPU nodes (optional, for CNN acceleration)

### Step 1: Build Container Image
```bash
cd deployment/docker

# Build inference API image
docker build -t yourrepo/vpn-inference-api:v1.0 -f Dockerfile.inference-api ../../inference/

# Push to registry
docker push yourrepo/vpn-inference-api:v1.0
```

### Step 2: Upload Models to MinIO
```bash
# Port-forward MinIO (after deploying namespace + minio)
kubectl port-forward -n vpn-inference svc/minio 9000:9000

# Upload models
mc alias set minio http://localhost:9000 minioaccesskey miniosecretkey
mc mb minio/models
mc cp --recursive ./models/stage1 minio/models/stage1/
mc cp --recursive ./models/stage2 minio/models/stage2/
```

### Step 3: Deploy to Kubernetes
```bash
cd deployment/k8s

# Apply manifests in order
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-config.yaml
kubectl apply -f 03-minio.yaml
kubectl apply -f 04-redis.yaml

# Wait for storage services
kubectl wait --for=condition=ready pod -l app=minio -n vpn-inference --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n vpn-inference --timeout=120s

# Deploy inference stack
kubectl apply -f 05-tf-serving.yaml
kubectl apply -f 06-inference-api.yaml
kubectl apply -f 07-ingress.yaml

# Check status
kubectl get pods -n vpn-inference
```

### Step 4: Verify Deployment
```bash
# Port-forward inference API
kubectl port-forward -n vpn-inference svc/inference-api 8080:8080

# Health check
curl http://localhost:8080/health

# Test prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "192.168.1.100",
    "dst_ip": "8.8.8.8",
    "src_port": 51234,
    "dst_port": 443,
    "protocol": "TCP",
    "is_vpn": true,
    "fraud_score": 35,
    "flow_duration": 120.5,
    "total_fwd_packets": 150,
    "human_score": 0.85
  }'
```

---

## Performance Targets

### Latency
- **Edge Filter**: <10ms (P99)
- **Stage-1 CNN**: ~50ms
- **Stage-2 XGBoost**: ~50ms
- **End-to-end**: <200ms (P99)

### Throughput
- **Target**: 10,000 requests/second
- **Strategy**: Horizontal autoscaling (HPA)
- **Caching**: Redis for low-risk IPs (TTL: 1hr)

### Accuracy
- **Stage-1**: >90% per-class F1-score
- **Stage-2**: AUC >0.95, FPR@95%TPR <2%

### Resource Requirements
- **Inference API pod**: 250m CPU, 512Mi RAM (request)
- **TF Serving pod**: 500m CPU, 1Gi RAM (request)
- **Redis**: 100m CPU, 128Mi RAM
- **MinIO**: 100m CPU, 256Mi RAM

---

## Security & Ethics

### Privacy Protection
- **Data Minimization**: Only collect features needed for model
- **Retention**: 7 days logs, 30 days training data
- **Anonymization**: Hash IP addresses after 24 hours
- **Encryption**: All data encrypted at rest and in transit

### Compliance
- **GDPR Article 6**: Legitimate interest for fraud prevention
- **Right to Explanation**: Provide reason codes for decisions
- **Appeals Process**: Human review queue for high-impact blocks

### Ethical Guidelines
1. **No discrimination**: VPN usage alone ≠ malicious
2. **Proportional response**: Prefer CHALLENGE over BLOCK
3. **Transparency**: Document detection methods in privacy policy
4. **Continuous monitoring**: Track and fix false positives

### Deanonymisation (Caution)
**Passive techniques** (lawful for forensics):
- DNS/WebRTC leak detection
- MTU/MSS fingerprinting
- Timing correlation

**Active techniques** (requires legal approval):
- Canarytokens / honeypots
- Traffic manipulation (DO NOT USE without authorization)

⚠️ **Legal Notice**: Deanonymisation has serious legal/ethical constraints. Always obtain proper authorization and consult legal counsel.

---

## Monitoring & Maintenance

### Metrics to Track
- **Prediction latency** (P50, P95, P99)
- **False Positive Rate** (per policy tier)
- **Cache hit rate**
- **Model drift** (compare live vs validation distribution)

### Alerting
```yaml
alerts:
  - name: HighLatency
    condition: p99_latency > 300ms
    action: scale_up
    
  - name: HighFPR
    condition: fpr > 0.05
    action: rollback_model + alert_team
    
  - name: ModelDrift
    condition: feature_distribution_divergence > 0.3
    action: trigger_retraining
```

### Model Retraining
**Trigger Conditions**:
- FPR > 5% for 24 hours
- New attack patterns detected
- Scheduled: Monthly

**Process**:
1. Collect false positives from review queue
2. Label and add to training set
3. Retrain Stage-2 model
4. A/B test on 10% traffic
5. Full rollout if metrics improve

---

## Next Steps

### Immediate (Sprint 1-2)
1. ✅ Generate Packet-Block images from VNAT dataset
2. ✅ Train Stage-1 CNN on application classification
3. ⬜ Validate Stage-1 model (target: >85% accuracy)
4. ⬜ Implement edge layer IP intelligence integration

### Short-term (Sprint 3-4)
5. ⬜ Merge datasets for Stage-2 training
6. ⬜ Train and tune Stage-2 XGBoost model
7. ⬜ Deploy inference stack to dev cluster
8. ⬜ Implement monitoring/logging (ELK/Prometheus)

### Long-term (Sprint 5-6)
9. ⬜ Production deployment with canary rollout
10. ⬜ Integrate feedback loop for continuous learning
11. ⬜ Implement graph anomaly detector (unsupervised)
12. ⬜ Optimize for GPU acceleration (TensorRT)

---

**Last Updated**: November 9, 2025  
**Version**: 1.0.0  
**Maintainer**: MD Hassan
