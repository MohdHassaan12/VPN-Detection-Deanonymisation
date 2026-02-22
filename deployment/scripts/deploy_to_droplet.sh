#!/bin/bash
# deploy_to_droplet.sh

# Usage: ./deploy_to_droplet.sh <DROPLET_IP> <USERNAME>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <DROPLET_IP> <USERNAME>"
    echo "Example: $0 192.168.1.100 root"
    exit 1
fi

DROPLET_IP=$1
USERNAME=$2
REMOTE_DIR="/opt/vpn_detection"

echo "Deploying to $USERNAME@$DROPLET_IP:$REMOTE_DIR..."

# Create remote directory
ssh $USERNAME@$DROPLET_IP "mkdir -p $REMOTE_DIR"

# Rsync project files (excluding large local datasets, .git, and virtual envs)
rsync -avz --progress \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude 'datasets' \
    --exclude '__pycache__' \
    --exclude '*.pcap' \
    --exclude '*.csv' \
    --exclude 'inference/models/*' \
    ./ $USERNAME@$DROPLET_IP:$REMOTE_DIR/

echo "Deployment complete! Code synced to $REMOTE_DIR"
echo "Next step: Run setup_droplet.sh on the droplet"
