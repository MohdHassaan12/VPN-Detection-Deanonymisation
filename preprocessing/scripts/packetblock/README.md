# Packet-Block Image Generation for VPN Detection

This directory contains scripts for converting PCAP files into Packet-Block images suitable for CNN training.

## Overview

**Packet-Block images** encode network traffic flows as 64×64×3 RGB images where:
- **R channel**: Client→Server packet sizes (normalized 0-255)
- **G channel**: Server→Client packet sizes (normalized 0-255)
- **B channel**: Inter-arrival times (normalized 0-255)
- Each packet maps to one pixel sequentially

## Usage

### Basic Usage

```bash
python pcap_to_packetblock.py \
  --pcap-dir /path/to/pcaps/ \
  --out-dir ./output_images/ \
  --img-size 64
```

### Advanced Options

```bash
python pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/Benign/ \
  --out-dir ./outputs/benign_images/ \
  --img-size 64 \
  --flow-timeout 60.0 \
  --min-packets 3 \
  --max-pkt-size 1500 \
  --max-interarrival 1.0
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--pcap-dir` | Required | Directory containing .pcap/.pcapng files |
| `--out-dir` | Required | Output directory for images |
| `--img-size` | 64 | Image dimensions (width = height) |
| `--flow-timeout` | 60.0 | Flow idle timeout in seconds |
| `--min-packets` | 3 | Minimum packets required per flow |
| `--max-pkt-size` | 1500 | Max packet size for normalization |
| `--max-interarrival` | 1.0 | Max IAT for normalization (seconds) |

## Output Structure

```
output_images/
├── flow_capture1.pcap_0000000.png
├── flow_capture1.pcap_0000001.png
├── ...
└── manifest.csv
```

### Manifest CSV Format

```csv
image_filename,src_ip,src_port,dst_ip,dst_port,protocol,start_ts,end_ts,num_packets
flow_capture1.pcap_0000000.png,192.168.1.100,51234,8.8.8.8,443,TCP,2025-11-09T10:30:15Z,2025-11-09T10:32:45Z,245
```

## Example: Processing USTC-TFC2016 Dataset

```bash
# Process benign traffic
python pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/Benign/ \
  --out-dir ./outputs/ustc_benign/ \
  --img-size 64

# Process malware traffic
python pcap_to_packetblock.py \
  --pcap-dir ../USTC-TFC2016-master/Malware/ \
  --out-dir ./outputs/ustc_malware/ \
  --img-size 64

# Results
# Benign: ~500 images (BitTorrent, FTP, Gmail, etc.)
# Malware: ~300 images (Cridex, Zeus, Miuref, etc.)
```

## Requirements

```bash
pip install scapy pillow tqdm numpy pandas
```

### Platform-specific Notes

**macOS**: Install libpcap if needed
```bash
brew install libpcap
```

**Linux**: Install libpcap-dev
```bash
sudo apt-get install libpcap-dev
```

## Performance

- **Processing speed**: ~1000 flows/minute
- **Memory usage**: ~500MB for 10K flows
- **Output size**: ~10KB per image (PNG)

For large datasets (>100K flows), consider:
1. Processing in batches
2. Using parallel processing (GNU parallel)
3. Streaming mode (future feature)

## Troubleshooting

### "No module named 'scapy'"
```bash
pip install scapy
```

### "Permission denied" on PCAP files
```bash
sudo chown $USER:$USER /path/to/pcaps/*.pcap
```

### Out of memory errors
Reduce batch size or process files individually:
```bash
for pcap in *.pcap; do
  python pcap_to_packetblock.py --pcap-dir . --out-dir ./output/ --pattern "$pcap"
done
```

## Integration with Training Pipeline

After generating images, use them for CNN training:

```bash
# 1. Generate images
python pcap_to_packetblock.py --pcap-dir ./pcaps --out-dir ./images

# 2. Train Stage-1 model
cd ../../model_training/stage1_app_classifier
python train_cnn.py --image-dir ../../preprocessing/outputs/images --epochs 50

# 3. Evaluate
python evaluate.py --model-dir ../../inference/models/stage1
```

## References

- **Original concept**: PacketPrint (IEEE S&P 2020)
- **Similar approaches**: FlowPic (NDSS 2020), TrafficVision (IMC 2018)

---

**See also**: `preprocessing/README.md` for full pipeline documentation
