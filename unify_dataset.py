#!/usr/bin/env python3
"""
Unified dataset builder.
Loads heterogeneous network traffic data (CSV, JSON, PCAP, flow text) and normalizes
into a single tabular CSV for model training/testing.

Output: unified_dataset.csv

Dependencies (optional based on available formats):
  pip install pandas scapy tqdm python-dateutil
"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict, Any

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None

try:
    from scapy.all import PcapReader  # type: ignore
    from scapy.layers.inet import IP, TCP, UDP
except ImportError:
    PcapReader = None

from dateutil import parser as dateparser  # type: ignore
from tqdm import tqdm  # type: ignore

UNIFIED_COLUMNS = [
    'timestamp',        # ISO8601 string
    'src_ip',
    'dst_ip',
    'src_port',
    'dst_port',
    'protocol',
    'packet_len',
    'direction',       # optional (client->server etc.)
    'label',           # target label if available
    'source_type',     # file modality origin
    'additional_meta'  # JSON string for extra fields
]

def safe_iso(ts) -> str:
    if ts is None:
        return ''
    if isinstance(ts, (int, float)):
        return datetime.utcfromtimestamp(ts).isoformat()
    if isinstance(ts, str):
        try:
            return dateparser.parse(ts).isoformat()
        except Exception:
            return ts
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts)

def normalize_record(rec: Dict[str, Any], source_type: str) -> Dict[str, Any]:
    out = {c: '' for c in UNIFIED_COLUMNS}
    # Map common fields heuristically
    out['timestamp'] = safe_iso(rec.get('timestamp') or rec.get('time') or rec.get('ts'))
    out['src_ip'] = rec.get('src_ip') or rec.get('source_ip') or rec.get('src')
    out['dst_ip'] = rec.get('dst_ip') or rec.get('destination_ip') or rec.get('dst')
    out['src_port'] = rec.get('src_port') or rec.get('sport') or rec.get('srcport')
    out['dst_port'] = rec.get('dst_port') or rec.get('dport') or rec.get('dst_port') or rec.get('dstport')
    out['protocol'] = rec.get('protocol') or rec.get('proto') or rec.get('layer')
    out['packet_len'] = rec.get('packet_len') or rec.get('length') or rec.get('pkt_len') or rec.get('size')
    out['direction'] = rec.get('direction') or ''
    out['label'] = rec.get('label') or rec.get('class') or rec.get('target') or ''
    out['source_type'] = source_type
    # Additional meta: everything else not mapped
    meta = {k: v for k, v in rec.items() if k not in out}
    out['additional_meta'] = json.dumps(meta) if meta else ''
    return out

def load_csv(path: str) -> List[Dict[str, Any]]:
    rows = []
    if pd:
        try:
            df = pd.read_csv(path)
            for rec in df.to_dict(orient='records'):
                rows.append(normalize_record(rec, 'csv'))
            return rows
        except Exception:
            pass
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for rec in reader:
            rows.append(normalize_record(rec, 'csv'))
    return rows

def load_json(path: str) -> List[Dict[str, Any]]:
    data = []
    with open(path) as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        # assume dict of lists / records
        if all(isinstance(v, list) for v in raw.values()):
            for k, lst in raw.items():
                for rec in lst:
                    if isinstance(rec, dict):
                        rec['__subset'] = k
                        data.append(normalize_record(rec, 'json'))
        else:
            data.append(normalize_record(raw, 'json'))
    elif isinstance(raw, list):
        for rec in raw:
            if isinstance(rec, dict):
                data.append(normalize_record(rec, 'json'))
    return data

def load_pcap(path: str) -> List[Dict[str, Any]]:
    results = []
    if PcapReader is None:
        return results
    try:
        for pkt in PcapReader(path):
            if IP in pkt:
                ip = pkt[IP]
                proto = 'TCP' if TCP in pkt else 'UDP' if UDP in pkt else ip.proto
                src_port = pkt[TCP].sport if TCP in pkt else pkt[UDP].sport if UDP in pkt else ''
                dst_port = pkt[TCP].dport if TCP in pkt else pkt[UDP].dport if UDP in pkt else ''
                rec = {
                    'timestamp': pkt.time,
                    'src_ip': ip.src,
                    'dst_ip': ip.dst,
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'protocol': proto,
                    'packet_len': len(pkt),
                }
                results.append(normalize_record(rec, 'pcap'))
    except Exception:
        pass
    return results

def load_flow_txt(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            # naive parse: timestamp src_ip:src_port > dst_ip:dst_port proto bytes label(optional)
            try:
                ts = parts[0]
                src = parts[1]
                arrow_idx = parts.index('>') if '>' in parts else 2
                dst = parts[arrow_idx + 1]
                proto = parts[arrow_idx + 2] if len(parts) > arrow_idx + 2 else ''
                length = parts[arrow_idx + 3] if len(parts) > arrow_idx + 3 else ''
                label = parts[arrow_idx + 4] if len(parts) > arrow_idx + 4 else ''
                src_ip, src_port = (src.split(':') + [''])[:2]
                dst_ip, dst_port = (dst.split(':') + [''])[:2]
                rec = {
                    'timestamp': ts,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'protocol': proto,
                    'packet_len': length,
                    'label': label,
                }
                records.append(normalize_record(rec, 'flow_txt'))
            except Exception:
                continue
    return records

LOADERS = {
    '.csv': load_csv,
    '.json': load_json,
    '.pcap': load_pcap,
    '.cap': load_pcap,
    '.txt': load_flow_txt,
    '.log': load_flow_txt,
}

def discover_files(root: str) -> List[str]:
    targets = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            ext = os.path.splitext(fn.lower())[1]
            if ext in LOADERS:
                targets.append(os.path.join(dirpath, fn))
    return targets

def unify(input_dirs: List[str], output_csv: str):
    all_records: List[Dict[str, Any]] = []
    files = []
    for d in input_dirs:
        if os.path.isfile(d):
            files.append(d)
        elif os.path.isdir(d):
            files.extend(discover_files(d))
    print(f'Discovered {len(files)} files.')
    for path in tqdm(files, desc='Processing files'):
        ext = os.path.splitext(path)[1].lower()
        loader = LOADERS.get(ext)
        if not loader:
            continue
        recs = loader(path)
        all_records.extend(recs)
    print(f'Loaded {len(all_records)} raw records.')
    # Deduplicate by (timestamp, src_ip, dst_ip, src_port, dst_port, protocol, packet_len)
    seen = set()
    deduped = []
    for r in all_records:
        key = tuple(r.get(k) for k in ['timestamp','src_ip','dst_ip','src_port','dst_port','protocol','packet_len'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    print(f'Deduplicated to {len(deduped)} records.')
    # Sort by timestamp if parseable
    try:
        deduped.sort(key=lambda x: dateparser.parse(x['timestamp']) if x['timestamp'] else datetime.min)
    except Exception:
        pass
    # Write CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=UNIFIED_COLUMNS)
        writer.writeheader()
        for r in deduped:
            writer.writerow(r)
    print(f'Wrote unified dataset to {output_csv}')

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Unify heterogeneous network data into a single CSV.')
    ap.add_argument('-i','--inputs', nargs='+', required=True, help='Input directories or files.')
    ap.add_argument('-o','--output', default='unified_dataset.csv', help='Output CSV path.')
    args = ap.parse_args()
    unify(args.inputs, args.output)
