# Deployment Quick Start Guide

This guide walks you through deploying the VPN Detection & Deanonymisation inference system on Kubernetes.

## Prerequisites

- Kubernetes 1.24+ cluster
- kubectl configured
- Docker installed
- At least 4 CPU cores, 8GB RAM available
- (Optional) GPU nodes for CNN acceleration

## Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   MinIO     │──────│  TF Serving  │──────│  Inference API  │
│  (Models)   │      │  (Stage-1)   │      │  (FastAPI)      │
└─────────────┘      └──────────────┘      └─────────────────┘
                             │                        │
                             │                        │
                     ┌───────┴────────────────────────┴───────┐
                     │          Redis (Cache)                 │
                     └────────────────────────────────────────┘
```

## Step-by-Step Deployment

### 1. Build the Inference API Container

```bash
cd /path/to/VPN Detection & Deanoymisation

# Build Docker image
docker build -t yourrepo/vpn-inference-api:v1.0 \
  -f deployment/docker/Dockerfile.inference-api \
  inference/

# Push to your registry
docker push yourrepo/vpn-inference-api:v1.0
```

**Update the image reference** in `deployment/k8s/06-inference-api.yaml`:
```yaml
image: yourrepo/vpn-inference-api:v1.0  # Change this line
```

---

### 2. Deploy Infrastructure Components

```bash
cd deployment/k8s

# Create namespace
kubectl apply -f 01-namespace.yaml

# Deploy configuration
kubectl apply -f 02-config.yaml

# Deploy MinIO (model storage)
kubectl apply -f 03-minio.yaml

# Deploy Redis (cache)
kubectl apply -f 04-redis.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=minio -n vpn-inference --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n vpn-inference --timeout=120s

# Verify
kubectl get pods -n vpn-inference
```

Expected output:
```
NAME                     READY   STATUS    RESTARTS   AGE
minio-xxxxx             1/1     Running   0          2m
redis-xxxxx             1/1     Running   0          2m
```

---

### 3. Upload Models to MinIO

First, train your models (see [Model Training](#model-training)) or use placeholder models for testing.

```bash
# Port-forward MinIO
kubectl port-forward -n vpn-inference svc/minio 9000:9000 &

# Install MinIO client (if not installed)
# macOS: brew install minio/stable/mc
# Linux: wget https://dl.min.io/client/mc/release/linux-amd64/mc

# Configure MinIO client
mc alias set minio http://localhost:9000 minioaccesskey miniosecretkey

# Create bucket
mc mb minio/models

# Upload models
mc cp --recursive ./inference/models/stage1 minio/models/stage1/
mc cp --recursive ./inference/models/stage2 minio/models/stage2/

# Verify upload
mc ls minio/models/
```

---

### 4. Deploy Inference Stack

```bash
# Deploy TensorFlow Serving (Stage-1 CNN)
kubectl apply -f 05-tf-serving.yaml

# Wait for model download
kubectl wait --for=condition=ready pod -l app=tf-serving -n vpn-inference --timeout=300s

# Deploy Inference API (FastAPI)
kubectl apply -f 06-inference-api.yaml

# Wait for API pods
kubectl wait --for=condition=ready pod -l app=inference-api -n vpn-inference --timeout=180s

# Deploy Ingress (optional)
kubectl apply -f 07-ingress.yaml
```

---

### 5. Verify Deployment

```bash
# Check all pods
kubectl get pods -n vpn-inference

# Expected output:
# NAME                             READY   STATUS    RESTARTS   AGE
# inference-api-xxxxx             1/1     Running   0          3m
# inference-api-yyyyy             1/1     Running   0          3m
# minio-xxxxx                     1/1     Running   0          10m
# redis-xxxxx                     1/1     Running   0          10m
# tf-serving-xxxxx                1/1     Running   0          5m

# Check logs
kubectl logs -n vpn-inference -l app=inference-api --tail=50

# Port-forward API
kubectl port-forward -n vpn-inference svc/inference-api 8080:8080
```

---

### 6. Test the API

**Health Check**:
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "redis_connected": true,
  "version": "1.0.0"
}
```

**Prediction Test**:
```bash
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "src_ip": "192.168.1.100",
    "dst_ip": "8.8.8.8",
    "src_port": 51234,
    "dst_port": 443,
    "protocol": "TCP",
    "is_vpn": true,
    "is_datacenter": false,
    "fraud_score": 25,
    "flow_duration": 45.2,
    "total_fwd_packets": 120,
    "total_bwd_packets": 98,
    "human_score": 0.92,
    "login_failure_rate": 0.0
  }'
```

Expected response:
```json
{
  "request_id": "req_1699564321000",
  "risk_score": 18,
  "app_class": "BROWSING",
  "app_confidence": 0.87,
  "intent_class": "BENIGN",
  "intent_confidence": 0.82,
  "action": "ALLOW",
  "reason": "Low risk - legitimate traffic pattern detected",
  "latency_ms": 87.3,
  "cached": false
}
```

---

## Model Training

### Stage-1: Application Classifier (CNN)

```bash
cd preprocessing

# Generate Packet-Block images from USTC dataset
python scripts/pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/Benign/ \
  --out-dir ./outputs/packetblock_images/benign/ \
  --img-size 64

python scripts/pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/Malware/ \
  --out-dir ./outputs/packetblock_images/malware/ \
  --img-size 64

# Train CNN
cd ../model_training/stage1_app_classifier
python train_cnn.py \
  --image-dir ../../preprocessing/outputs/packetblock_images/ \
  --output-dir ../../inference/models/stage1/ \
  --epochs 50 \
  --batch-size 32

# Validate model
python evaluate.py \
  --model-dir ../../inference/models/stage1/ \
  --test-data ../../preprocessing/outputs/test_images/
```

### Stage-2: Intent Classifier (XGBoost)

```bash
cd preprocessing

# Merge datasets
python scripts/merge_datasets.py \
  --config configs/merge_config.yaml

# Feature extraction
python scripts/feature_extractor.py \
  --input outputs/Unified_Dataset.csv \
  --output outputs/stage2_features.csv

# Train XGBoost
cd ../model_training/stage2_intent_classifier
python train_xgboost.py \
  --input ../../preprocessing/outputs/stage2_features.csv \
  --output ../../inference/models/stage2/model.xgb \
  --n-estimators 200

# Validate
python evaluate.py \
  --model ../../inference/models/stage2/model.xgb \
  --test-data ../../preprocessing/outputs/test_features.csv
```

---

## Scaling & Production

### Horizontal Pod Autoscaling

HPA is already configured in `06-inference-api.yaml`:
- Min replicas: 2
- Max replicas: 10
- Target CPU: 60%

Monitor autoscaling:
```bash
kubectl get hpa -n vpn-inference
watch kubectl get pods -n vpn-inference
```

### GPU Acceleration (Optional)

For faster Stage-1 CNN inference, deploy on GPU nodes:

1. **Add GPU node pool** to your cluster
2. **Update TF Serving deployment**:
```yaml
# In 05-tf-serving.yaml
resources:
  limits:
    nvidia.com/gpu: 1  # Add this
```
3. **Use GPU-optimized TF Serving image**:
```yaml
image: tensorflow/serving:2.13.0-gpu
```

### Production Checklist

- [ ] Replace placeholder secrets in `02-config.yaml`
- [ ] Use persistent volumes for MinIO (not emptyDir)
- [ ] Configure ingress with TLS/SSL
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log aggregation (ELK or Loki)
- [ ] Implement backup for models
- [ ] Set up alerts for high FPR
- [ ] Document incident response procedures

---

## Troubleshooting

### Models Not Loading

```bash
# Check initContainer logs
kubectl logs -n vpn-inference tf-serving-xxxxx -c fetch-models

# Verify MinIO contents
kubectl port-forward -n vpn-inference svc/minio 9000:9000
mc ls minio/models/
```

### High Latency

```bash
# Check resource usage
kubectl top pods -n vpn-inference

# Scale up manually
kubectl scale deployment inference-api -n vpn-inference --replicas=5

# Check Redis connection
kubectl exec -it -n vpn-inference redis-xxxxx -- redis-cli ping
```

### Prediction Errors

```bash
# View API logs
kubectl logs -n vpn-inference -l app=inference-api -f

# Check model versions
kubectl exec -it -n vpn-inference inference-api-xxxxx -- ls -la /models/
```

---

## Clean Up

```bash
# Delete all resources
kubectl delete namespace vpn-inference

# Or delete individually
kubectl delete -f deployment/k8s/
```

---

## Next Steps

1. **Set up monitoring**: Deploy Prometheus + Grafana
2. **Configure alerts**: High latency, FPR, model drift
3. **Implement feedback loop**: Collect false positives for retraining
4. **Load testing**: Use k6 or locust to validate throughput
5. **Security hardening**: Network policies, pod security policies

---

**Support**: See full documentation in `docs/architecture/IMPLEMENTATION_GUIDE.md`
