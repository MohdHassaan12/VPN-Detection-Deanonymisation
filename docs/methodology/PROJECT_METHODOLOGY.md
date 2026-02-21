# VPN User ML Segregation Model - Complete Methodology

## Executive Summary

This document outlines a comprehensive methodology for building a machine learning system that:
1. **Detects VPN/Proxy traffic** using multi-layered fingerprinting
2. **Classifies user intent** to distinguish benign privacy-seekers from malicious actors
3. **Implements risk-based policies** (Allow/Challenge/Block) instead of blanket blocking

**Core Philosophy**: Move from content analysis to context analysis. Since encryption prevents payload inspection, we analyze the shape, timing, source, and behavior of traffic.

---

## Phase 1: VPN Detection Layer (The Filter)

### 1.1 IP-Based Intelligence (Layer 1)

**Purpose**: Fast, inexpensive first-pass filter using IP reputation databases.

**Implementation Strategy**:
```
Incoming Connection → Extract Source IP → Query IP Intelligence API → Extract Features
```

**Key Features to Extract**:
- `is_vpn`, `is_proxy`, `is_tor` (Boolean flags)
- `ip_type`: **Datacenter vs. Residential vs. Mobile** (Critical segregation feature)
- `fraud_score`: Pre-computed risk score (0-100)
- `asn`: Autonomous System Number
- `provider_name`: VPN service provider (e.g., "NordVPN")

**Why IP Type Matters**:
- **Datacenter IPs**: Cheap, bulk-sourced from cloud providers → Used by 90% of automated attacks (bots, scrapers, credential stuffing)
- **Residential IPs**: Expensive, from real ISPs → Used by sophisticated actors OR legitimate privacy users
- **Risk Scoring Impact**: Datacenter = Higher baseline risk score

**Recommended Providers**:
- IPQualityScore (most comprehensive fraud scoring)
- IPinfo (good coverage, developer-friendly)
- IP2Proxy (VPN-specific database)

---

### 1.2 Protocol Fingerprinting (Layer 2)

**Purpose**: Detect "unknown" or self-hosted VPNs not in IP databases.

#### A. MTU/MSS Fingerprinting (Most Robust)

**Theory**: VPN encapsulation adds protocol headers → Reduces effective MTU → Observable in TCP handshake

**Normal Traffic**:
- Ethernet MTU: 1500 bytes
- TCP MSS (in SYN packet): 1460 bytes

**VPN Signatures**:
- IPsec/Azure VPN: MSS ≈ 1350 bytes
- WireGuard: MSS ≈ 1420-1440 bytes  
- OpenVPN: MSS ≈ 1380-1409 bytes

**Implementation**:
```python
# Parse TCP SYN packet (unencrypted)
# Extract MSS option from TCP Options field
if MSS < 1440:
    vpn_detected = True
    confidence = 0.85
```

**Advantages**:
- Protocol-agnostic (works on any VPN)
- Passive detection (no active probing)
- Cannot be easily hidden without performance penalty

#### B. Protocol-Specific DPI Signatures

**OpenVPN Detection**:
- Look for byte pattern `0x38` (handshake opcode) in UDP payload
- Detect characteristic packet sizes during handshake
- 85%+ accuracy even with obfuscation

**WireGuard Detection**:
- Fixed-size headers (unique signature)
- Distinct 4-message handshake pattern

---

### 1.3 Statistical Traffic Analysis (Layer 3)

**Additional Features**:
- **RTT (Round-Trip Time)**: VPNs add latency → Measurable delay increase
- **TCP/IP Fingerprinting**: OS-level fingerprint mismatch
  - Example: User-Agent says "Windows 11" but TCP stack says "Linux kernel 5.x"
  - Strong proxy/VPN indicator

---

## Phase 2: Two-Stage ML Segregation Pipeline

### Stage 1: Application Classification (What is the user doing?)

**Goal**: Classify encrypted traffic into application categories.

**Output Classes**:
- `BROWSING` (Web traffic)
- `CHAT` (Messaging apps)
- `VOIP` (Voice calls)
- `VIDEO` (Streaming)
- `FILE_TRANSFER` (Downloads/uploads)
- `P2P` (BitTorrent, etc.)
- `C2_CNC` (Command & Control - malicious)
- `UNKNOWN`

#### Feature Engineering: Packet Block Image (CNN-Based)

**Concept**: Convert traffic flow into a 2D visual "texture" image, then use CNN for classification.

**Process**:
1. **Define Packet Block**: Group of consecutive packets in same direction
2. **Generate Image**: 64x64 pixel image where:
   - Row = Packet block sequence
   - Color intensity = Block size
   - Red channel = Client → Server
   - Green channel = Server → Client
3. **Visual Signatures**:
   - VoIP: Regular, small, bi-directional blocks (conversation pattern)
   - File Download: Large, uni-directional block (sustained transfer)
   - Web Browsing: Bursty pattern (request → response → request)
   - C2 Traffic: Small, periodic, regular blocks (heartbeat)

**Model Architecture**:
```
Input (64x64x3 image) 
→ Conv2D(32) → MaxPool 
→ Conv2D(64) → MaxPool 
→ Conv2D(64) 
→ Flatten → Dense(64) → Dropout(0.5) 
→ Output (8 classes, softmax)
```

**Alternative: Flow Statistics**
For simpler implementation, use statistical features:
- Packet count, byte count per direction
- Packet size distribution (min, max, mean, std)
- Inter-arrival times (IAT)
- Flow duration
- Time-of-day features

---

### Stage 2: Intent Classification (Is the user malicious?)

**Goal**: Distinguish "benign privacy user" from "malicious actor" within same application class.

#### A. Behavioral Biometrics (Human vs. Bot Detection)

**Key Differentiators**:

1. **Header/Fingerprint Mismatches**
   - Bot claims to be "Chrome on Windows" in User-Agent
   - But TLS fingerprint reveals "Python Requests library"
   - **Result**: Definitive bot signal

2. **Session Behavior Analysis**
   - **Human**: Bursty, irregular, random navigation
   - **Bot**: Programmatic, rapid (millisecond intervals), periodic
   - Feature: Request rate, session duration, navigation entropy

3. **Client-Side JavaScript Probing** (Advanced)
   - Inject invisible JS to collect:
     - Device fingerprint (browser, OS, plugins)
     - Mouse movements, typing speed
     - Page navigation patterns
   - Unmasks headless browsers and automation tools

**Output**: `human_score` (0.0 to 1.0)

---

#### B. Threat-Specific Pattern Detection (Supervised ML)

**Use Case 1: Credential Stuffing Detection**

**Attack Signature**:
- High-volume automated login attempts
- Uses IP rotation (VPN/proxy pools) to evade blocking
- Very high failure rate

**Features**:
```python
features = {
    'endpoint': '/login',
    'request_volume': 150,  # requests per minute
    'login_failure_rate': 0.95,  # 95% failures
    'ip_change_rate': 0.8,  # Frequent IP switching
    'user_agent_diversity': 0.3,  # Low diversity (bot pool)
    'account_velocity': 50,  # Attempts on 50 different accounts
}
```

**Detection Strategy** (Araña System Approach):
- Cluster requests by IP + Time Window
- Filter benign clusters (high success rate)
- Flag clusters with: `failure_rate > 0.7 AND volume > threshold`

---

**Use Case 2: Botnet C&C Traffic Detection**

**Attack Signature**:
- Compromised machines "phone home" to Command & Control server
- Uses encrypted VPN to hide communication

**Flow-Based Features**:
```python
c2_features = {
    'periodicity': 0.92,  # High regularity (every 5 min)
    'persistence': True,  # Same destination over days
    'flow_duration': 'short',  # Quick check-ins
    'packet_sizes': 'small_fixed',  # Fixed payload sizes
    'destination_diversity': 0.1,  # Always same IP
    'port_pattern': 'non_standard',  # Not 80/443
}
```

**Training Data**: CIC-IDS-2017 dataset (has labeled "Botnet" class)

---

#### C. Unsupervised Anomaly Detection (Zero-Day Threats)

**Problem**: Supervised models only detect known attacks.

**Solution**: Graph-based anomaly detection (HyperVision approach)

**Concept**:
1. Build real-time network interaction graph
   - Nodes: IPs, ports, ASNs
   - Edges: Traffic flows
2. Apply graph learning algorithms to detect anomalous structures:
   - **Botnet**: Many-to-one pattern (many bots → one C&C)
   - **Port Scan**: One-to-many pattern (one source → many destinations)
   - **Data Exfiltration**: Unusual volume to rare destination

**Output**: `graph_anomaly_score` (0.0 to 1.0)

---

## Phase 3: Risk Scoring & Policy Engine

### 3.1 Architectural Decision: "Decrypt at Gateway" (Recommended)

**Two Options**:
- **Model A (Encrypted Analysis)**: ISP-style, analyze encrypted flows only
- **Model B (Decrypt at Gateway)**: Endpoint-style, decrypt at load balancer first

**Recommended: Model B** for application endpoints (banking websites)

**Why**:
- Traffic is already decrypted at TLS termination point (load balancer)
- Can inspect actual application data (not just statistical side-channels)
- Much lower computational overhead
- More effective against TLS 1.3 and Encrypted ClientHello (ECH)

**Architecture Flow**:
```
User Request 
→ Edge Firewall (IP check, MTU check - fast filter) 
→ Load Balancer (TLS decryption) 
→ ML Risk Engine (full feature extraction + scoring) 
→ Policy Engine (Allow/Challenge/Block decision)
```

---

### 3.2 Comprehensive Feature Vector

**The ML model takes this input vector**:

| Category | Feature | Description |
|----------|---------|-------------|
| **IP Reputation** | `ip_type` | Datacenter/Residential/Mobile |
| | `anonymizer_flag` | Is known VPN/Tor/Proxy |
| | `ip_fraud_score` | 0-100 from vendor |
| | `asn_reputation` | Network provider reputation |
| **Connection** | `mtu_value` | Detected MTU/MSS |
| **Fingerprint** | `protocol_id` | OpenVPN/WireGuard/None |
| | `fingerprint_mismatch` | User-Agent vs. TLS mismatch |
| **Application** | `app_class` | Output from Stage 1 CNN |
| **Behavioral** | `human_score` | 0-1 human-ness score |
| | `login_failure_rate` | % failed login attempts |
| | `account_velocity` | # accounts from this IP |
| | `flow_periodicity` | Connection regularity |
| | `graph_anomaly_score` | Network graph anomaly |

---

### 3.3 Risk Scoring Model

**Model Options**:
- Random Forest (interpretable, fast)
- Gradient Boosted Trees (XGBoost/LightGBM - high accuracy)
- Deep Neural Network (handles complex patterns)

**Training Strategy**:
```python
# Binary classification
y_train = ['benign', 'malicious']

# Or multi-class for granularity
y_train = ['benign', 'bot', 'credential_stuffing', 'c2', 'unknown_anomaly']
```

**Output**: Risk score 0-99

---

### 3.4 Policy Enforcement (The Segregation)

**Risk Score Tiers**:

**🟢 Score 1-20 (Low Risk - ALLOW)**
- Profile: Residential IP, known commercial VPN, normal browsing behavior
- Action: **Full access** - Treat as legitimate user
- Example: Privacy-conscious customer using NordVPN

**🟡 Score 21-60 (Medium Risk - CHALLENGE)**
- Profile: Datacenter IP, new device, accessing sensitive endpoint
- Action: **Adaptive Authentication**
  - Trigger MFA (Multi-Factor Authentication)
  - Present CAPTCHA
  - Request email verification
- Example: First-time user on datacenter VPN → Verify identity without blocking

**🔴 Score 61-99 (High Risk - BLOCK/RATE-LIMIT)**
- Profile: Datacenter IP + high login failures + bot behavior
- Action: **Block or throttle connection**
- Log for investigation
- Example: Credential stuffing bot

**Key Insight**: The Challenge tier is what enables "segregation" - malicious users fail challenges, benign users pass through.

---

## Phase 4: Dataset Strategy

### 4.1 The "No-Go-Dataset" Problem

**Challenge**: No single dataset labeled as "benign privacy VPN user" vs. "malicious VPN user"

**Solution**: Hybrid dataset creation from multiple academic sources

---

### 4.2 Dataset Inventory

**Available in Project**: `USTC-TFC2016-master/`
- 10 benign apps (BitTorrent, Facetime, Gmail, Skype, etc.)
- 10 malware types (Cridex, Geodo, Htbot, Neris, etc.)
- **Use**: Stage 2 training (malware vs. benign)

**To Download**:

| Dataset | Size | Labels | Primary Use |
|---------|------|--------|-------------|
| **ISCXVPN2016** | 28GB | VPN/Non-VPN + 7 app types | Stage 1: Application classifier |
| **VNAT (MIT)** | 36.1GB | VPN/Non-VPN + 5 apps + C2 | Stage 1: Includes C&C label! |
| **CIC-IDS-2017** | Large | Benign + Attack types (Botnet, Brute Force, DDoS) | Stage 2: Intent classifier |
| **UNSW-NB15** | Medium | Benign + 9 attack types | Stage 2: Alternative dataset |

---

### 4.3 Data Preprocessing Pipeline

**For Stage 1 (Application Classification)**:
```python
# Input: PCAP files from ISCXVPN2016, VNAT
# Process:
1. Extract flows using flow-based features or packet sequences
2. Generate Packet Block Images (64x64x3)
3. Label with application type (Browsing, Chat, VoIP, C2, etc.)
4. Train CNN classifier

# Output: Trained App_Class model
```

**For Stage 2 (Intent Classification)**:
```python
# Input: PCAP files from CIC-IDS-2017, USTC-TFC2016, UNSW-NB15
# Process:
1. Extract flows
2. Run Stage 1 model to get app_class feature
3. Extract all features from Table (IP type, MTU, behavioral metrics)
4. Create labels:
   - All "Benign" samples → Class 0
   - All "Botnet", "Brute Force", "Malware" → Class 1
5. Train Random Forest/XGBoost on full feature vector

# Output: Risk scoring model
```

**Critical Warning**: Dataset quality issues exist
- Some datasets have class overlap (same sample labeled both ways)
- Requires manual validation and cleaning phase

---

## Phase 5: Implementation Roadmap

### Sprint 1: Infrastructure Setup (Week 1-2)
- [ ] Set up Python environment (TensorFlow, Scikit-learn, Scapy)
- [ ] Download and organize datasets
- [ ] Implement PCAP parsing utilities
- [ ] Create data preprocessing pipeline

### Sprint 2: VPN Detection Layer (Week 3-4)
- [ ] Implement IP intelligence API integration
- [ ] Build MTU/MSS fingerprinting module
- [ ] Create protocol fingerprinting (OpenVPN/WireGuard)
- [ ] Test detection accuracy on ISCXVPN2016

### Sprint 3: Stage 1 - Application Classifier (Week 5-7)
- [ ] Implement Packet Block Image generation
- [ ] Build CNN architecture
- [ ] Train on ISCXVPN2016 + VNAT datasets
- [ ] Validate: Target accuracy >90% for app classification

### Sprint 4: Stage 2 - Intent Classifier (Week 8-10)
- [ ] Feature engineering: Extract all features from Table
- [ ] Implement behavioral biometrics module
- [ ] Train Random Forest/XGBoost on CIC-IDS-2017
- [ ] Test credential stuffing detection
- [ ] Test botnet C&C detection

### Sprint 5: Risk Scoring & Policy Engine (Week 11-12)
- [ ] Build unified risk scoring model
- [ ] Implement policy tiers (Allow/Challenge/Block)
- [ ] Create API for real-time scoring
- [ ] Test with live FortiAnalyzer logs (available in project)

### Sprint 6: Deployment & Optimization (Week 13-14)
- [ ] Performance optimization (latency <100ms per request)
- [ ] False positive rate analysis and tuning
- [ ] Documentation and deployment guide
- [ ] Ethical review and GDPR compliance check

---

## Critical Success Factors

### 1. False Positive Management
**Goal**: FPR < 2% (for every 100 benign VPN users, <2 incorrectly flagged)

**Strategies**:
- Use Challenge tier instead of immediate blocking
- Continuously monitor and retrain on false positives
- Whitelist known commercial VPN providers with good reputation

### 2. Future-Proofing Against Encryption
**Threat**: TLS 1.3 + Encrypted ClientHello (ECH) defeats many techniques

**Mitigations**:
- Prioritize "Decrypt at Gateway" architecture
- Focus on features ECH cannot hide: IP type, MTU, behavioral patterns
- Shift from handshake analysis to flow-based analysis

### 3. Ethical & Legal Compliance
**Considerations**:
- GDPR: IP addresses and behavioral data are personal data
- Legal basis: "Legitimate interest" for fraud prevention
- Data minimization: Only collect features needed for model
- Transparency: Document in privacy policy
- **Core Principle**: Using a VPN alone should NOT result in high risk score

### 4. Performance Requirements
**Real-time Constraints**:
- IP check: <10ms
- MTU/Protocol check: <50ms
- ML inference: <100ms
- **Total latency budget**: <200ms per request

---

## Evaluation Metrics

### Model Performance
- **Accuracy**: >92% overall
- **Precision** (Malicious class): >90% (minimize false accusations)
- **Recall** (Malicious class): >85% (catch most attacks)
- **F1-Score**: >88%
- **False Positive Rate**: <2%

### Business Metrics
- **Blocked attack attempts**: Measure over time
- **User friction**: % of benign users who see Challenge
- **Challenge pass rate**: % of challenged users who pass (should be >70%)
- **User complaints**: Track "incorrectly blocked" reports

---

## Next Steps

1. **Review this methodology** with stakeholders
2. **Set up development environment** (Sprint 1)
3. **Download datasets** and verify integrity
4. **Start with VPN detection layer** - Quickest to implement and test
5. **Iterate based on FortiAnalyzer logs** - Use real traffic data

---

## References
- Full academic references available in source document
- Key datasets: ISCXVPN2016, VNAT, CIC-IDS-2017, USTC-TFC2016, UNSW-NB15
- Key techniques: MTU fingerprinting, Packet Block Images, Araña system, HyperVision system

---

**Document Version**: 1.0  
**Last Updated**: November 9, 2025  
**Author**: ML Security Team
