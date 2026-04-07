import os
import asyncio
import aiohttp
import random

# Cache to avoid spamming the APIs for the same destination IP
_ip_cache = {}

IPINFO_API_KEY = os.getenv("IPINFO_API_KEY", "")
IPQS_API_KEY = os.getenv("IPQS_API_KEY", "")

async def fetch_ipinfo(session: aiohttp.ClientSession, ip: str):
    """Fetch geographical location from IPinfo.io"""
    if not IPINFO_API_KEY:
        # Fallback to plausible dummy coords
        return {
            "coord": [(random.random() * 360) - 180, (random.random() * 140) - 70],
            "location": "Local Segment (No API Key)"
        }
    
    try:
        url = f"https://ipinfo.io/{ip}/json?token={IPINFO_API_KEY}"
        async with session.get(url, timeout=2.0) as response:
            if response.status == 200:
                data = await response.json()
                loc = data.get("loc", "0,0").split(",")
                # IPinfo returns "lat,lng", but Map expects [lng, lat]
                return {
                    "coord": [float(loc[1]), float(loc[0])],
                    "location": f"{data.get('city', 'Unknown')}, {data.get('country', 'XX')}"
                }
    except Exception as e:
        print(f"[OSINT ERROR] IPinfo fetch failed: {e}")
        pass
    
    return {
        "coord": [(random.random() * 360) - 180, (random.random() * 140) - 70],
        "location": "Lookup Failed"
    }

async def fetch_ipqs(session: aiohttp.ClientSession, ip: str):
    """Fetch VPN/Fraud intelligence from IPQualityScore"""
    if not IPQS_API_KEY:
        # Fallback default proxy assumptions
        return {
            "fraud_score": random.randint(30, 95),
            "vpn": random.choice([True, False]),
            "tor": False
        }

    try:
        # URL structure: https://www.ipqualityscore.com/api/json/ip/IPQS_API_KEY/IP_ADDRESS
        url = f"https://www.ipqualityscore.com/api/json/ip/{IPQS_API_KEY}/{ip}"
        async with session.get(url, timeout=2.0) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "fraud_score": data.get("fraud_score", 0),
                    "vpn": data.get("vpn", False) or data.get("proxy", False),
                    "tor": data.get("tor", False)
                }
    except Exception as e:
        print(f"[OSINT ERROR] IPQS fetch failed: {e}")
        pass

    return {"fraud_score": 50, "vpn": False, "tor": False}

async def enrich_ip(ip: str):
    """
    Given an IP, quickly retrieve geographical and threat intellect.
    Results are cached in-memory to limit API quota usage.
    """
    # Exclude obvious local networks
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127.") or ip == "Unknown":
        return {
            "coord": [0, 0],
            "location": "Local Network",
            "fraud_score": 0,
            "threat_type": "Internal"
        }

    if ip in _ip_cache:
        return _ip_cache[ip]

    async with aiohttp.ClientSession() as session:
        geo_task = asyncio.create_task(fetch_ipinfo(session, ip))
        threat_task = asyncio.create_task(fetch_ipqs(session, ip))

        geo, threat = await asyncio.gather(geo_task, threat_task)

    threat_type = "High Risk Proxy" if threat.get("fraud_score", 0) > 85 else ("VPN Node" if threat.get("vpn") else "Direct Route")
    if threat.get("tor"):
        threat_type = "Tor Exit Node"

    result = {
        "coord": geo["coord"],
        "location": geo["location"],
        "fraud_score": threat["fraud_score"],
        "threat_type": threat_type
    }

    _ip_cache[ip] = result
    
    # Cap cache size to avoid memory bloat
    if len(_ip_cache) > 2000:
        _ip_cache.pop(next(iter(_ip_cache)))

    return result
