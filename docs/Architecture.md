# System Architecture

![System Architecture](../architecture/architecture-diagram.svg)

## 1. Domain Overview
The system operates at the intersection of cybersecurity, networking, and machine learning to detect VPN-mediated traffic and deanonymise user intent ethically. It distinguishes benign privacy usage from malicious abuse (C2, credential stuffing, infiltration) relying on metadata, timing, and flow patterns—never deep payload inspection of encrypted content.

## 2. Problem With Existing Systems
Limitations of static rules, IP blacklists, and DPI under modern encryption lead to poor visibility, latency costs, and privacy trade-offs.

| Limitation | Description |
|------------|-------------|
| Encrypted Payloads | TLS 1.3 + ECH defeat DPI signatures. |
| Evasion Techniques | Rapid IP/port/fingerprint rotation by VPN vendors. |
| Binary Decisions | Allow/Block lacks contextual risk tiers. |
| Privacy Risks | Aggressive inspection erodes user trust. |
| Performance Bottlenecks | High-latency inspection fails at scale. |

## 3. Multi-Layer Architecture (Overview)
1. Edge Firewall: Fast pre-filter (IP reputation, MTU/MSS fingerprint) <10 ms.
2. TLS Load Balancer: Controlled termination to extract JA3, SNI, RTT without full content exposure.
3. ML Risk Engine: Two-stage pipeline — CNN application classification then ensemble (XGBoost / RF) intent scoring (0–99).
4. Policy Engine: Adaptive enforcement via risk tiers with logging & feedback loops.
Support Infrastructure: MinIO (model artifacts), Redis (low-latency lookups), YAML configs, Prometheus/Grafana & ELK for observability.

## 4. Model Stack
Stage 1 CNN:
- Input: 64×64×3 Packet Block Image (direction, size, timing encoded).
- Architecture: Conv2D(32)→Pool→Conv2D(64)→Pool→Flatten→Dense(128)→Dropout(0.5)→Softmax(7 classes).
- Datasets: ISCXVPN2016, VNAT.
- Metrics: Accuracy ≈ 98.1%, F1 ≈ 0.92.

Stage 2 Ensemble (XGBoost / RandomForest):
- Input Features: 25+ (IP intelligence, statistical flow features, CNN App_Class).
- Datasets: CIC-IDS2017, USTC-TFC2016, UNSW-NB15.
- Metrics: AUC ≈ 0.953, Precision ≈ 97.4%, Recall ≈ 96.9%.

Zero-Day Graph Layer (Future / Optional):
- Unsupervised graph analytics for anomalous structural patterns (many-to-one C2, lateral scans).

## 5. Risk Tier Policy
| Tier | Score Range | Action | Notes |
|------|-------------|--------|-------|
| Low  | 0–20        | ALLOW  | Normal usage. |
| Medium | 21–60     | CHALLENGE | CAPTCHA / MFA friction to validate legitimacy. |
| High | 61–99       | BLOCK / RATE-LIMIT | Potential malicious automation or exfiltration. |

Thresholds are YAML-configurable for rapid tuning without redeploying code or models.

## 6. Algorithmic Flow (Condensed)
1. Edge Firewall:
   - Query IP intelligence APIs.
   - Extract MSS/MTU from TCP SYN.
   - Early flag if MTU anomaly or fraud score high.
2. TLS Load Balancer:
   - Controlled decryption for handshake metadata (SNI, JA3, RTT).
3. ML Risk Engine:
   - App_Class = CNN(PacketBlockImage(flow)).
   - Risk_Score = XGBoost(Features ∪ {App_Class}).
4. Policy Engine:
   - Map Risk_Score to tier → action.
5. Observability:
   - Export metrics, log decision, feed back mislabeled cases for retraining.

Pseudo:
```
App_Class = CNN(image(flow))
Risk_Score = XGBoost(feature_vector + App_Class)
if Risk_Score <= 20: ALLOW
elif Risk_Score <= 60: CHALLENGE
else: BLOCK
log(decision, Risk_Score, features)
update_metrics()
```

## 7. Monitoring & Feedback Loop
- Prometheus counters: vpn_flows_total, blocked_flows_total, challenge_ratio.
- Grafana dashboards for latency, model inference time, false-positive review queue length.
- ELK for structured decision logs (JSON schema: timestamp, ip, risk_score, action, features_hash).
- Periodic drift analysis: compare feature distributions vs. training baseline (saved in MinIO).

## 8. Privacy & Ethics
- No payload content stored.
- Metadata retention minimized and hashed where feasible.
- Challenge mechanism avoids unnecessary blocking of legitimate privacy users.

## 9. Future Enhancements
- Integrate lightweight ONNX runtime for CNN edge inference.
- Deploy graph anomaly detector (GNN or community detection) for zero-day C2.
- Adaptive policy tuning via reinforcement signals (success of challenges, false-positive appeals).
- Federated learning across multiple edge sites (share gradients, preserve raw data locality).

## 10. Summary
The layered design merges deterministic fingerprinting with probabilistic ML to yield real-time, nuanced VPN user intent scoring while respecting encryption boundaries. Subsequent implementation work will cover dataset acquisition, training pipelines, deployment manifests, and operational runbooks.
