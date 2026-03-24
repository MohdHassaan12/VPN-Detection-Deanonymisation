#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy_to_droplet.sh  —  Deploy VPN Detection to a DigitalOcean droplet
#
# Usage:
#   ./deployment/scripts/deploy_to_droplet.sh <DROPLET_IP> [USERNAME]
#
# Prerequisites (local machine):
#   - SSH key configured for the droplet
#   - .env file in project root (copy from .env.example and fill in values)
#   - rsync installed
#
# What it does:
#   1. Syncs code to /opt/vpn_detection on the droplet (excludes large files)
#   2. Installs Docker + Docker Compose plugin if not present
#   3. Copies your local .env file to the droplet
#   4. Builds and runs `docker compose up -d`
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DROPLET_IP="${1:-}"
USERNAME="${2:-root}"
REMOTE_DIR="/opt/vpn_detection"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

if [ -z "$DROPLET_IP" ]; then
  echo "❌  Usage: $0 <DROPLET_IP> [USERNAME]"
  echo "   Example: $0 165.232.100.200 root"
  exit 1
fi

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo "❌  Missing .env file at project root."
  echo "   Copy .env.example → .env and fill in VITE_API_BASE_URL, SECRET_KEY, etc."
  exit 1
fi

SSH="ssh -o StrictHostKeyChecking=no $USERNAME@$DROPLET_IP"
SCP="scp -o StrictHostKeyChecking=no"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀  Deploying to $USERNAME@$DROPLET_IP:$REMOTE_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1: Create remote directory ──────────────────────────────────────────
echo ""
echo "📁  [1/5] Creating remote directory..."
$SSH "mkdir -p $REMOTE_DIR"

# ── Step 2: Sync code ───────────────────────────────────────────────────────
echo ""
echo "📤  [2/5] Syncing code (rsync)..."
rsync -avz --progress \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.venv_tf' \
  --exclude 'node_modules' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '*.pcap' \
  --exclude 'LL MIT VNAT Dataset' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude 'pretrained_model.bin' \
  --exclude 'datasets' \
  --exclude 'ET-BERT-*' \
  "$PROJECT_ROOT/" "$USERNAME@$DROPLET_IP:$REMOTE_DIR/"

# ── Step 3: Copy .env ────────────────────────────────────────────────────────
echo ""
echo "🔐  [3/5] Uploading .env..."
$SCP "$PROJECT_ROOT/.env" "$USERNAME@$DROPLET_IP:$REMOTE_DIR/.env"

# ── Step 4: Install Docker on droplet (if needed) ────────────────────────────
echo ""
echo "🐋  [4/5] Ensuring Docker is installed on droplet..."
$SSH bash << 'REMOTE'
set -e
if ! command -v docker &> /dev/null; then
  echo "  → Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker "$USER" || true
  systemctl enable docker
  systemctl start docker
else
  echo "  ✓ Docker already installed: $(docker --version)"
fi

# Docker Compose plugin (v2)
if ! docker compose version &> /dev/null; then
  echo "  → Installing Docker Compose plugin..."
  apt-get install -y docker-compose-plugin
else
  echo "  ✓ Docker Compose already installed: $(docker compose version)"
fi
REMOTE

# ── Step 5: Build & launch containers ────────────────────────────────────────
echo ""
echo "🏗️   [5/5] Building and starting containers..."
$SSH bash << REMOTE
set -e
cd "$REMOTE_DIR"
docker compose pull redis 2>/dev/null || true
docker compose up -d --build --remove-orphans
echo ""
echo "⏳  Waiting for services to become healthy (up to 60s)..."
sleep 60
docker compose ps
echo ""
curl -s http://localhost/health && echo "" || echo "⚠️  Health check via curl failed — check logs: docker compose logs inference-api"
REMOTE

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅  Deployment complete!"
echo ""
echo "  Dashboard  →  http://$DROPLET_IP"
echo "  API Docs   →  http://$DROPLET_IP/api/docs"
echo "  Health     →  http://$DROPLET_IP/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
