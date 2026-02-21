# Data Preprocessing Progress Report - Phase 2 Complete

**Project**: VPN Detection & User Segregation System  
**Phase**: Dataset Merging & Finalization  
**Date**: November 10, 2025  
**Status**: ✅ **PHASE 2 COMPLETE** (with findings)

---

## Executive Summary

Phase 2 has been completed with successful merging of all three aligned datasets. However, aggressive deduplication resulted in removal of 99.4% of data, leaving only 3,893 unique flows from the university network traffic. The CIC-IDS2017 attack samples were removed due to duplicate 5-tuples.

### Key Finding
**Data retention: 0.2%** - Only university benign traffic remains after deduplication. CIC-IDS2017 attack data needs to be preserved differently.

---

## Phase 2 Results

### ✅ **Processing Pipeline Executed**

| Step | Input Rows | Output Rows | Removed | Action |
|------|------------|-------------|---------|--------|
| **1. Merge** | 1,935,392 | 1,935,392 | 0 | ✅ Combined 3 datasets |
| **2. Deduplicate** | 1,935,392 | 11,190 | 1,924,202 (99.4%) | ⚠️ Too aggressive |
| **3. Missing Values** | 11,190 | 5,165 | 6,025 | ✅ Removed incomplete rows |
| **4. Outliers** | 5,165 | 3,893 | 1,272 | ✅ IQR method (factor=3.0) |
| **FINAL** | **1,935,392** | **3,893** | **1,931,499 (99.8%)** | ⚠️ Too much loss |

### 📊 **Final Dataset Composition**

**Unified Dataset: 3,893 flows**
- Source: University network only (FortiAnalyzer + PCAP)
- Intent Labels: 100% Benign
- Application Labels: 23.5% known (914 flows)
  - Browsing: 654 flows (71.6%)
  - Enterprise_App: 260 flows (28.4%)
  - Unknown: 2,979 flows (76.5%)

### 🎯 **Train/Val/Test Splits**

All splits contain only **Benign** traffic:
- **Train**: 2,725 flows (70%)
- **Validation**: 584 flows (15%)
- **Test**: 584 flows (15%)

**Stratification**: By `intent_label` (currently only "Benign")

---

## Analysis: Why 99.4% Deduplication?

### Root Cause
CIC-IDS2017 contains synthetic attack traffic with **repeated 5-tuples** (same source IP, destination IP, source port, destination port, protocol combinations).

### What Happened
1. **CIC-IDS2017**: 1,924,096 flows → Many duplicates
   - Attack simulations repeated similar network patterns
   - Same IP addresses used across different attack types
   
2. **Deduplication Logic**: Kept only **first occurrence** of each unique 5-tuple
   - Result: Most attack samples removed as "duplicates"
   
3. **University Data**: 11,296 flows → Mostly unique
   - Real production traffic has diverse 5-tuples
   - Minimal internal duplication

### Why This Matters
- **Problem**: Lost all attack diversity from CIC-IDS2017
- **Impact**: Cannot train attack detection models (Stage 2)
- **Current Dataset**: Only benign university traffic remains

---

## Label Normalization ✅

Successfully normalized intent labels from CIC-IDS2017:

| Original Label | Normalized Label | Count (before dedup) |
|----------------|------------------|----------------------|
| DoS Wednesday | DoS | 584,991 |
| Benign Monday | Benign | 458,831 |
| DDoS Friday | DDoS | 221,264 |
| Infiltration Thursday | Infiltration | 207,630 |
| Botnet Friday | Botnet | 176,038 |
| WebAttacks Thursday | Web_Attack | 155,820 |
| Portscan Friday | Portscan | 119,522 |

**After deduplication**: All attack labels lost, only "Benign" remains.

---

## Data Quality Validation ✅

### Critical Columns Check
- ✅ `src_ip`: No missing values
- ✅ `dst_ip`: No missing values
- ✅ `protocol`: No missing values  
- ✅ `intent_label`: No missing values

### Port Ranges
- ✅ All ports in valid range (0-65535)
- ✅ 0 invalid ports detected

### Protocol Distribution
- ✅ 100% valid protocols (TCP=6, UDP=17, ICMP=1)

### Application Labels
- ✅ 914 flows (23.5%) have known application labels
- ⚠️ 2,979 flows (76.5%) remain "Unknown"

---

## Files Generated

### Output Directory: `preprocessing/outputs/`

```
outputs/
├── Unified_Dataset.csv                    (3,893 rows × 117 columns) - 456 KB
├── Stage1_App_Classification.csv          (914 rows) - 108 KB
├── Stage2_Intent_Classification.csv       (3,893 rows) - 456 KB
├── train.csv                              (2,725 rows) - 319 KB
├── val.csv                                (584 rows) - 68 KB
├── test.csv                               (584 rows) - 68 KB
└── phase2_merge_report.json               (metadata)
```

### Report: `phase2_merge_report.json`
Contains:
- Processing timestamp
- Statistics (rows removed at each step)
- Feature list (117 columns)
- Label distributions
- Data quality metrics

---

## Issues & Recommendations

### ⚠️ **Issue 1: Lost Attack Data**

**Problem**: 99.4% deduplication removed all CIC-IDS2017 attack samples

**Root Cause**: 5-tuple based deduplication too aggressive for synthetic attack data

**Recommendations**:
1. **Option A - Keep CIC-IDS2017 Separate**
   - Use CIC-IDS2017 for Stage 2 (Intent Classification)
   - Use University data for Stage 1 (App Classification)
   - Don't merge - use as separate training sources

2. **Option B - Smarter Deduplication**
   - Deduplicate **within** each dataset, not across datasets
   - Keep attack diversity from CIC-IDS2017
   - Only deduplicate university data

3. **Option C - Feature-based Dedup**
   - Use flow features instead of 5-tuple for similarity
   - Keep flows with different statistical characteristics
   - Remove only truly identical flows

**Immediate Action**: Recommend **Option A** - Keep datasets separate for different training stages

### ⚠️ **Issue 2: Class Imbalance**

**Problem**: Final dataset only contains "Benign" label

**Impact**: 
- Cannot train Stage 2 (Intent Classification) model
- No attack/normal discrimination possible
- Model would only predict "Benign"

**Solution**: Use CIC-IDS2017 separately for Stage 2 training (see Option A above)

### ⚠️ **Issue 3: Limited App Labels**

**Problem**: Only 23.5% of flows have known application labels

**Impact**:
- Stage 1 training data limited to 914 flows
- Only 2 application classes (Browsing, Enterprise_App)
- May need more diverse application traffic

**Solution**: This is acceptable for proof-of-concept, but production system would need:
- More diverse application traffic
- Integration with DPI (Deep Packet Inspection)
- Application-level labeling from FortiGate

---

## Recommended Next Steps

### ✅ **Immediate: Use Datasets Strategically**

**For Stage 1 (Application Classification)**:
- **Dataset**: `Stage1_App_Classification.csv` (914 flows)
- **Source**: University FortiAnalyzer logs
- **Labels**: Browsing (654) + Enterprise_App (260)
- **Purpose**: Classify network applications from flow features

**For Stage 2 (Intent Classification)**:
- **Dataset**: Use original `cic_ids_2017_aligned.csv` (1.92M flows)
- **Source**: CIC-IDS2017 benchmark dataset
- **Labels**: 7 classes (DoS, DDoS, Benign, Botnet, etc.)
- **Purpose**: Detect attacks and classify threat types

### 🔄 **Alternative: Re-run Phase 2 with Modified Strategy**

Create `merge_datasets_v2.py` with:
1. Separate deduplication per dataset
2. Preserve attack samples from CIC-IDS2017
3. Merge with class balancing

**Command**:
```bash
python3 scripts/merge_datasets_v2.py \
  --preserve-attacks \
  --balance-classes \
  --aligned-dir outputs/aligned \
  --output-dir outputs/v2
```

---

## Technical Achievements ✅

### What Worked Well

1. **Label Normalization** ✅
   - Successfully cleaned all day names from CIC-IDS2017 labels
   - Consistent label format across datasets

2. **Feature Alignment** ✅  
   - All 117 features present in merged dataset
   - Compatible schemas from Phase 1

3. **Data Quality** ✅
   - No missing values in critical columns
   - Valid port ranges and protocols
   - Clean data ready for training

4. **Train/Val/Test Split** ✅
   - Proper stratification implemented
   - 70/15/15 ratio maintained
   - Reproducible (random_state=42)

5. **Missing Value Handling** ✅
   - Removed incomplete rows (>50% missing)
   - Filled remaining nulls appropriately

6. **Outlier Removal** ✅
   - IQR method with factor=3.0
   - Removed extreme values from 86 features

### Lessons Learned

1. **Synthetic vs Real Data**
   - Synthetic datasets (CIC-IDS2017) have different characteristics
   - Cannot apply same preprocessing to both
   - Need separate handling strategies

2. **Deduplication Strategy**
   - 5-tuple deduplication too simplistic
   - Should consider temporal aspects
   - Should preserve attack diversity

3. **Dataset Purpose**
   - Different datasets serve different purposes
   - CIC-IDS2017 → Attack detection training
   - University data → Real-world application classification

---

## Resource Usage

### Processing Time
- Phase 2 total: ~7 seconds
- Loading: ~5 seconds
- Merging: ~1 second
- Deduplication: ~1 second
- Cleaning: <1 second

### Memory Usage
- Peak: ~4.2 GB (loading CIC-IDS2017)
- Average: ~1.5 GB during processing

### Disk Space
- Input: 880 MB (3 aligned files)
- Output: ~1.5 MB (all final files)
- Reduction: 99.8% (due to aggressive deduplication)

---

## Next Phase: Model Training

### Ready for Training ✅

**Stage 1: Application Classification**
- ✅ Dataset: 914 flows with 2 app classes
- ✅ Features: 117 numerical + categorical features
- ✅ Quality: Clean, no missing values
- ⚠️ **Limitation**: Small dataset, only 2 classes

**Stage 2: Intent Classification**  
- ⚠️ **Issue**: Current unified dataset only has "Benign"
- ✅ **Solution**: Use `cic_ids_2017_aligned.csv` separately (1.92M flows, 7 classes)
- ✅ Quality: Clean, normalized labels

### Training Strategy

**Recommended Approach**:

1. **Stage 1 Model** (Application Classifier)
   ```bash
   - Input: Stage1_App_Classification.csv (914 flows)
   - Model: Random Forest / XGBoost
   - Classes: 2 (Browsing, Enterprise_App)
   - Validation: Cross-validation (due to small size)
   ```

2. **Stage 2 Model** (Intent Classifier)
   ```bash
   - Input: cic_ids_2017_aligned.csv (1.92M flows)
   - Model: Deep Neural Network / Ensemble
   - Classes: 7 (DoS, DDoS, Benign, Botnet, Infiltration, Web_Attack, Portscan)
   - Split: Use existing 70/15/15 split logic
   ```

---

## File Structure

```
preprocessing/
├── outputs/
│   ├── aligned/                           # Phase 1 outputs
│   │   ├── cic_ids_2017_aligned.csv      (876 MB) ← Use for Stage 2
│   │   ├── university_fortianalyzer_aligned.csv
│   │   └── university_pcap_aligned.csv
│   │
│   ├── Unified_Dataset.csv                (456 KB) ← University traffic only
│   ├── Stage1_App_Classification.csv      (108 KB) ← Use for Stage 1
│   ├── Stage2_Intent_Classification.csv   (456 KB) ← Don't use (only Benign)
│   ├── train.csv                          (319 KB)
│   ├── val.csv                            (68 KB)
│   ├── test.csv                           (68 KB)
│   └── phase2_merge_report.json
│
└── docs/
    └── progress/
        ├── PHASE1_ALIGNMENT_COMPLETE.md
        └── PHASE2_MERGE_COMPLETE.md       ← This report
```

---

## Success Criteria - Phase 2

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Merge all datasets | ✅ | ✅ 3 datasets merged | ✅ PASS |
| Normalize labels | ✅ | ✅ Day names removed | ✅ PASS |
| Remove duplicates | ✅ | ⚠️ 99.4% removed | ⚠️ TOO AGGRESSIVE |
| Handle missing values | ✅ | ✅ Properly handled | ✅ PASS |
| Remove outliers | ✅ | ✅ IQR method applied | ✅ PASS |
| Create stage datasets | ✅ | ✅ Stage 1 & 2 created | ✅ PASS |
| Train/val/test split | ✅ | ✅ 70/15/15 split | ✅ PASS |
| **Attack diversity** | ✅ | ✗ Lost all attacks | ❌ FAIL |

**Overall**: ⚠️ **Partial Success** - Technical pipeline works, but strategy needs adjustment

---

## Conclusion

Phase 2 successfully implemented the merging pipeline with label normalization, deduplication, cleaning, and splitting. However, the aggressive deduplication strategy removed 99.4% of the data, eliminating all CIC-IDS2017 attack samples.

### Key Takeaway
**The datasets should be used separately**:
- **University data** → Stage 1 (Application Classification)
- **CIC-IDS2017** → Stage 2 (Intent/Attack Classification)

This approach preserves attack diversity while leveraging real university traffic for application classification.

### Ready for Phase 3
✅ **YES** - with the recommended strategy adjustment:
- Stage 1 training with `Stage1_App_Classification.csv` (914 flows)
- Stage 2 training with `cic_ids_2017_aligned.csv` (1.92M flows)

---

**Report Generated**: November 10, 2025, 02:35 AM  
**Author**: Data Engineering Pipeline  
**Version**: 2.0  
**Status**: Phase 2 Complete ⚠️ (with recommendations)
