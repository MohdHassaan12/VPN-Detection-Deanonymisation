# VPN Segregation System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: EDGE FIREWALL                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  • IP Intelligence Check (IPQualityScore/IPinfo API)     │   │
│  │  • MTU/MSS Fingerprinting (Passive TCP Analysis)         │   │
│  │  • Fast Filter: Block obvious threats                    │   │
│  │  • Latency: <10ms                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                   ┌────────────┴────────────┐
                   │   Pass-Through (90%)    │
                   │   Block (10% - obvious) │
                   └────────────┬────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LAYER 2: LOAD BALANCER                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  • TLS Termination (Decrypt Traffic)                     │   │
│  │  • Protocol Fingerprinting (OpenVPN/WireGuard)           │   │
│  │  • Extract Application Headers                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 3: ML RISK SCORING ENGINE                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  STAGE 1: Application Classifier (CNN)                   │   │
│  │  • Input: Packet Block Images or Flow Statistics         │   │
│  │  • Output: App_Class (Browsing/Chat/VoIP/C2/etc.)        │   │
│  │  • Latency: ~50ms                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  STAGE 2: Intent Classifier (Random Forest/XGBoost)      │   │
│  │  • Input: 15+ features (IP, App, Behavioral)             │   │
│  │  • Output: Risk Score (0-99)                             │   │
│  │  • Latency: ~50ms                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LAYER 4: POLICY ENGINE                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Risk Score Evaluation & Action Decision                 │   │
│  │  • Score 1-20:  ALLOW (Full Access)                      │   │
│  │  • Score 21-60: CHALLENGE (MFA/CAPTCHA)                  │   │
│  │  • Score 61-99: BLOCK/RATE-LIMIT                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION SERVER                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING & LOGGING                          │
│  • Event Log: All risk scores and decisions                     │
│  • Metrics: FPR, FNR, Latency, Threat counts                    │
│  • Feedback Loop: Retrain models on false positives             │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Edge Firewall (Fast Filter)
**Purpose**: Eliminate obvious threats before expensive ML processing

**Capabilities**:
- Query IP intelligence APIs in parallel
- Passive MTU detection from TCP handshake
- Simple rule-based blocking (known malicious IPs)

**Decision Logic**:
```python
if ip_fraud_score > 90:
    return BLOCK
elif ip_type == "datacenter" and known_bad_asn:
    return BLOCK
elif mtu_value < 1350:
    flag_as_vpn = True
    
# Pass through to next layer for detailed analysis
```

### 2. Load Balancer (TLS Termination)
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

### 3. ML Risk Scoring Engine (Two-Stage Pipeline)

#### Stage 1: Application Classifier
**Model Type**: CNN (Convolutional Neural Network)

**Input Format Options**:
1. **Packet Block Images** (64x64x3 RGB)
2. **Flow Statistics** (20-30 numerical features)

**Training Data**:
- ISCXVPN2016 (28GB, 7 app types)
- VNAT (36GB, 5 app types + C2)

**Output**: One of 8 classes
- BROWSING, CHAT, VOIP, VIDEO, FILE_TRANSFER, P2P, C2_CNC, UNKNOWN

#### Stage 2: Intent Classifier
**Model Type**: Random Forest or XGBoost

**Input**: Comprehensive feature vector (15+ features)

**Training Data**:
- CIC-IDS-2017 (attack patterns)
- USTC-TFC2016 (malware vs benign)
- UNSW-NB15 (diverse attacks)

**Output**: Risk score 0-99

### 4. Policy Engine (Action Decision)
**Purpose**: Convert risk score to business action

**Policy Configuration** (Adjustable):
```yaml
policies:
  low_risk:
    threshold: [0, 20]
    action: ALLOW
    logging: minimal
    
  medium_risk:
    threshold: [21, 60]
    action: CHALLENGE
    challenge_types:
      - MFA
      - CAPTCHA
      - Email_Verification
    logging: detailed
    
  high_risk:
    threshold: [61, 99]
    action: BLOCK
    rate_limit: true
    alert: security_team
    logging: full
```

## Data Flow Example

### Scenario 1: Benign Privacy User
```
User: Customer using NordVPN to access banking website

Flow:
1. Edge Firewall:
   - IP Check: is_vpn=true, ip_type=residential, fraud_score=15
   - MTU: 1420 (WireGuard detected)
   - Action: PASS_THROUGH

2. Load Balancer:
   - TLS Decrypt: Standard browser fingerprint
   - Protocol: WireGuard confirmed

3. ML Engine:
   Stage 1: app_class = BROWSING
   Stage 2: 
     - human_score = 0.95 (mouse movements detected)
     - login_failure_rate = 0.0
     - fingerprint_mismatch = false
     - RISK SCORE = 18

4. Policy Engine:
   - Score 18 → LOW_RISK tier
   - Action: ALLOW
   - User Experience: Seamless login ✅
```

### Scenario 2: Credential Stuffing Bot
```
Attacker: Bot using datacenter VPN pool for credential stuffing

Flow:
1. Edge Firewall:
   - IP Check: is_vpn=true, ip_type=datacenter, fraud_score=75
   - MTU: 1380 (OpenVPN)
   - Action: FLAG + PASS_THROUGH (for ML analysis)

2. Load Balancer:
   - TLS Decrypt: User-Agent = "Chrome/120" but TLS fingerprint = Python/Requests
   - Protocol: OpenVPN

3. ML Engine:
   Stage 1: app_class = BROWSING
   Stage 2:
     - human_score = 0.05 (no mouse/keyboard)
     - login_failure_rate = 0.92 (92% failures in 5min window)
     - fingerprint_mismatch = true
     - account_velocity = 45 (tried 45 different accounts)
     - RISK SCORE = 94

4. Policy Engine:
   - Score 94 → HIGH_RISK tier
   - Action: BLOCK + LOG + ALERT
   - User Experience: Connection refused ❌
```

### Scenario 3: Suspicious But Uncertain
```
User: New user on datacenter VPN, first login attempt

Flow:
1-2. Edge + Load Balancer: Flags as datacenter VPN

3. ML Engine:
   Stage 1: app_class = BROWSING
   Stage 2:
     - human_score = 0.85 (appears human)
     - login_failure_rate = 0.0 (first attempt)
     - new_device = true
     - RISK SCORE = 45

4. Policy Engine:
   - Score 45 → MEDIUM_RISK tier
   - Action: CHALLENGE (Request MFA)
   - User Experience: "Please verify your identity via email" ⚠️
   - If user passes MFA → Whitelisted for future logins
```

## Technology Stack

### Infrastructure
- **Edge Firewall**: NGINX/HAProxy with Lua scripting
- **Load Balancer**: NGINX Plus or AWS ALB
- **API Gateway**: Kong or AWS API Gateway

### ML/Data Processing
- **Language**: Python 3.9+
- **ML Frameworks**: 
  - TensorFlow/Keras (CNN for Stage 1)
  - Scikit-learn/XGBoost (Stage 2)
- **Packet Analysis**: Scapy, PyShark
- **Feature Store**: Redis (real-time) + PostgreSQL (historical)

### Deployment
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **Model Serving**: TensorFlow Serving or FastAPI
- **Monitoring**: Prometheus + Grafana

### Data Storage
- **Live Traffic**: Redis (session state, recent flows)
- **Model Training**: S3 or MinIO (PCAP files, datasets)
- **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana)

## Scalability Considerations

### Performance Targets
- **Throughput**: 10,000 requests/second
- **Latency**: <200ms end-to-end (P99)
- **Availability**: 99.9% uptime

### Scaling Strategy
1. **Horizontal Scaling**: 
   - Stateless ML inference services
   - Load balance across multiple instances

2. **Caching**:
   - Cache IP intelligence results (TTL: 1 hour)
   - Cache risk scores for known good IPs (TTL: 24 hours)

3. **Optimization**:
   - Use model quantization (INT8) for faster inference
   - Batch predictions when possible
   - GPU acceleration for CNN (Stage 1)

## Security & Privacy

### Data Protection
- Encrypt all PII at rest and in transit
- Anonymize logs (hash IP addresses after 24 hours)
- Minimum data retention (30 days for training, 7 days for logs)

### Compliance
- **GDPR Article 6**: Legitimate interest for fraud prevention
- **Data Minimization**: Only collect features needed for model
- **Right to Explanation**: Provide reason codes for blocks/challenges
- **Privacy Policy**: Clearly document VPN detection and behavioral analysis

### Ethical Guidelines
- **No discrimination**: VPN usage alone ≠ high risk
- **Proportional response**: Prefer Challenge over Block
- **Continuous monitoring**: Track and fix false positives
- **User feedback**: Provide appeals process

## Disaster Recovery

### Fallback Modes
1. **ML Service Down**: Fall back to IP-based rules only
2. **IP API Down**: Use cached results + MTU detection
3. **Complete Failure**: Allow all traffic (fail-open) with logging

### Model Rollback
- Maintain last 3 model versions
- Automated A/B testing before full deployment
- Instant rollback if FPR > 5%

---

**Last Updated**: November 9, 2025
