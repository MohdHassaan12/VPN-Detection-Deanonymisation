"""
FastAPI Inference Service for VPN Detection & Deanonymisation
Serves Stage-1 (CNN App Classifier) and Stage-2 (XGBoost Intent Classifier)
"""
import os
import time
import logging
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

from .model_loader import ModelManager
from .predict import predict_flow
from .utils import extract_features_from_request

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global model manager and cache
model_manager: Optional[ModelManager] = None
redis_client: Optional[aioredis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global model_manager, redis_client
    
    # Startup: Load models
    logger.info("Loading ML models...")
    model_manager = ModelManager(
        stage1_model_dir=os.getenv("STAGE1_MODEL_DIR", "/models/stage1"),
        stage2_model_path=os.getenv("STAGE2_MODEL_PATH", "/models/stage2/model.xgb")
    )
    await model_manager.load_models()
    logger.info("Models loaded successfully")
    
    # Connect to Redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    try:
        redis_client = await aioredis.from_url(
            f"redis://{redis_host}:{redis_port}",
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
        redis_client = None
    
    yield
    
    # Shutdown: Close connections
    if redis_client:
        await redis_client.close()
    logger.info("Inference service shut down")


app = FastAPI(
    title="VPN Detection & Deanonymisation API",
    description="Multi-stage ML inference for VPN/intent classification",
    version="1.0.0",
    lifespan=lifespan
)


# Request/Response Models
class FlowFeatures(BaseModel):
    """Input features for prediction"""
    # IP Intelligence
    src_ip: str = Field(..., description="Source IP address")
    dst_ip: Optional[str] = Field(None, description="Destination IP")
    src_port: int = Field(..., description="Source port")
    dst_port: int = Field(..., description="Destination port")
    protocol: str = Field(..., description="TCP or UDP")
    
    # IP reputation (from edge layer)
    is_vpn: Optional[bool] = Field(None, description="IP is known VPN")
    is_proxy: Optional[bool] = Field(None, description="IP is known proxy")
    is_datacenter: Optional[bool] = Field(None, description="IP is datacenter")
    fraud_score: Optional[float] = Field(None, ge=0, le=100, description="IP fraud score 0-100")
    
    # Flow statistics
    flow_duration: Optional[float] = Field(None, description="Flow duration in seconds")
    total_fwd_packets: Optional[int] = Field(None, description="Forward packets count")
    total_bwd_packets: Optional[int] = Field(None, description="Backward packets count")
    total_length_fwd_packets: Optional[int] = Field(None, description="Total bytes forward")
    total_length_bwd_packets: Optional[int] = Field(None, description="Total bytes backward")
    fwd_packet_length_mean: Optional[float] = Field(None, description="Mean forward packet size")
    bwd_packet_length_mean: Optional[float] = Field(None, description="Mean backward packet size")
    flow_iat_mean: Optional[float] = Field(None, description="Mean inter-arrival time")
    
    # Behavioral
    human_score: Optional[float] = Field(None, ge=0, le=1, description="Human behavior score")
    login_failure_rate: Optional[float] = Field(None, ge=0, le=1, description="Recent login failure rate")
    account_velocity: Optional[int] = Field(None, description="Accounts attempted in window")
    
    # Additional metadata
    mtu_value: Optional[int] = Field(None, description="Detected MTU value")
    tls_fingerprint: Optional[str] = Field(None, description="TLS fingerprint hash")
    user_agent: Optional[str] = Field(None, description="HTTP User-Agent")
    

class PredictionResponse(BaseModel):
    """Prediction response"""
    request_id: str
    risk_score: int = Field(..., ge=0, le=99, description="Risk score 0-99")
    app_class: str = Field(..., description="Application classification")
    app_confidence: float = Field(..., ge=0, le=1, description="Stage-1 confidence")
    intent_class: str = Field(..., description="Intent classification (BENIGN/MALICIOUS)")
    intent_confidence: float = Field(..., ge=0, le=1, description="Stage-2 confidence")
    action: str = Field(..., description="Policy action: ALLOW/CHALLENGE/BLOCK")
    reason: str = Field(..., description="Human-readable explanation")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")
    cached: bool = Field(False, description="Result from cache")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: bool
    redis_connected: bool
    version: str


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model_manager and model_manager.models_ready() else "degraded",
        models_loaded=model_manager.models_ready() if model_manager else False,
        redis_connected=redis_client is not None,
        version="1.0.0"
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(features: FlowFeatures, request: Request):
    """Main prediction endpoint"""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", f"req_{int(time.time() * 1000)}")
    
    if not model_manager or not model_manager.models_ready():
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    # Check cache
    cache_key = f"prediction:{features.src_ip}:{features.dst_ip}:{features.dst_port}"
    cached_result = None
    
    if redis_client:
        try:
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                import json
                result = json.loads(cached_result)
                result["cached"] = True
                result["request_id"] = request_id
                result["latency_ms"] = (time.time() - start_time) * 1000
                logger.info(f"Cache hit for {cache_key}")
                return PredictionResponse(**result)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
    
    # Predict
    try:
        result = await predict_flow(
            features=features,
            model_manager=model_manager,
            request_id=request_id
        )
        
        # Add latency
        latency_ms = (time.time() - start_time) * 1000
        result["latency_ms"] = latency_ms
        result["cached"] = False
        
        # Cache result (TTL based on risk score)
        if redis_client:
            try:
                import json
                cache_ttl = 3600 if result["risk_score"] < 20 else 300  # 1hr for low risk, 5min for others
                await redis_client.setex(cache_key, cache_ttl, json.dumps(result))
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        
        logger.info(f"Prediction completed: risk_score={result['risk_score']}, action={result['action']}, latency={latency_ms:.2f}ms")
        return PredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=List[PredictionResponse])
async def predict_batch(flows: List[FlowFeatures], request: Request):
    """Batch prediction endpoint"""
    results = []
    for flow in flows:
        try:
            result = await predict(flow, request)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch prediction error for flow: {e}")
            # Continue with other predictions
            continue
    return results


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # TODO: Implement proper Prometheus metrics
    return {
        "predictions_total": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "avg_latency_ms": 0
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
