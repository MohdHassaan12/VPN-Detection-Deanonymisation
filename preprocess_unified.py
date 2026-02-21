#!/usr/bin/env python3
"""
Preprocess unified dataset for model training/testing.
- Loads unified CSV from unify_dataset.py
- Cleans and normalizes types
- Optional simple label mapping
- Writes cleaned CSV and train/test splits

Dependencies: pandas (preferred), scikit-learn (optional for stratified split)
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None

try:
    from sklearn.model_selection import train_test_split  # type: ignore
except Exception:
    train_test_split = None

UNIFIED_COLUMNS = [
    'timestamp', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol',
    'packet_len', 'direction', 'label', 'source_type', 'additional_meta'
]

PROTO_MAP = {
    'TCP': 6,
    'UDP': 17,
    'ICMP': 1,
}

LABEL_POSITIVE_TOKENS = {'vpn', 'anonym', 'proxy', 'tor'}
LABEL_NEGATIVE_TOKENS = {'novpn', 'benign', 'normal', 'nonvpn', 'clear'}


def _safe_iso(ts: Any) -> str:
    if ts in (None, ''):
        return ''
    if isinstance(ts, (int, float)):
        return datetime.utcfromtimestamp(float(ts)).isoformat()
    if isinstance(ts, str):
        # Attempt multiple common formats
        for fmt in (
            '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S.%f'
        ):
            try:
                return datetime.strptime(ts, fmt).isoformat()
            except Exception:
                pass
        return ts
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts)


def _to_int(val: Any, default: int = -1) -> int:
    try:
        if val in (None, ''):
            return default
        return int(float(val))
    except Exception:
        return default


def _norm_protocol(val: Any) -> str:
    if val is None:
        return ''
    s = str(val).upper()
    if s.isdigit():
        # numeric protocol value, map common ones to names
        num = int(s)
        for k, v in PROTO_MAP.items():
            if v == num:
                return k
        return s
    # strip payload like 'TCP/HTTP'
    if '/' in s:
        s = s.split('/')[0]
    return s


def _protocol_num(proto_str: str) -> int:
    if not proto_str:
        return 0
    return PROTO_MAP.get(proto_str.upper(), 0)


def _standardize_label(lbl: Any) -> str:
    if lbl is None:
        return ''
    s = str(lbl).strip().lower()
    return s


def _infer_label_num(lbl: str) -> Optional[int]:
    if not lbl:
        return None
    # heuristic: contains any positive/negative tokens
    if any(tok in lbl for tok in LABEL_POSITIVE_TOKENS):
        return 1
    if any(tok in lbl for tok in LABEL_NEGATIVE_TOKENS):
        return 0
    if lbl in ('1', 'true', 'yes', 'positive'):
        return 1
    if lbl in ('0', 'false', 'no', 'negative'):
        return 0
    return None


def preprocess(
    input_csv: str,
    output_clean: str,
    train_path: Optional[str] = None,
    test_path: Optional[str] = None,
    test_size: float = 0.2,
    seed: int = 42,
    drop_unlabeled: bool = False,
):
    if pd is None:
        # Fallback minimal cleaning without pandas
        rows: List[Dict[str, Any]] = []
        with open(input_csv, newline='') as f:
            reader = csv.DictReader(f)
            for r in reader:
                # ...existing code...
                r_std = {c: r.get(c, '') for c in UNIFIED_COLUMNS}
                r_std['timestamp'] = _safe_iso(r_std['timestamp'])
                r_std['src_port'] = _to_int(r_std['src_port'])
                r_std['dst_port'] = _to_int(r_std['dst_port'])
                r_std['packet_len'] = _to_int(r_std['packet_len'], default=0)
                proto = _norm_protocol(r_std['protocol'])
                r_std['protocol'] = proto
                r_std['protocol_num'] = _protocol_num(proto)
                lbl = _standardize_label(r_std['label'])
                r_std['label'] = lbl
                lbl_num = _infer_label_num(lbl)
                if drop_unlabeled and lbl_num is None:
                    continue
                r_std['label_num'] = '' if lbl_num is None else lbl_num
                # drop rows missing essential fields
                if not r_std['src_ip'] or not r_std['dst_ip'] or not r_std['timestamp']:
                    continue
                rows.append(r_std)
        # Write cleaned CSV
        fieldnames = UNIFIED_COLUMNS + ['protocol_num', 'label_num']
        with open(output_clean, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        # Basic random split if requested and label available
        if train_path and test_path:
            import random
            rng = random.Random(seed)
            rng.shuffle(rows)
            n_test = int(len(rows) * test_size)
            test_rows = rows[:n_test]
            train_rows = rows[n_test:]
            for p, subset in ((train_path, train_rows), (test_path, test_rows)):
                with open(p, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in subset:
                        writer.writerow(r)
        return

    # pandas path
    df = pd.read_csv(input_csv)

    # Ensure all columns exist
    for c in UNIFIED_COLUMNS:
        if c not in df.columns:
            df[c] = ''

    # Type normalization
    df['timestamp'] = df['timestamp'].apply(_safe_iso)
    for c in ['src_port', 'dst_port', 'packet_len']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(-1 if c != 'packet_len' else 0).astype(int)
    df['protocol'] = df['protocol'].apply(_norm_protocol)
    df['protocol_num'] = df['protocol'].apply(_protocol_num)

    # Label handling
    df['label'] = df['label'].apply(_standardize_label)
    df['label_num'] = df['label'].apply(_infer_label_num)
    if drop_unlabeled:
        df = df[df['label_num'].notna()]

    # Drop rows missing essential fields
    df = df[(df['src_ip'] != '') & (df['dst_ip'] != '') & (df['timestamp'] != '')]

    # Deduplicate
    df = df.drop_duplicates(subset=['timestamp','src_ip','dst_ip','src_port','dst_port','protocol','packet_len'])

    # Write cleaned
    df.to_csv(output_clean, index=False)

    # Train/test split if paths provided
    if train_path and test_path:
        stratify_col = None
        if 'label_num' in df.columns and df['label_num'].notna().sum() > 0:
            # use only rows with label for splitting
            df_labeled = df[df['label_num'].notna()]
            if df_labeled['label_num'].nunique() > 1:
                stratify_col = df_labeled['label_num']
                if train_test_split is not None:
                    train_df, test_df = train_test_split(
                        df_labeled, test_size=test_size, random_state=seed, stratify=stratify_col
                    )
                else:
                    # manual stratified split
                    train_parts = []
                    test_parts = []
                    for cls, grp in df_labeled.groupby('label_num'):
                        n_test = int(len(grp) * test_size)
                        part_test = grp.sample(n=n_test, random_state=seed)
                        part_train = grp.drop(part_test.index)
                        test_parts.append(part_test)
                        train_parts.append(part_train)
                    train_df = pd.concat(train_parts)
                    test_df = pd.concat(test_parts)
            else:
                # fallback random split
                train_df = df.sample(frac=1 - test_size, random_state=seed)
                test_df = df.drop(train_df.index)
        else:
            train_df = df.sample(frac=1 - test_size, random_state=seed)
            test_df = df.drop(train_df.index)

        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Clean unified CSV and create train/test splits.')
    ap.add_argument('-i','--input', default='unified_dataset.csv', help='Input unified CSV path')
    ap.add_argument('-o','--output', default='unified_dataset.cleaned.csv', help='Output cleaned CSV path')
    ap.add_argument('--train', default='train.csv', help='Output train CSV path')
    ap.add_argument('--test', default='test.csv', help='Output test CSV path')
    ap.add_argument('--test-size', type=float, default=0.2, help='Test size fraction')
    ap.add_argument('--seed', type=int, default=42, help='Random seed')
    ap.add_argument('--drop-unlabeled', action='store_true', help='Drop rows with unknown labels')
    args = ap.parse_args()

    preprocess(
        input_csv=args.input,
        output_clean=args.output,
        train_path=args.train,
        test_path=args.test,
        test_size=args.test_size,
        seed=args.seed,
        drop_unlabeled=args.drop_unlabeled,
    )