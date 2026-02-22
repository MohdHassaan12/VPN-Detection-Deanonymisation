#!/bin/bash
# setup_droplet.sh

# This script sets up the Python environment on the Ubuntu droplet.
# Run this *on* the droplet after deploying the code.

APP_DIR="/opt/vpn_detection"

echo "Setting up environment in $APP_DIR..."
cd $APP_DIR || exit 1

# 1. System updates & Dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv libpcap-dev build-essential tmux default-jre

# 2. Virtual Environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

# 3. Install Python requirements
echo "Installing pip dependencies..."
pip install --upgrade pip
pip install -r preprocessing/requirements.txt
pip install -r inference/requirements.txt
pip install scapy pandas numpy xgboost scikit-learn jupyter

echo "Setup Complete!"
echo "To start training (e.g., using tmux):"
echo "1. Activate env: source .venv/bin/activate"
echo "2. Run: python model_training/stage2_intent_classifier/train_xgboost.py --input <path_to_csv>"
