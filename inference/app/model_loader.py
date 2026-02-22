"""
Model loading and management for inference service
"""
import os
import logging
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages loading and serving of Stage-1 and Stage-2 models"""
    
    def __init__(self, stage1_model_dir: str, stage2_model_path: str):
        self.stage1_model_dir = stage1_model_dir
        self.stage2_model_path = stage2_model_path
        
        self.stage1_model = None  # TensorFlow SavedModel
        self.stage2_model = None  # XGBoost model
        
        # Application class labels (from Stage-1 training)
        self.app_classes = [
            "BROWSING",
            "CHAT", 
            "VOIP",
            "VIDEO",
            "FILE_TRANSFER",
            "P2P",
            "C2_CNC",
            "UNKNOWN"
        ]
        
    async def load_models(self):
        """Load both models"""
        await self._load_stage1()
        await self._load_stage2()
        
    async def _load_stage1(self):
        """Load Stage-1 TensorFlow CNN model"""
        try:
            import tensorflow as tf
            
            if not os.path.exists(self.stage1_model_dir):
                raise FileNotFoundError(f"Stage-1 model not found at {self.stage1_model_dir}")
            
            logger.info(f"Loading Stage-1 model from {self.stage1_model_dir}")
            self.stage1_model = tf.keras.models.load_model(self.stage1_model_dir)
            logger.info(f"Stage-1 model loaded successfully")
            
            # Warm-up inference
            dummy_input = np.zeros((1, 64, 64, 3), dtype=np.float32)
            _ = self.stage1_model.predict(dummy_input, verbose=0)
            logger.info("Stage-1 model warm-up completed")
            
        except Exception as e:
            logger.warning(f"Failed to load Stage-1 model (will use fallback): {e}")
            self.stage1_model = None
    
    async def _load_stage2(self):
        """Load Stage-2 XGBoost model"""
        try:
            import xgboost as xgb
            
            if not os.path.exists(self.stage2_model_path):
                raise FileNotFoundError(f"Stage-2 model not found at {self.stage2_model_path}")
            
            logger.info(f"Loading Stage-2 model from {self.stage2_model_path}")
            self.stage2_model = xgb.Booster()
            self.stage2_model.load_model(self.stage2_model_path)
            logger.info("Stage-2 model loaded successfully")
            
            # Warm-up inference
            import pandas as pd
            # Create a dummy dataframe with the exactly 100 feature columns
            try:
                with open(os.path.join(os.path.dirname(self.stage2_model_path), "feature_names.txt"), "r") as f:
                    feature_cols = [line.strip() for line in f if line.strip()]
            except:
                feature_cols = [f"f{i}" for i in range(100)]
                
            dummy_df = pd.DataFrame(np.zeros((1, len(feature_cols)), dtype=np.float32), columns=feature_cols)
            _ = self.stage2_model.predict(xgb.DMatrix(dummy_df))
            logger.info("Stage-2 model warm-up completed")
            
        except Exception as e:
            logger.error(f"Failed to load Stage-2 model: {e}")
            raise
    
    def models_ready(self) -> bool:
        """Check if required models are loaded (Stage 2 is required, Stage 1 is optional)"""
        return self.stage2_model is not None
    
    def predict_app_class(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict application class using Stage-1 CNN
        
        Args:
            features: Either (64, 64, 3) image or (n_features,) flow stats vector
            
        Returns:
            (predicted_class, confidence)
        """
        if self.stage1_model is None:
            # Fallback behavior if model isn't loaded
            return "UNKNOWN", 0.0
        
        try:
            # Ensure batch dimension
            if len(features.shape) == 3:
                features = np.expand_dims(features, axis=0)
            
            # Predict
            predictions = self.stage1_model.predict(features, verbose=0)
            class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][class_idx])
            
            app_class = self.app_classes[class_idx] if class_idx < len(self.app_classes) else "UNKNOWN"
            
            logger.debug(f"Stage-1 prediction: {app_class} (confidence: {confidence:.3f})")
            return app_class, confidence
            
        except Exception as e:
            logger.error(f"Stage-1 prediction error: {e}")
            return "UNKNOWN", 0.0
    
    def predict_risk_score(self, features: np.ndarray) -> Tuple[int, str, float]:
        """
        Predict risk score using Stage-2 XGBoost
        
        Args:
            features: (n_features,) vector of combined features
            
        Returns:
            (risk_score, intent_class, confidence)
        """
        if self.stage2_model is None:
            raise RuntimeError("Stage-2 model not loaded")
        
        try:
            import pandas as pd
            import xgboost as xgb
            
            # Ensure 2D shape
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
                
            # Try to load feature names to prevent XGBoost ValueError
            try:
                with open(os.path.join(os.path.dirname(self.stage2_model_path), "feature_names.txt"), "r") as f:
                    feature_cols = [line.strip() for line in f if line.strip()]
                features = pd.DataFrame(features, columns=feature_cols)
            except Exception as e:
                logger.warning(f"Could not load feature names: {e}, using raw numpy array")
            
            # Predict
            dmatrix = xgb.DMatrix(features)
            predictions = self.stage2_model.predict(dmatrix)
            
            # Convert probability to risk score (0-99)
            probability = float(predictions[0])
            risk_score = int(probability * 99)
            
            # Intent classification
            intent_class = "MALICIOUS" if risk_score > 60 else "BENIGN"
            confidence = probability if intent_class == "MALICIOUS" else (1.0 - probability)
            
            logger.debug(f"Stage-2 prediction: risk_score={risk_score}, intent={intent_class}")
            return risk_score, intent_class, confidence
            
        except Exception as e:
            logger.error(f"Stage-2 prediction error: {e}")
            return 50, "UNKNOWN", 0.5  # Default to medium risk on error
