"""
FastAPI Inference Service for VPN Detection & Deanonymisation
Serves Stage-1 (CNN App Classifier) and Stage-2 (XGBoost Intent Classifier)
"""
import os
import time
import logging
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pydantic import BaseModel, Field
import redis.asyncio as aioredis
import numpy as np

from .model_loader import ModelManager
from .predict import predict_flow
from .utils import extract_features_from_request
from .auth import authenticate_user, create_access_token, get_current_active_user, get_current_admin_user, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES, Token, User
from datetime import timedelta

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global model manager and cache
model_manager: Optional[ModelManager] = None
redis_client: Optional[aioredis.Redis] = None


async def simulate_traffic_task():
    """Background task to simulate traffic and populate WebSocket for dashboard."""
    import random
    import datetime
    
    flowTypes = ['HTTPS', 'DNS', 'QUIC', 'TCP', 'UDP', 'OpenVPN', 'WireGuard']
    apps = ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'VOIP', 'FILE_TRANSFER']
    
    logger.info("Starting traffic simulation background task...")
    
    while True:
        try:
            await asyncio.sleep(1.5)
            
            if not model_manager or not model_manager.models_ready():
                continue
                
            isVpn = random.random() > 0.6
            deanonymised = isVpn and random.random() > 0.1
            trueApp = apps[random.randint(0, len(apps)-1)] if (isVpn and deanonymised) else flowTypes[random.randint(0, len(flowTypes)-1)]
            
            # Generate dummy xgboost features (100 is expected by the model)
            dummy_features = np.random.rand(100).astype(np.float32)
            
            risk_score, intent_class, intent_confidence = model_manager.predict_risk_score(dummy_features)
            
            # Determine action
            if risk_score <= 20:
                action = "ALLOW"
            elif risk_score <= 60:
                action = "CHALLENGE"
            else:
                action = "BLOCK"
            
            request_id = f"req_sim_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
            latency_ms = random.randint(10, 50)
            
            broadcast_msg = {
                "id": request_id,
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "src": f"10.0.0.{random.randint(1, 255)}",
                "dst": f"{random.randint(1,255)}.{random.randint(1,255)}.1.{random.randint(1,255)}",
                "flowType": trueApp,
                "action": action,
                "confidence": round(intent_confidence * 100, 1),
                "latency": latency_ms,
                "isVpn": isVpn,
                "deanonymised": deanonymised,
                "trueApp": trueApp
            }
            if ws_manager:
                await ws_manager.broadcast(broadcast_msg)
        except Exception as e:
            logger.warning(f"Error in traffic simulator: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global model_manager, redis_client

    
    # Startup: Load models
    logger.info("Loading ML models...")
    model_manager = ModelManager(
        stage1_model_dir=os.getenv("STAGE1_MODEL_DIR", "models/stage1"),
        stage2_model_path=os.getenv("STAGE2_MODEL_PATH", "models/stage2/model.xgb")
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
        
    # Start traffic simulation
    sim_task = asyncio.create_task(simulate_traffic_task())
    
    yield
    
    # Shutdown: Close connections
    sim_task.cancel()
    if redis_client:
        await redis_client.close()
    logger.info("Inference service shut down")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                pass

ws_manager = ConnectionManager()

app = FastAPI(
    title="VPN Detection & Deanonymisation API",
    description="Multi-stage ML inference for VPN/intent classification",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class FlowFeatures(BaseModel):
    """Input features for prediction"""
    # Essential Routing & Identification
    src_ip: str = Field(..., description="Source IP address")
    dst_ip: Optional[str] = Field(None, description="Destination IP")
    src_port: Optional[int] = Field(None, description="Source port")
    dst_port: Optional[int] = Field(None, description="Destination port")
    protocol: Optional[str] = Field(None, description="Protocol (TCP/UDP)")
    
    # Optional IP intelligence features returned by edge layer
    is_vpn: Optional[bool] = Field(None, description="IP is known VPN")
    is_proxy: Optional[bool] = Field(None, description="IP is known proxy")
    is_datacenter: Optional[bool] = Field(None, description="IP is datacenter")
    fraud_score: Optional[float] = Field(None, ge=0, le=100, description="IP fraud score 0-100")
    
    # Catch-all for the 100 flow features required by XGBoost
    # The client must supply these under the 'raw_features' dict,
    # or we extract them from a flattened dict.
    raw_features: Dict[str, float] = Field(default_factory=dict, description="The 100 raw numeric features required by XGBoost model")


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


from prometheus_client import make_asgi_app, Counter, Histogram

# Initialize Prometheus metrics
PREDICTIONS_TOTAL = Counter(
    'vpn_predictions_total',
    'Total predictions made by risk action',
    ['action']
)
CACHE_HITS = Counter(
    'vpn_cache_hits_total',
    'Total cache hits vs misses',
    ['status']
)
INFERENCE_LATENCY = Histogram(
    'vpn_inference_latency_ms',
    'Inference latency in milliseconds',
    buckets=(10, 25, 50, 100, 250, 500, 1000)
)

# ... (keep existing setup and app object definition) ...

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Authentication Endpoints
@app.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


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
async def predict(features: FlowFeatures, request: Request, current_user: User = Depends(get_current_active_user)):
    """Main prediction endpoint (Secured)"""
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
                latency_ms = (time.time() - start_time) * 1000
                result["latency_ms"] = latency_ms
                
                # Update metrics
                CACHE_HITS.labels(status='hit').inc()
                PREDICTIONS_TOTAL.labels(action=result['action']).inc()
                INFERENCE_LATENCY.observe(latency_ms)
                
                logger.info(f"Cache hit for {cache_key}")
                return PredictionResponse(**result)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            
    # Metrics
    CACHE_HITS.labels(status='miss').inc()
    
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
                
        # Broadcast via WebSockets
        try:
            import datetime
            broadcast_msg = {
                "id": request_id,
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "src": features.src_ip,
                "dst": features.dst_ip or "Unknown",
                "flowType": result["app_class"],
                "action": result["action"],
                "confidence": result["intent_confidence"] * 100,
                "latency": latency_ms,
                "isVpn": features.is_vpn if features.is_vpn is not None else False,
                "deanonymised": result["app_class"] not in ["UNKNOWN", "VPN"],
                "trueApp": result["app_class"]
            }
            asyncio.create_task(ws_manager.broadcast(broadcast_msg))
        except Exception as e:
            logger.warning(f"Broadcast error: {e}")

        # Update specific metrics
        PREDICTIONS_TOTAL.labels(action=result['action']).inc()
        INFERENCE_LATENCY.observe(latency_ms)
        
        logger.info(f"Prediction completed: risk_score={result['risk_score']}, action={result['action']}, latency={latency_ms:.2f}ms")
        return PredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=List[PredictionResponse])
async def predict_batch(flows: List[FlowFeatures], request: Request, current_user: User = Depends(get_current_active_user)):
    """Batch prediction endpoint (Secured)"""
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



@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


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
