# VPN Detection & Deanonymisation Project

A production-ready, multi-layer ML pipeline for detecting and classifying VPN traffic with risk-based policy enforcement.

## 🎯 Project Overview

This system implements a **4-layer architecture** that:
1. **Filters** obvious threats at the edge (<10ms)
2. **Decrypts** traffic at the gateway for deep inspection
3. **Classifies** applications using CNN (Packet-Block images)
4. **Scores** intent/risk using XGBoost for adaptive policy

**Key Features**:
- ✅ Two-stage ML pipeline (App → Intent)
- ✅ Privacy-respecting (VPN ≠ auto-block)
- ✅ Low latency (<200ms end-to-end)
- ✅ Kubernetes-native with autoscaling
- ✅ Comprehensive dataset support (VNAT, ISCX, CIC-IDS, USTC)

---

## 📁 Project Structure

```
├── preprocessing/           # Data pipeline & ETL
│   ├── scripts/
│   │   ├── pcap_to_packetblock.py    # PCAP → Images
│   │   ├── merge_datasets.py         # Dataset unification
│   │   └── feature_extractor.py      # Feature engineering
│   └── configs/
│       └── merge_config.yaml
│
├── model_training/          # ML model training
│   ├── stage1_app_classifier/        # CNN (8 app classes)
│   └── stage2_intent_classifier/     # XGBoost (risk scoring)
│
├── inference/               # Production inference service
│   ├── app/
│   │   ├── main.py                   # FastAPI service
│   │   ├── model_loader.py           # TF + XGBoost loader
│   │   ├── predict.py                # Two-stage pipeline
│   │   └── utils.py                  # Feature extraction
│   └── requirements.txt
│
├── deployment/              # Kubernetes deployment
│   ├── docker/
│   │   └── Dockerfile.inference-api
│   └── k8s/
│       ├── 01-namespace.yaml
│       ├── 02-config.yaml
│       ├── 03-minio.yaml             # Model storage
│       ├── 04-redis.yaml             # Cache
│       ├── 05-tf-serving.yaml        # Stage-1 CNN server
│       ├── 06-inference-api.yaml     # FastAPI + HPA
│       └── 07-ingress.yaml
│
├── docs/
│   ├── architecture/
│   │   ├── SYSTEM_ARCHITECTURE.md    # Original design doc
│   │   └── IMPLEMENTATION_GUIDE.md   # Complete guide
│   └── preprocessing/
│       └── PREPROCESSING_GUIDE.md
│
└── datasets/                # Raw datasets
    ├── CIC-IDS2017/
    └── USTC-TFC2016-master/
```

---

## 🚀 Quick Start

### 1. Generate Packet-Block Images

```bash
cd preprocessing

# Process USTC dataset
python scripts/pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/Benign/ \
  --out-dir ./outputs/packetblock_images/ \
  --img-size 64

# Output: ~500 images + manifest.csv
```

### 2. Train Models

```bash
# Stage-1: Application Classifier (CNN)
cd model_training/stage1_app_classifier
python train_cnn.py --image-dir ../../preprocessing/outputs/packetblock_images/ --epochs 50

# Stage-2: Intent Classifier (XGBoost)
cd ../stage2_intent_classifier
python train_xgboost.py --input ../../preprocessing/outputs/stage2_features.csv --n-estimators 200
```

### 3. Deploy to Kubernetes

```bash
cd deployment/k8s

# Deploy all components
kubectl apply -f 01-namespace.yaml
kubectl apply -f 02-config.yaml
kubectl apply -f 03-minio.yaml
kubectl apply -f 04-redis.yaml
kubectl apply -f 05-tf-serving.yaml
kubectl apply -f 06-inference-api.yaml

# Verify
kubectl get pods -n vpn-inference
```

### 4. Test Inference

```bash
# Port-forward
kubectl port-forward -n vpn-inference svc/inference-api 8080:8080

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
    "fraud_score": 25,
    "flow_duration": 45.2,
    "human_score": 0.92
  }'
```

---

## 📊 Datasets

| Dataset | Size | Purpose | Labels |
|---------|------|---------|--------|
| **VNAT** | 36GB | App classification + C2 | 5 app types + C2 |
| **ISCXVPN2016** | 28GB | VPN vs Non-VPN + Apps | 7 app types |
| **CIC-IDS2017** | Parquet | Attack detection | Benign + 7 attack types |
| **USTC-TFC2016** | PCAPs | Benign vs Malware | 10 benign + 8 malware |

---

## 🏗️ Architecture Layers

### Layer 1: Edge Firewall
- **IP Intelligence** (IPQualityScore/IPinfo API)
- **MTU/MSS Fingerprinting** (passive TCP analysis)
- **Latency**: <10ms

### Layer 2: TLS Termination
- Decrypt traffic at gateway
- Extract headers + fingerprints
- Defeats ECH/TLS 1.3 obfuscation

### Layer 3: ML Risk Scoring Engine

**Stage-1: CNN (Application Classifier)**
- Input: 64×64×3 Packet-Block images
- Output: 8 app classes (BROWSING, CHAT, VOIP, VIDEO, etc.)
- Latency: ~50ms

**Stage-2: XGBoost (Intent Classifier)**
- Input: 25-feature vector (IP intel + flow stats + behavioral)
- Output: Risk score 0-99
- Latency: ~50ms

### Layer 4: Policy Engine

| Risk Score | Action | Description |
|------------|--------|-------------|
| 0-20 | **ALLOW** | Low risk, legitimate traffic |
| 21-60 | **CHALLENGE** | MFA/CAPTCHA required |
| 61-99 | **BLOCK** | High risk, suspicious activity |

---

## 🎓 Key Innovations

1. **Packet-Block Images**: Novel encoding of flows as images for CNN
2. **Two-stage Pipeline**: Separates "what" (app) from "why" (intent)
3. **Privacy-first**: VPN usage alone doesn't trigger block
4. **Adaptive Policy**: Risk-based responses with human-readable reasons

---

## 📈 Performance Targets

| Metric | Target | Achieved |
|--------|--------|----------|
| End-to-end Latency (P99) | <200ms | ⬜ TBD |
| Throughput | 10K req/s | ⬜ TBD |
| Stage-1 Accuracy | >90% F1 | ⬜ TBD |
| Stage-2 AUC | >0.95 | ⬜ TBD |
| False Positive Rate | <2% | ⬜ TBD |

---

## 🔒 Security & Ethics

- **Data Minimization**: Only collect necessary features
- **Retention**: 7 days logs, 30 days training data
- **GDPR Compliant**: Legitimate interest for fraud prevention
- **Transparency**: Provide reason codes for all decisions
- **Appeals**: Human review queue for high-impact blocks

⚠️ **Deanonymisation Warning**: Active techniques (traffic manipulation, honeypots) require legal authorization. This project focuses on passive detection methods.

---

## 📚 Documentation

- **[System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)**: Original design document
- **[Implementation Guide](docs/architecture/IMPLEMENTATION_GUIDE.md)**: Complete step-by-step guide
- **[Deployment Guide](deployment/README.md)**: Kubernetes deployment instructions
- **[Preprocessing Guide](preprocessing/README.md)**: Data pipeline documentation

---

## 🛠️ Development Setup

### Prerequisites
- Python 3.9+
- Docker
- Kubernetes (minikube/kind for local testing)
- kubectl

### Install Dependencies

```bash
# Preprocessing
cd preprocessing
pip install -r requirements.txt

# Inference service
cd ../inference
pip install -r requirements.txt
```

### Run Tests

```bash
# Unit tests
pytest inference/tests/

# Integration tests
pytest preprocessing/tests/
```

---

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (Completed)
- [x] Project structure
- [x] Packet-Block image generation
- [x] FastAPI inference service
- [x] Kubernetes manifests
- [x] Documentation

### ⬜ Phase 2: Training (In Progress)
- [ ] Train Stage-1 CNN on USTC/VNAT
- [ ] Train Stage-2 XGBoost on CIC-IDS
- [ ] Validate models (>85% accuracy target)
- [ ] Model versioning & registry

### ⬜ Phase 3: Deployment (Planned)
- [ ] Deploy to dev cluster
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Load testing (k6)
- [ ] Production deployment with canary

### ⬜ Phase 4: Optimization (Future)
- [ ] GPU acceleration (TensorRT)
- [ ] Graph anomaly detector (unsupervised)
- [ ] Feedback loop for continuous learning
- [ ] A/B testing framework

---

## 🤝 Contributing

This is a research/academic project. Contributions welcome:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

**Please ensure**:
- Code follows PEP 8 style
- Tests pass (`pytest`)
- Documentation updated

---

## 📄 License

[Specify License]

---

## 👤 Author

**MD Hassan**  

---

## 🙏 Acknowledgments

- **Datasets**: VNAT (MIT Lincoln Lab), CIC-IDS (Canadian Institute for Cybersecurity), USTC
- **Inspiration**: PacketPrint (IEEE S&P 2020), FlowPic (NDSS 2020)
- **Tools**: TensorFlow, XGBoost, FastAPI, Kubernetes

---

**Last Updated**: March 19, 2026  
**Version**: 1.0.0

---

## 📞 Support

For questions or issues:
- 📖 Check [Documentation](docs/)
- 🐛 Report bugs via GitHub Issues
- 💬 Discussions: [Your Discussion Forum/Email]
