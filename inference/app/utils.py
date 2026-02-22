"""
Utility functions for feature extraction and processing
"""
import numpy as np
from typing import Optional


def extract_features_from_request(request_data: dict) -> dict:
    """Extract and validate features from raw request"""
    # Placeholder for feature extraction logic
    return request_data


def build_stage2_features(features, app_class: str, app_confidence: float) -> np.ndarray:
    """
    Build Stage-2 feature vector matching the exact 100 features used during XGBoost training.
    
    Reads feature_names.txt directly to ensure the vector order is perfect.
    """
    import os
    
    # Load exact feature names list
    current_dir = os.path.dirname(__file__)
    feature_names_path = os.path.join(current_dir, "../models/stage2/feature_names.txt")
    
    try:
        with open(feature_names_path, "r") as f:
            feature_names = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"Warning: Could not read feature_names.txt: {e}. Returning dummy zeros.")
        return np.zeros(100, dtype=np.float32)
        
    # Build vector based on the exact expected list
    feature_vector = []
    
    raw_dict = features.raw_features or {}
    
    for fname in feature_names:
        # Some basic fallbacks for things not explicitly provided
        val = raw_dict.get(fname)
        
        if val is None:
            # Check edge layer attrs if present
            if fname == 'Protocol' and features.protocol:
                val = 6.0 if features.protocol.upper() == 'TCP' else 17.0
            elif fname == 'vpn_flag' and features.is_vpn is not None:
                val = 1.0 if features.is_vpn else 0.0
            elif fname == 'src_port': val = features.src_port
            elif fname == 'dst_port': val = features.dst_port
            else:
                val = 0.0 # Strict default for missing features
                
        feature_vector.append(float(val))
        
    return np.array(feature_vector, dtype=np.float32)


def normalize_feature(value: Optional[float], min_val: float, max_val: float) -> float:
    """Normalize feature to 0-1 range"""
    if value is None:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def encode_app_class(app_class: str) -> int:
    """Encode app class to integer"""
    app_classes = ["BROWSING", "CHAT", "VOIP", "VIDEO", "FILE_TRANSFER", "P2P", "C2_CNC", "UNKNOWN"]
    try:
        return app_classes.index(app_class)
    except ValueError:
        return len(app_classes) - 1  # UNKNOWN
