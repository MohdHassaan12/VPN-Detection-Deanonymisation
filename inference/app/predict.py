"""
Prediction logic for two-stage ML pipeline
"""
import logging
from typing import Dict
import numpy as np

from .model_loader import ModelManager
from .utils import build_stage2_features

logger = logging.getLogger(__name__)


def determine_action(risk_score: int) -> tuple[str, str]:
    """
    Determine policy action based on risk score
    
    Returns:
        (action, reason)
    """
    if risk_score <= 20:
        return "ALLOW", "Low risk - legitimate traffic pattern detected"
    elif risk_score <= 60:
        return "CHALLENGE", "Medium risk - additional verification required (MFA/CAPTCHA)"
    else:
        return "BLOCK", "High risk - suspicious activity detected"


async def predict_flow(features, model_manager: ModelManager, request_id: str) -> Dict:
    """
    Run two-stage prediction pipeline
    
    Stage 1: Classify application type (CNN)
    Stage 2: Score intent/risk (XGBoost)
    
    Args:
        features: FlowFeatures pydantic model
        model_manager: ModelManager instance
        request_id: Request ID for logging
        
    Returns:
        Dict with prediction results
    """
    
    # Stage 1: Application Classification
    # For now, use flow statistics (in production, use Packet-Block images if available)
    stage1_features = build_stage1_features(features)
    app_class, app_confidence = model_manager.predict_app_class(stage1_features)
    
    logger.info(f"[{request_id}] Stage-1: app_class={app_class}, confidence={app_confidence:.3f}")
    
    # Stage 2: Intent/Risk Scoring
    stage2_features = build_stage2_features(features, app_class, app_confidence)
    risk_score, intent_class, intent_confidence = model_manager.predict_risk_score(stage2_features)
    
    logger.info(f"[{request_id}] Stage-2: risk_score={risk_score}, intent={intent_class}")
    
    # Determine action
    action, reason = determine_action(risk_score)
    
    # Build response
    result = {
        "request_id": request_id,
        "risk_score": risk_score,
        "app_class": app_class,
        "app_confidence": app_confidence,
        "intent_class": intent_class,
        "intent_confidence": intent_confidence,
        "action": action,
        "reason": reason
    }
    
    return result


def build_stage1_features(features) -> np.ndarray:
    """
    Build Stage-1 input features (flow statistics for now)
    
    In production, this would load/generate Packet-Block images
    For now, create a dummy 64x64x3 image or use flow stats
    """
    # TODO: In production, load actual Packet-Block image from flow
    # For now, create feature vector from flow stats
    
    flow_features = [
        features.raw_features.get('flow_duration', 0.0),
        features.raw_features.get('total_fwd_packets', 0),
        features.raw_features.get('total_bwd_packets', 0),
        features.raw_features.get('total_length_fwd_packets', 0),
        features.raw_features.get('total_length_bwd_packets', 0),
        features.raw_features.get('fwd_packet_length_mean', 0.0),
        features.raw_features.get('bwd_packet_length_mean', 0.0),
        features.raw_features.get('flow_iat_mean', 0.0),
    ]
    
    # Pad to expected size or use placeholder
    # If model expects image: return np.zeros((64, 64, 3), dtype=np.float32)
    # If model expects flow vector: return np.array(flow_features, dtype=np.float32)
    
    # For this example, return a dummy image (replace with real image loading)
    dummy_image = np.random.rand(64, 64, 3).astype(np.float32) * 0.1
    return dummy_image
