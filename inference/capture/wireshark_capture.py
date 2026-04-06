import time
import requests
import logging
import asyncio
import os
import sys

# Ensure module can be run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyshark
from features.realtime_extractor import FlowTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - WIRESHARK - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8080/api")
USERNAME = "admin"
PASSWORD = "admin123"

class WiresharkPipeline:
    def __init__(self, interface='en0'):
        self.interface = interface
        self.tracker = FlowTracker(max_window=50)
        self.token = None
        self.batch_queue = []
        
    def authenticate(self):
        try:
            logger.info(f"Authenticating with backend at {API_URL}/auth/login")
            resp = requests.post(f"{API_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD})
            resp.raise_for_status()
            self.token = resp.json()["access_token"]
            logger.info("Successfully authenticated with ML Backend. Token acquired.")
        except requests.exceptions.ConnectionError:
            logger.error(f"Backend is not reachable at {API_URL}. Start it with LIVE_CAPTURE_MODE=True.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")
            raise

    def send_batch(self):
        if not self.batch_queue:
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            # Limit payload size to top 15 most active flows to prevent backend crash
            payload = sorted(self.batch_queue, key=lambda x: x.get("packet_count", 0), reverse=True)[:15]
            
            resp = requests.post(f"{API_URL}/predict/batch", json=payload, headers=headers)
            
            if resp.status_code == 401:
                logger.warning("Token expired. Re-authenticating...")
                self.authenticate()
            elif resp.status_code == 200:
                logger.info(f"Successfully piped {len(payload)} PyShark flow states to XGBoost Engine.")
            else:
                logger.error(f"Failed to post flows: {resp.status_code} - {resp.text}")
                
            self.batch_queue.clear()
        except Exception as e:
            logger.error(f"Error posting batch: {e}")
            self.batch_queue.clear()

    async def capture_loop(self):
        self.authenticate()
        logger.info(f"Starting PyShark Live Capture on interface: {self.interface}...")
        
        # We process packets async to not block
        try:
            capture = pyshark.LiveCapture(interface=self.interface)
            
            last_flush = time.time()
            async for packet in capture.sniff_continuously():
                try:
                    feature_set = self.tracker.process_packet(packet)
                    if feature_set:
                        self.batch_queue.append(feature_set)
                        
                    # Flush every 2 seconds if we have data
                    if time.time() - last_flush > 2.0:
                        if self.batch_queue:
                            self.send_batch()
                        last_flush = time.time()
                        
                except Exception as packet_err:
                    logger.debug(f"Skipping malformed packet: {packet_err}")
                    
        except KeyboardInterrupt:
            logger.info("Gracefully shutting down Wireshark capture.")
        except Exception as e:
            logger.error(f"Capture failed. Did you run with sudo? Error: {e}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        logger.warning("You are not running as root/Administrator! PyShark/tshark requires sudo to read interface.")
    
    # Interface bridge100 or en0
    interface = os.getenv("CAPTURE_INTERFACE", "en0")
    
    pipeline = WiresharkPipeline(interface=interface)
    try:
        asyncio.run(pipeline.capture_loop())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
