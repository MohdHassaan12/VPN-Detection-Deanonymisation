import requests
import json
import time

def main():
    print("Testing VPN Detection API...")
    url = "http://localhost:8080/predict"
    
    # Payload matching the exact updated schema
    payload = {
        "src_ip": "10.0.0.1",
        "dst_ip": "8.8.8.8",
        "src_port": 54321,
        "dst_port": 443,
        "protocol": "TCP",
        "raw_features": {
            "Flow Duration": 1500.0,
            "packet_count_total": 50,
            "byte_count_total": 45000,
            "mtu": 1500,
            "vpn_flag": 0
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers)
        duration = (time.time() - start_time) * 1000
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Request took: {duration:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print("\nPrediction Result:")
            print(json.dumps(result, indent=2))
        else:
            print(f"\nError: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API. Is it running on localhost:8080?")

if __name__ == "__main__":
    main()
