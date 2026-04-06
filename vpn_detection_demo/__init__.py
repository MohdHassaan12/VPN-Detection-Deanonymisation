# vpn_detection_demo/__init__.py
"""
VPN Detection & Deanonymisation Demo
-------------------------------------
Real-time ML pipeline for local network VPN detection on macOS (Apple Silicon).

Modules:
    capture   – live packet capture via PyShark/tshark
    features  – flow-based sliding-window feature extraction
    model     – RandomForest inference engine
    utils     – device detection & network utilities
    dashboard – Streamlit real-time dashboard (app.py)
    main      – pipeline orchestrator (run directly)
"""
__version__ = "1.0.0"
