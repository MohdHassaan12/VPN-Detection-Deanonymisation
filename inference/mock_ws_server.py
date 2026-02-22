from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import asyncio
import json
import random
import datetime
from app.auth import authenticate_user, create_access_token, get_current_active_user, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES, Token, User
from datetime import timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    print("Client connected!")
    flowTypes = ['HTTPS', 'DNS', 'QUIC', 'TCP', 'UDP', 'OpenVPN', 'WireGuard']
    apps = ['BROWSING', 'VIDEO', 'CHAT', 'P2P', 'VOIP', 'GAMING']
    try:
        while True:
            await asyncio.sleep(1.5)
            isVpn = random.random() > 0.6
            deanonymised = isVpn and random.random() > 0.1
            trueApp = apps[random.randint(0, len(apps)-1)] if (isVpn and deanonymised) else flowTypes[random.randint(0, len(flowTypes)-1)]
            
            log = {
                "id": f"req_{random.randint(1000, 9999)}",
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "src": f"10.0.0.{random.randint(1, 255)}",
                "dst": f"{random.randint(1,255)}.{random.randint(1,255)}.1.{random.randint(1,255)}",
                "flowType": trueApp,
                "action": "BLOCK" if isVpn and random.random() > 0.4 else ("CHALLENGE" if isVpn else "ALLOW"),
                "confidence": round(random.uniform(85, 99), 1),
                "latency": random.randint(10, 50),
                "isVpn": isVpn,
                "deanonymised": deanonymised,
                "trueApp": trueApp
            }
            await websocket.send_text(json.dumps(log))
    except Exception as e:
        print("Disconnected", e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
