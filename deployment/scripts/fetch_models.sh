#!/bin/bash
# fetch_models.sh

# Usage: ./fetch_models.sh <DROPLET_IP> <USERNAME>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <DROPLET_IP> <USERNAME>"
    echo "Example: $0 192.168.1.100 root"
    exit 1
fi

DROPLET_IP=$1
USERNAME=$2
REMOTE_DIR="/opt/vpn_detection"

echo "Fetching trained models from $USERNAME@$DROPLET_IP..."

# Rsync the models directory back to the local machine
cd "$(dirname "$0")/../../" || exit 1
rsync -avz --progress "$USERNAME@$DROPLET_IP:$REMOTE_DIR/inference/models/" "./inference/models/"

echo "Models fetched successfully! Your local FastAPI server can now use them."
