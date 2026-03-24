#!/usr/bin/env python3
"""
pcap_to_packetblock.py

Convert PCAP(s) -> Packet-Block images for ML.

Usage:
    python pcap_to_packetblock.py --pcap-dir ./pcaps --out-dir ./images --img-size 64

Output:
    ./images/*.png
    ./images/manifest.csv  (columns: image_filename, src_ip, src_port, dst_ip, dst_port, protocol, start_ts, end_ts, num_packets)
"""
import os
import argparse
import csv
import math
from collections import defaultdict, namedtuple
from datetime import datetime
from tqdm import tqdm
from PIL import Image
import numpy as np

# scapy import
try:
    from scapy.utils import RawPcapReader
    from scapy.layers.inet import IP, TCP, UDP
except Exception as e:
    raise ImportError("scapy is required (pip install scapy). Error: " + str(e))

FlowKey = namedtuple("FlowKey", ["ip1", "port1", "ip2", "port2", "proto"])

def normalize(x, minv, maxv):
    if maxv <= minv:
        return 0.0
    return max(0.0, min(1.0, (x - minv) / (maxv - minv)))

def parse_pcap_packets(pcap_path):
    """
    Yield (ts, proto, src_ip, src_port, dst_ip, dst_port, pkt_len).
    Uses scapy RawPcapReader (fast streaming).
    """
    for pkt_data, pkt_meta in RawPcapReader(pcap_path):
        ts = float(pkt_meta.sec) + float(pkt_meta.usec) / 1_000_000.0
        from scapy.layers.l2 import Ether
        try:
            eth = Ether(pkt_data)
            if not eth.haslayer(IP):
                continue
            pkt = eth[IP]
        except Exception:
            # not an Ethernet/IP packet
            continue
        pkt_len = len(pkt_data)
        if pkt.haslayer(TCP):
            tp = pkt[TCP]
            proto = "TCP"
            src_port = int(tp.sport)
            dst_port = int(tp.dport)
        elif pkt.haslayer(UDP):
            tp = pkt[UDP]
            proto = "UDP"
            src_port = int(tp.sport)
            dst_port = int(tp.dport)
        else:
            # only handle TCP/UDP flows
            continue
        src_ip = pkt.src
        dst_ip = pkt.dst
        yield {
            "ts": ts,
            "proto": proto,
            "src_ip": src_ip,
            "src_port": src_port,
            "dst_ip": dst_ip,
            "dst_port": dst_port,
            "pkt_len": pkt_len
        }

def canonical_flow_key(src_ip, src_port, dst_ip, dst_port, proto):
    """
    Return a canonical flow key where ip1/port1 is the flow initiator later decided.
    For grouping, store both directions under one flow tuple (unordered key)
    """
    # use tuple ordering to create symmetric key
    a = (src_ip, src_port)
    b = (dst_ip, dst_port)
    if a <= b:
        return FlowKey(a[0], a[1], b[0], b[1], proto)
    else:
        return FlowKey(b[0], b[1], a[0], a[1], proto)

def build_flows(pcap_path, flow_timeout=60.0, max_flows=None, min_packets=3):
    """
    Build flows from pcap. Yields flow dicts:
      {
        'flow_key': FlowKey(...),
        'packets': [ {ts, src_ip, src_port, dst_ip, dst_port, pkt_len}... ],
      }
    Simple flow_timeout: if next packet for that canonical key is >flow_timeout from last, start new flow.
    """
    flows = {}  # map flow_id -> flow info
    last_ts = {}
    last_fid_map = {}
    flow_counter = 0

    for pkt in parse_pcap_packets(pcap_path):
        k = canonical_flow_key(pkt["src_ip"], pkt["src_port"], pkt["dst_ip"], pkt["dst_port"], pkt["proto"])
        last = last_ts.get(k)
        
        if last is None or (pkt["ts"] - last) > flow_timeout:
            # start new flow sequence id
            fid = (k, flow_counter)
            flows[fid] = {
                "flow_key": k,
                "packets": [],
            }
            last_fid_map[k] = fid
            flow_counter += 1
        else:
            fid = last_fid_map.get(k)
            if fid is None or fid not in flows:
                fid = (k, flow_counter)
                flows[fid] = {"flow_key": k, "packets": []}
                last_fid_map[k] = fid
                flow_counter += 1

        flows[fid]["packets"].append(pkt)
        last_ts[k] = pkt["ts"]
        
        if max_flows and len(flows) >= max_flows:
            break

    # emit flows that meet min_packets
    for fid, f in flows.items():
        if len(f["packets"]) >= min_packets:
            yield f

def packets_to_packetblock_image(flow, img_size=64, max_pkt_size=1500, max_interarrival=1.0):
    """
    Convert a flow (dict with 'flow_key' and 'packets') to an image numpy array (H,W,3) uint8.
    Encoding:
      - Each packet -> pixel index i (sequential)
      - R channel: c2s packet size normalized * 255 (client->server)
      - G channel: s2c packet size normalized * 255 (server->client)
      - B channel: inter-arrival time normalized * 255 (delta from previous packet)
    client = flow initiator = first packet's src_ip/src_port
    If multiple packets map to same pixel index, average values.
    """
    packets = flow["packets"]
    width = img_size
    height = img_size
    max_pixels = width * height
    # Determine client (initiator)
    first = packets[0]
    client_tuple = (first["src_ip"], first["src_port"])
    # Prepare accumulation arrays
    acc = np.zeros((height, width, 3), dtype=np.float32)
    counts = np.zeros((height, width, 1), dtype=np.int32)

    prev_ts = None
    for idx, pkt in enumerate(packets[:max_pixels]):
        row = idx // width
        col = idx % width
        # direction
        is_c2s = (pkt["src_ip"], pkt["src_port"]) == client_tuple
        size_norm = min(pkt["pkt_len"], max_pkt_size) / float(max_pkt_size)
        if prev_ts is None:
            delta = 0.0
        else:
            delta = pkt["ts"] - prev_ts
        delta_norm = min(delta, max_interarrival) / float(max_interarrival)
        r = size_norm * 255.0 if is_c2s else 0.0
        g = size_norm * 255.0 if (not is_c2s) else 0.0
        b = delta_norm * 255.0
        acc[row, col, 0] += r
        acc[row, col, 1] += g
        acc[row, col, 2] += b
        counts[row, col, 0] += 1
        prev_ts = pkt["ts"]

    # average
    mask = counts[:, :, 0] > 0
    img = np.zeros((height, width, 3), dtype=np.uint8)
    if mask.any():
        # avoid division by zero
        counts_safe = counts.copy()
        counts_safe[counts_safe == 0] = 1
        avg = acc / counts_safe
        img = np.clip(avg, 0, 255).astype(np.uint8)
    return img

def save_image(img_np, out_path):
    img = Image.fromarray(img_np)
    img.save(out_path, format="PNG")

def process_pcap_to_images(pcap_path, out_dir, img_size=64, max_packets=None, flow_timeout=60.0, max_pkt_size=1500, max_interarrival=1.0, min_packets=3):
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    cnt = 0
    for flow in tqdm(build_flows(pcap_path, flow_timeout=flow_timeout, min_packets=min_packets), desc=f"Flows in {os.path.basename(pcap_path)}"):
        img_np = packets_to_packetblock_image(flow, img_size=img_size, max_pkt_size=max_pkt_size, max_interarrival=max_interarrival)
        # skip flows that are all zeros (very small)
        if img_np.sum() == 0:
            continue
        fk = flow["flow_key"]
        start_ts = flow["packets"][0]["ts"]
        end_ts = flow["packets"][-1]["ts"]
        num_packets = len(flow["packets"])
        fname = f"flow_{os.path.basename(pcap_path)}_{cnt:07d}.png"
        out_path = os.path.join(out_dir, fname)
        save_image(img_np, out_path)
        manifest.append({
            "image_filename": fname,
            "src_ip": fk.ip1,
            "src_port": fk.port1,
            "dst_ip": fk.ip2,
            "dst_port": fk.port2,
            "protocol": fk.proto,
            "start_ts": datetime.utcfromtimestamp(start_ts).isoformat() + "Z",
            "end_ts": datetime.utcfromtimestamp(end_ts).isoformat() + "Z",
            "num_packets": num_packets
        })
        cnt += 1
    # write manifest CSV
    manifest_path = os.path.join(out_dir, "manifest.csv")
    if manifest:
        with open(manifest_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
            writer.writeheader()
            for row in manifest:
                writer.writerow(row)
    return manifest_path, cnt

def main():
    parser = argparse.ArgumentParser(description="PCAP -> PacketBlock images ETL")
    parser.add_argument("--pcap-dir", required=True, help="Directory containing input .pcap / .pcapng files")
    parser.add_argument("--out-dir", required=True, help="Output directory for images and manifest")
    parser.add_argument("--img-size", type=int, default=64, help="Image width/height (default 64)")
    parser.add_argument("--flow-timeout", type=float, default=60.0, help="Flow timeout in seconds to split flows (default 60s)")
    parser.add_argument("--min-packets", type=int, default=3, help="Minimum packets in flow to produce image")
    parser.add_argument("--max-packets-per-flow", type=int, default=None, help="Max packets to consider per flow (default img_size^2)")
    parser.add_argument("--max-pkt-size", type=int, default=1500, help="Max packet size used for normalization")
    parser.add_argument("--max-interarrival", type=float, default=1.0, help="Inter-arrival time (s) to cap for normalization")
    args = parser.parse_args()

    pcap_files = [os.path.join(args.pcap_dir, f) for f in os.listdir(args.pcap_dir) if f.lower().endswith((".pcap", ".pcapng"))]
    if not pcap_files:
        print("No pcap files found in", args.pcap_dir)
        return

    total_images = 0
    for pcap in pcap_files:
        print("Processing:", pcap)
        manifest_path, produced = process_pcap_to_images(
            pcap,
            args.out_dir,
            img_size=args.img_size,
            max_packets=args.max_packets_per_flow,
            flow_timeout=args.flow_timeout,
            max_pkt_size=args.max_pkt_size,
            max_interarrival=args.max_interarrival,
            min_packets=args.min_packets
        )
        print(f"Produced {produced} images from {os.path.basename(pcap)}; manifest at {manifest_path}")
        total_images += produced
    print("Done. Total images:", total_images)

if __name__ == "__main__":
    main()
