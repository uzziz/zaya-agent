#!/usr/bin/env bash
# Zaya Agent — beginner-friendly one-command installer
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
  local prompt_text="$1"
  local default="$2"
  read -r -p "$prompt_text [$default]: " input
  echo "${input:-$default}"
}

ask_nonempty() {
  local prompt_text="$1"
  local val=""
  while [[ -z "$val" ]]; do
    read -r -p "$prompt_text: " val
    if [[ -z "$val" ]]; then
      log_warn "This field is required."
    fi
  done
  echo "$val"
}

# ---- 1) Collect inputs ----
log_info "Let's set up Zaya Agent on your VPS."

VPS_REGION=$(prompt "VPS provider region" "hostinger-europe")
CLIENT_ID=$(ask_nonempty "Client Telegram ID (get it from https://t.me/userinfobot)")
OPENROUTER_KEY=$(ask_nonempty "OpenRouter API key")
BOT_TOKEN=$(ask_nonempty "Telegram bot token (from @BotFather)")
ACCEPTABLE_PRICE=$(prompt "Acceptable hourly price" "")

# ---- 2) Prerequisites ----
log_info "Checking prerequisites..."
MISSING_INSTALLER=false
if ! command -v docker &>/dev/null; then
  log_warn "Docker not found. Installing now..."
  MISSING_INSTALLER=true
fi
if ! command -v docker compose &>/dev/null; then
  log_warn "docker compose not found. Installing Docker..."
  MISSING_INSTALLER=true
fi

if $MISSING_INSTALLER; then
  echo ""
  log_info "Installing Docker. This requires sudo."
  if [[ "$EUID" -ne 0 ]]; then
    read -r -p "Run with sudo? (y/N): " run_sudo
    if [[ "$run_sudo" =~ ^[Yy]$ ]]; then
      sudo bash -c "
        apt-get update && apt-get install -y ca-certificates curl gnupg lsb-release
        && install -m 0755 -d /etc/apt/keyrings
        && curl -fsSL https://download.docker.com/linux/\$(. /etc/os-release && echo \$ID)/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        && echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/\$(. /etc/os-release && echo \$ID) \$(. /etc/os-release && echo \$VERSION_CODENAME) stable\" > /etc/apt/sources.list.d/docker.list
        && apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
      " || log_warn "Docker installation failed. Please install Docker manually."
    fi
  else
    apt-get update && apt-get install -y ca-certificates curl gnupg lsb-release
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo $ID)/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release && echo $ID) $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  fi
  echo ""
fi

# ---- 3) Write .env ----
cat > "$ZAYA_DIR/.env" << EOF
OPENROUTER_API_KEY=$OPENROUTER_KEY
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
CLIENT_ID=$CLIENT_ID
ACCEPTABLE_PRICE=${ACCEPTABLE_PRICE:-}
EOF
chmod 600 "$ZAYA_DIR/.env"
log_info "Saved .env to $ZAYA_DIR/.env"

# ---- 4) Write docker-compose.yml ----
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

# ---- 5) Write systemd unit ----
cat > /etc/systemd/system/zaya-engine.service << EOF
[Unit]
Description=Zaya Agent Engine
After=docker.service
Requires=docker.service

[Service]
Restart=always
RestartSec=5
EnvironmentFile=$ZAYA_DIR/.env
ExecStartPre=-/usr/bin/docker compose --project-name zaya -f $ZAYA_DIR/docker-compose.yml down
ExecStart=/usr/bin/docker compose --project-name zaya -f $ZAYA_DIR/docker-compose.yml up
ExecStopPost=-/usr/bin/docker compose --project-name zaya -f $ZAYA_DIR/docker-compose.yml down
WorkingDirectory=$ZAYA_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now zaya-engine
log_info "Service enabled and started."

# ---- 6) Verify ----
sleep 5
log_info "Checking service status..."
if systemctl is-active --quiet zaya-engine; then
  log_info "Zaya Agent is running!"
else
  log_warn "Service may not have started. Check logs with: journalctl -u zaya-engine -f"
fi

echo ""
echo "========================================"
echo -e "${GREEN}Setup complete!${NC}"
echo "========================================"
echo ""
echo "Check logs:"
echo "  journalctl -u zaya-engine -f"
echo ""
echo "Test your bot on Telegram — send it a message."
echo "========================================"
