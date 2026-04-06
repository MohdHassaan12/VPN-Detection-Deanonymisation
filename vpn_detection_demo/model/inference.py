"""
model/inference.py
-------------------
ML inference layer for the VPN detection demo.

Loads the pre-trained RandomForest classifier (vpn_classifier.joblib)
and exposes a clean prediction API that accepts a 11-feature numpy vector
and returns:
    • is_vpn          – bool
    • confidence      – float 0-1
    • risk_score      – int 0-100
    • risk_level      – "LOW" | "MEDIUM" | "HIGH"
    • label           – "VPN" | "Non-VPN"
"""

import os
import time
import logging
import numpy as np
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Expected number of features (matches model training)
# ---------------------------------------------------------------------------

N_FEATURES = 11
FEATURE_NAMES = [
    "mean_pkt_size", "std_pkt_size", "min_pkt_size", "max_pkt_size",
    "mean_iat", "std_iat", "flow_duration",
    "total_bytes", "packet_count", "tcp_ratio", "udp_ratio",
]

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "vpn_classifier.joblib")


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class InferenceResult:
    """Output of the VPN inference pipeline for a single flow."""
    is_vpn: bool
    label: str          # "VPN" or "Non-VPN"
    confidence: float   # 0.0 – 1.0
    risk_score: int     # 0 – 100
    risk_level: str     # "LOW" | "MEDIUM" | "HIGH"
    latency_ms: float   # inference time in milliseconds
    src_ip: str = ""    # optional, set by caller


def compute_risk_score(probability: float) -> int:
    """
    Map VPN probability to risk score 0–100.
    Calibrated so borderline flows don't immediately spike to 100.
    """
    return min(100, int(round(probability * 100)))


def risk_level(score: int) -> str:
    """Categorise a 0–100 risk score into LOW / MEDIUM / HIGH."""
    if score <= 20:
        return "LOW"
    elif score <= 60:
        return "MEDIUM"
    else:
        return "HIGH"


# ---------------------------------------------------------------------------
# Main inference engine
# ---------------------------------------------------------------------------

class VPNInferenceEngine:
    """
    Thread-safe wrapper around the scikit-learn RandomForest classifier.

    Usage
    -----
        engine = VPNInferenceEngine()
        engine.load()

        result = engine.predict(feature_vector, src_ip="10.0.0.5")
        print(result.label, result.risk_score)
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self._model = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self) -> bool:
        """Load the joblib model file.  Returns True on success."""
        try:
            import joblib
            logger.info(f"[VPNInference] Loading model from {self.model_path}")
            self._model = joblib.load(self.model_path)
            self._loaded = True

            # Validate model shape
            expected_features = getattr(self._model, "n_features_in_", None)
            if expected_features and expected_features != N_FEATURES:
                logger.warning(
                    f"[VPNInference] Model expects {expected_features} features "
                    f"but N_FEATURES={N_FEATURES}. Predictions may be incorrect."
                )

            logger.info(
                f"[VPNInference] Model loaded: "
                f"n_estimators={getattr(self._model, 'n_estimators', '?')}, "
                f"classes={getattr(self._model, 'classes_', '?')}"
            )
            return True

        except Exception as exc:
            logger.error(f"[VPNInference] Failed to load model: {exc}")
            self._loaded = False
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded and self._model is not None

    # ------------------------------------------------------------------
    # Predict
    # ------------------------------------------------------------------

    def predict(
        self,
        feature_vector: np.ndarray,
        src_ip: str = "",
    ) -> Optional[InferenceResult]:
        """
        Run inference on a 11-element feature vector.

        Args:
            feature_vector: shape (11,) float32 numpy array.
            src_ip: originating IP, attached to the result for traceability.

        Returns:
            InferenceResult, or None if model not loaded / bad input.
        """
        if not self.is_loaded:
            logger.warning("[VPNInference] predict() called but model not loaded.")
            return None

        if feature_vector is None or len(feature_vector) != N_FEATURES:
            logger.debug(f"[VPNInference] Invalid feature vector (len={len(feature_vector) if feature_vector is not None else None})")
            return None

        try:
            t0 = time.perf_counter()

            # Reshape to (1, N_FEATURES) for sklearn
            X = feature_vector.reshape(1, -1).astype(np.float32)

            # Predict class + probability
            pred_class = int(self._model.predict(X)[0])          # 0 or 1
            proba = self._model.predict_proba(X)[0]               # [P(0), P(1)]

            vpn_proba = float(proba[1]) if len(proba) > 1 else float(proba[0])
            is_vpn = bool(pred_class == 1)

            score = compute_risk_score(vpn_proba)
            latency = (time.perf_counter() - t0) * 1_000          # ms

            result = InferenceResult(
                is_vpn=is_vpn,
                label="VPN" if is_vpn else "Non-VPN",
                confidence=vpn_proba if is_vpn else (1.0 - vpn_proba),
                risk_score=score,
                risk_level=risk_level(score),
                latency_ms=round(latency, 3),
                src_ip=src_ip,
            )

            logger.debug(
                f"[VPNInference] {src_ip} → {result.label} "
                f"(conf={result.confidence:.2%}, risk={result.risk_score}, latency={result.latency_ms:.1f}ms)"
            )
            return result

        except Exception as exc:
            logger.error(f"[VPNInference] Prediction error for {src_ip}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Convenience: simulate (for testing without live capture)
    # ------------------------------------------------------------------

    def predict_mock(self, src_ip: str = "10.0.0.1", is_vpn_hint: bool = False) -> InferenceResult:
        """
        Generate a realistic mock result for demo/testing.
        Bypasses the real model – useful when tshark is not available.
        """
        import random
        if is_vpn_hint:
            vpn_proba = random.uniform(0.65, 0.98)
        else:
            vpn_proba = random.uniform(0.02, 0.35)

        score = compute_risk_score(vpn_proba)
        is_vpn = vpn_proba >= 0.5

        return InferenceResult(
            is_vpn=is_vpn,
            label="VPN" if is_vpn else "Non-VPN",
            confidence=vpn_proba if is_vpn else (1.0 - vpn_proba),
            risk_score=score,
            risk_level=risk_level(score),
            latency_ms=round(random.uniform(0.5, 3.5), 2),
            src_ip=src_ip,
        )


# ---------------------------------------------------------------------------
# Module-level singleton (used by main.py and dashboard)
# ---------------------------------------------------------------------------

_engine: Optional[VPNInferenceEngine] = None


def get_engine() -> VPNInferenceEngine:
    """Return the module-level singleton, loading model on first access."""
    global _engine
    if _engine is None:
        _engine = VPNInferenceEngine()
        _engine.load()
    return _engine


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    engine = VPNInferenceEngine()
    ok = engine.load()
    if not ok:
        # Fallback: show mock predictions
        print("Model not loaded – showing mock results:")
        for i in range(5):
            r = engine.predict_mock(src_ip=f"10.0.0.{i+1}", is_vpn_hint=(i % 2 == 0))
            print(f"  {r.src_ip}: {r.label:8} risk={r.risk_score:3d}  conf={r.confidence:.2%}  {r.risk_level}")
    else:
        # Test with a dummy feature vector
        dummy = np.array([512, 128, 64, 1500, 0.05, 0.02, 10.0, 25600, 50, 0.7, 0.3], dtype=np.float32)
        result = engine.predict(dummy, src_ip="192.168.1.10")
        if result:
            print(f"Prediction: {result.label}, risk={result.risk_score}, level={result.risk_level}, conf={result.confidence:.2%}")
