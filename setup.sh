#!/usr/bin/env bash
# Zaya Agent — beginner-friendly one-command installer
# Run: bash setup.sh
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

ZAYA_DIR="$HOME/.zaya"
DATA_DIR="$HOME/.zaya/data"
mkdir -p "$ZAYA_DIR" "$DATA_DIR"

# ---- helpers ----
prompt() {
  local prompt="$1"
  local default="$2"
  read -r -p "$prompt [$default]: " input
  echo "${input:-$default}"
}

ask_nonempty() {
  local prompt="$1"
  local val=""
  while [[ -z "$val" ]]; do
    val=$(prompt "$prompt" "")
    if [[ -z "$val" ]]; then
      log_warn "This field is required."
    fi
  done
  echo "$val"
}

ask_toggle() {
  local prompt="$1"
  local default="${2:-y}"
  read -r -p "$prompt (y/N): " input
  : "${input:-$default}"
  [[ "$input" =~ ^[Yy]$ ]] && echo y || echo n
}

# ---- 1) Collect inputs ----
log_info "Let's set up the Zaya Agent pilot."

VPS_REGION=$(prompt "VPS provider region" "hostinger-europe")
CLIENT_ID=$(ask_nonempty "Client Telegram ID (e.g., 8461682030)")
OPENROUTER_KEY=$(ask_nonempty "OpenRouter API key")
BOT_TOKEN=$(ask_nonempty "Telegram bot token")
ACCEPTABLE_PRICE=$(prompt "Acceptable hourly price (optional)" "")

# ---- 2) Prerequisites ----
log_info "Checking prerequisites..."
MISSING_INSTALLER=false
if ! command -v docker &>/dev/null; then
  log_warn "Docker not found. We'll install it for you."
  MISSING_INSTALLER=true
fi
if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null; then
  log_warn "docker-compose (or docker compose) not found. We'll install it."
  MISSING_INSTALLER=true
fi

if $MISSING_INSTALLER; then
  echo ""
  log_info "We'll install Docker and docker-compose. This requires sudo."
  if [[ "$EUID" -ne 0 ]]; then
    read -r -p "Run installation commands with sudo now? (y/N): " run_sudo
    if [[ "$run_sudo" =~ ^[Yy]$ ]]; then
      sudo bash -c "
        apt-get update && apt-get install -y \
          ca-certificates curl gnupg lsb-release \
        && install -m 0755 -d /etc/apt/keyrings \
        && curl -fsSL https://download.docker.com/linux/\$(. /etc/os-release && echo \$ID)/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
        && echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/\$(. /etc/os-release && echo \$ID) \$(. /etc/os-release && echo \$VERSION_CODENAME) stable\" > /etc/apt/sources.list.d/docker.list \
        && apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin \
        && usermod -aG docker \$(whoami) && newgrp docker
      " || log_warn "Docker installation failed. Please install Docker and docker-compose manually."
    else
      log_warn "Skipping Docker install. Please install Docker and docker-compose manually to continue."
    fi
  else
    log_warn "Please install Docker and docker-compose manually, then re-run this script."
  fi
  echo ""
fi

# ---- 3) Optional DNS check ----
if ask_toggle "Check DNS resolution for $DOMAIN" "n"; then
  if command -v curl &>/dev/null; then
    IP=$(curl -s "http://ip-api.com/json/" | python3 -c "import sys,json; print(json.load(sys.stdin).get('query',''))" 2>/dev/null || echo "unknown")
    echo "Your public IP appears to be: $IP"
    RESOLVED=$(curl -s "http://$DOMAIN/" --max-time 5 -o /dev/null -w "%{http_code}" 2>/dev/null || echo "ERR")
    if [[ "$RESOLVED" == "000" ]]; then
      log_warn "Could not reach $DOMAIN. Make sure DNS points to this VPS."
    else
      log_info "$DOMAIN resolved and responded with HTTP $RESOLVED."
    fi
  else
    log_warn "curl not installed; skipping DNS check."
  fi
fi

# ---- 4) Write .env ----
cat > "$ZAYA_DIR/.env" << EOF
OPENROUTER_API_KEY=$OPENROUTER_KEY
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
DOMAIN=$DOMAIN
CLIENT_ID=$CLIENT_ID
ACCEPTABLE_PRICE=${ACCEPTABLE_PRICE:-}
EOF
chmod 600 "$ZAYA_DIR/.env"
log_info "Saved .env to $ZAYA_DIR/.env"

# ---- 5) Write docker-compose.yml ----
cat > "$ZAYA_DIR/docker-compose.yml" << EOF
version: "3.8"
services:
  zaya-engine:
    image: uzxia/zaya-engine:latest
    container_name: zaya-engine
    restart: unless-stopped
    env_file: $ZAYA_DIR/.env
    volumes:
      - $ZAYA_DIR/data:/opt/data
    command: gateway
EOF
log_info "Wrote docker-compose.yml to $ZAYA_DIR/docker-compose.yml"

# ---- 6) Write systemd unit ----
cat > /etc/systemd/system/zaya-engine.service << EOF
[Unit]
Description=Zaya Engine (pilot)
After=docker.service
Requires=docker.service

[Service]
Restart=always
RestartSec=5
EnvironmentFile=$ZAYA_DIR/.env
ExecStartPre=-/usr/bin/docker compose --project-name zaya-pilot -f $ZAYA_DIR/docker-compose.yml down
ExecStart=/usr/bin/docker compose --project-name zaya-pilot -f $ZAYA_DIR/docker-compose.yml up
ExecStopPost=-/usr/bin/docker compose --project-name zaya-pilot -f $ZAYA_DIR/docker-compose.yml down
WorkingDirectory=$ZAYA_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now zaya-engine
log_info "Service enabled and started."

# ---- 7) Verify ----
sleep 5
if curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/health" 2>/dev/null | grep -q "200\|301\|302\|404"; then
  log_info "Health check returned HTTP $(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/health" 2>/dev/null)."
else
  log_warn "Health endpoint not reachable yet. Check logs with: journalctl -u zaya-engine -f"
fi
log_info "Logs: journalctl -u zaya-engine -f"

# ---- 8) Final instructions ----
echo ""
echo "========================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "========================================"
echo "Share this one-liner with Jacoby:"
echo -e "${YELLOW}bash setup.sh${NC}"
echo ""
echo "Then verify:"
echo "  curl -sI http://$DOMAIN/health"
echo "  journalctl -u zaya-engine -f"
echo ""
echo "Next steps:"
echo "  - Set DNS for $DOMAIN to point to this VPS."
echo "  - Ensure OPENROUTER_API_KEY and TELEGRAM_BOT_TOKEN are valid."
echo "  - Allowlist client Telegram ID: $CLIENT_ID"
echo "========================================"
