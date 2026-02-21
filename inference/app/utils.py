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
    Build Stage-2 feature vector combining:
    - IP intelligence
    - Flow statistics  
    - Stage-1 app classification
    - Behavioral features
    
    Returns:
        numpy array of shape (n_features,)
    """
    
    # Map app_class to one-hot encoding
    app_classes = ["BROWSING", "CHAT", "VOIP", "VIDEO", "FILE_TRANSFER", "P2P", "C2_CNC", "UNKNOWN"]
    app_one_hot = [1.0 if cls == app_class else 0.0 for cls in app_classes]
    
    # Build feature vector
    feature_vector = [
        # IP intelligence (0-4)
        float(features.is_vpn or 0),
        float(features.is_proxy or 0),
        float(features.is_datacenter or 0),
        (features.fraud_score or 0.0) / 100.0,  # normalize to 0-1
        
        # Flow statistics (5-11)
        normalize_feature(features.flow_duration, 0, 300),  # max 5min
        normalize_feature(features.total_fwd_packets, 0, 1000),
        normalize_feature(features.total_bwd_packets, 0, 1000),
        normalize_feature(features.total_length_fwd_packets, 0, 100000),
        normalize_feature(features.total_length_bwd_packets, 0, 100000),
        normalize_feature(features.fwd_packet_length_mean, 0, 1500),
        normalize_feature(features.bwd_packet_length_mean, 0, 1500),
        
        # Behavioral (12-14)
        features.human_score or 0.5,  # default to neutral
        features.login_failure_rate or 0.0,
        normalize_feature(features.account_velocity, 0, 100),
        
        # MTU indicator (15)
        1.0 if (features.mtu_value or 1500) < 1450 else 0.0,  # VPN indicator
        
        # App classification (16-23)
        *app_one_hot,
        
        # App confidence (24)
        app_confidence,
    ]
    
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
