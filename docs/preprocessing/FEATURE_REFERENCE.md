# Feature Engineering Reference

## Overview
This document describes all features extracted from network traffic for VPN detection and user segregation.

---

## Feature Categories

### 1. Connection Identifiers (6 features)
Basic flow identification features.

| Feature | Type | Description | Example |
|---------|------|-------------|---------|
| `flow_id` | String | Unique flow identifier | `192.168.1.1:443-8.8.8.8:80-TCP` |
| `src_ip` | IP | Source IP address | `192.168.1.100` |
| `dst_ip` | IP | Destination IP address | `8.8.8.8` |
| `src_port` | Integer | Source port | `54321` |
| `dst_port` | Integer | Destination port | `443` |
| `protocol` | Integer | Protocol number (6=TCP, 17=UDP) | `6` |

---

### 2. Flow Statistics (20 features)
Aggregate statistics about the flow.

| Feature | Type | Range | Description |
|---------|------|-------|-------------|
| `packet_count_fwd` | Integer | 0-∞ | Forward direction packet count |
| `packet_count_bwd` | Integer | 0-∞ | Backward direction packet count |
| `packet_count_total` | Integer | 0-∞ | Total packets in flow |
| `byte_count_fwd` | Integer | 0-∞ | Forward direction bytes |
| `byte_count_bwd` | Integer | 0-∞ | Backward direction bytes |
| `byte_count_total` | Integer | 0-∞ | Total bytes in flow |
| `flow_duration` | Float | 0-∞ | Flow duration in seconds |
| `packets_per_second` | Float | 0-∞ | Packet rate |
| `bytes_per_second` | Float | 0-∞ | Byte rate |
| `byte_ratio` | Float | 0-∞ | Upload/download byte ratio |
| `packet_ratio` | Float | 0-∞ | Forward/backward packet ratio |
| `active_mean` | Float | 0-∞ | Mean active time |
| `active_std` | Float | 0-∞ | Std dev of active time |
| `idle_mean` | Float | 0-∞ | Mean idle time |
| `idle_std` | Float | 0-∞ | Std dev of idle time |
| `down_up_ratio` | Float | 0-∞ | Download/upload ratio |
| `fwd_bulk_rate` | Float | 0-∞ | Forward bulk transfer rate |
| `bwd_bulk_rate` | Float | 0-∞ | Backward bulk transfer rate |
| `packet_length_variance` | Float | 0-∞ | Variance in packet sizes |
| `packet_length_cv` | Float | 0-∞ | Coefficient of variation |

**Key Indicators**:
- High `byte_ratio` → Asymmetric traffic (e.g., video streaming)
- High `packets_per_second` → Real-time application (e.g., VoIP)
- Low `flow_duration` → Short-lived connection

---

### 3. Packet Size Features (10 features)
Statistical analysis of packet sizes.

| Feature | Type | Description | VPN Indicator |
|---------|------|-------------|---------------|
| `packet_length_min` | Integer | Minimum packet size | VPN adds overhead |
| `packet_length_max` | Integer | Maximum packet size | Often capped at MTU |
| `packet_length_mean` | Float | Average packet size | VPN: ~1400-1450 bytes |
| `packet_length_std` | Float | Std dev of packet size | VPN: Lower variance |
| `packet_length_q1` | Float | 1st quartile | Distribution analysis |
| `packet_length_q2` | Float | Median | Central tendency |
| `packet_length_q3` | Float | 3rd quartile | Distribution analysis |

**VPN Detection**:
- VPN traffic often shows MTU reduction (1400-1450 vs 1500)
- More consistent packet sizes (lower std dev)
- Encryption padding creates patterns

---

### 4. Timing Features (15 features)
Inter-arrival time and temporal patterns.

| Feature | Type | Description | Application Type |
|---------|------|-------------|------------------|
| `mean_iat_fwd` | Float | Mean IAT forward | Regular = Streaming |
| `mean_iat_bwd` | Float | Mean IAT backward | Irregular = Interactive |
| `std_iat_fwd` | Float | Std dev IAT forward | Low = Periodic |
| `std_iat_bwd` | Float | Std dev IAT backward | High = Bursty |
| `min_iat_fwd` | Float | Minimum IAT forward | Real-time apps |
| `max_iat_fwd` | Float | Maximum IAT forward | Idle periods |
| `iat_total` | Float | Total IAT | Flow regularity |
| `flow_iat_mean` | Float | Mean flow IAT | Traffic pattern |
| `flow_iat_std` | Float | Std dev flow IAT | Burstiness |
| `rtt_mean` | Float | Mean round-trip time | Network latency |
| `rtt_std` | Float | Std dev RTT | Jitter |
| `jitter` | Float | IAT variance | VoIP quality indicator |
| `periodicity_score` | Float | Regularity metric | 0=irregular, high=periodic |
| `burst_rate` | Float | Burst intensity | Peak traffic rate |
| `inter_burst_time` | Float | Time between bursts | Traffic pattern |

**Application Signatures**:
- **VoIP**: Low jitter, high periodicity
- **Video Streaming**: Regular IAT, moderate periodicity
- **Web Browsing**: Irregular IAT, bursty
- **File Transfer**: Continuous, minimal gaps

---

### 5. TCP Features (12 features)
TCP-specific flags and behavior.

| Feature | Type | Description | Behavioral Indicator |
|---------|------|-------------|---------------------|
| `fwd_syn_packets` | Integer | Forward SYN count | Connection attempts |
| `bwd_syn_packets` | Integer | Backward SYN count | Server responses |
| `fwd_ack_packets` | Integer | Forward ACK count | Acknowledgments |
| `fwd_fin_packets` | Integer | Forward FIN count | Graceful close |
| `fwd_rst_packets` | Integer | Forward RST count | Abrupt close/failure |
| `fwd_psh_packets` | Integer | Forward PSH count | Data push |
| `connection_rate` | Float | SYN per second | Scanning indicator |
| `failed_connections` | Integer | RST packet count | Failed attempts |
| `syn_ack_delay` | Float | Handshake delay | Network latency |

**Malicious Indicators**:
- High `connection_rate` → Port scanning
- Many `failed_connections` → Brute force
- Abnormal flag combinations → Attack traffic

---

### 6. VPN Detection Features (10 features)
Specific indicators of VPN usage.

| Feature | Type | Range | Description |
|---------|------|-------|-------------|
| `mss` | Integer | 0-1460 | TCP Maximum Segment Size |
| `mtu` | Integer | 0-1500 | Maximum Transmission Unit |
| `ttl` | Integer | 0-255 | Time To Live |
| `window_size` | Integer | 0-65535 | TCP window size |
| `tcp_options_count` | Integer | 0-10 | Number of TCP options |
| `protocol_hint` | Binary | 0/1 | VPN port detected |
| `encryption_detected` | Binary | 0/1 | High entropy payload |
| `entropy_score` | Float | 0-8 | Shannon entropy (>7.5 = encrypted) |
| `tls_version` | String | - | TLS version if detected |
| `cipher_suite` | String | - | Encryption cipher |

**VPN Signatures**:
- **OpenVPN**: Port 1194, high entropy
- **WireGuard**: Port 51820, UDP
- **IPSec**: Ports 500/4500
- **PPTP**: Port 1723

**Detection Logic**:
```python
if entropy_score > 7.5 and (dst_port in [1194, 1723, 500, 4500, 51820]):
    vpn_probability = HIGH
elif mss < 1400 and encryption_detected:
    vpn_probability = MEDIUM
```

---

### 7. IP Intelligence Features (8 features)
External reputation and geolocation data (optional, requires API).

| Feature | Type | Description | Data Source |
|---------|------|-------------|-------------|
| `fraud_score` | Integer | 0-100 | IP reputation score |
| `vpn_probability` | Float | 0-1 | VPN likelihood |
| `proxy_score` | Float | 0-1 | Proxy likelihood |
| `ip_type` | String | - | Residential/Datacenter/Mobile |
| `asn` | Integer | - | Autonomous System Number |
| `asn_reputation` | String | - | ASN reputation (clean/suspicious) |
| `geolocation_risk` | Float | 0-1 | Geo-anomaly score |
| `datacenter_flag` | Binary | 0/1 | Datacenter IP indicator |

**Integration** (IPQualityScore API):
```python
response = requests.get(f"https://ipqualityscore.com/api/json/ip/YOUR_KEY/{ip}")
fraud_score = response.json()['fraud_score']
vpn_probability = response.json()['vpn']
```

---

### 8. Behavioral Features (12 features)
User/session behavior analysis.

| Feature | Type | Description | Malicious Indicator |
|---------|------|-------------|---------------------|
| `login_failure_rate` | Float | Failed logins / total | High = Brute force |
| `account_velocity` | Float | Actions per minute | High = Bot |
| `session_duration` | Float | Session length (seconds) | Abnormal = Suspicious |
| `request_frequency` | Float | Requests per second | Very high = Attack |
| `connection_establishment_rate` | Float | New connections/sec | High = Scanning |
| `human_score` | Float | 0-1 | Behavioral biometrics |
| `bot_probability` | Float | 0-1 | Bot detection score |
| `anomaly_score` | Float | 0-1 | Statistical anomaly |
| `reputation_change` | Float | -1 to +1 | Reputation delta |
| `time_of_day_score` | Float | 0-1 | Temporal anomaly |

**Bot Detection**:
- `human_score` < 0.3 → Likely bot
- `account_velocity` > threshold → Automated
- Perfect regularity → Scripted behavior

---

### 9. Labels (3 features)
Ground truth and classifications.

| Feature | Type | Values | Purpose |
|---------|------|--------|---------|
| `app_label` | String | Browsing, Chat, VoIP, Video_Streaming, File_Transfer, Email, P2P, Gaming, C2_Communication | Stage-1 classification |
| `intent_label` | String | Benign, Botnet, BruteForce, DDoS, DoS, Portscan, Infiltration, Web_Attack, Credential_Stuffing, C2_Communication, Malware | Stage-2 classification |
| `vpn_flag` | Binary | 0/1 | VPN usage indicator |

---

## Feature Importance by Stage

### Stage-1: Application Classification
**Top 10 Features**:
1. `packets_per_second` - Application behavior
2. `mean_iat_total` - Traffic regularity
3. `packet_length_mean` - Protocol characteristics
4. `byte_ratio` - Upload/download pattern
5. `periodicity_score` - Traffic pattern
6. `flow_duration` - Session length
7. `jitter` - Real-time requirements
8. `dst_port` - Well-known ports
9. `bytes_per_second` - Bandwidth usage
10. `packet_length_std` - Size consistency

### Stage-2: Intent Classification
**Top 10 Features**:
1. `connection_rate` - Scanning indicator
2. `failed_connections` - Attack attempts
3. `fraud_score` - IP reputation
4. `bot_probability` - Automation detection
5. `entropy_score` - Encryption/obfuscation
6. `login_failure_rate` - Credential attacks
7. `request_frequency` - DDoS indicator
8. `anomaly_score` - Statistical outlier
9. `syn_ack_delay` - Network behavior
10. `vpn_flag` - Obfuscation attempt

---

## Feature Engineering Best Practices

### 1. Normalization
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_normalized = scaler.fit_transform(X)
```

### 2. Feature Selection
```python
from sklearn.feature_selection import SelectKBest, f_classif

selector = SelectKBest(f_classif, k=50)
X_selected = selector.fit_transform(X, y)
```

### 3. Handle Missing Values
```python
# Numerical: Fill with 0 or median
df[numeric_cols] = df[numeric_cols].fillna(0)

# Categorical: Fill with 'Unknown'
df[categorical_cols] = df[categorical_cols].fillna('Unknown')
```

### 4. Outlier Removal
```python
# IQR method
Q1 = df.quantile(0.25)
Q3 = df.quantile(0.75)
IQR = Q3 - Q1
df = df[~((df < (Q1 - 3 * IQR)) | (df > (Q3 + 3 * IQR))).any(axis=1)]
```

---

## References
- NFStream: https://www.nfstream.org/
- CIC Flow Meter: https://www.unb.ca/cic/research/applications.html
- IANA Port Numbers: https://www.iana.org/assignments/service-names-port-numbers/

---

**Last Updated**: November 9, 2025
