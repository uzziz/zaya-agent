#!/usr/bin/env bash
set -euo pipefail
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
ZAYA_DIR="$HOME/.zaya"
mkdir -p "$ZAYA_DIR" "$ZAYA_DIR/data"
prompt() { local p="$1"; local d="$2"; read -r -p "$p [$d]: " i; echo "${i:-$d}"; }
ask_nonempty() { local p="$1"; local v=""; while [[ -z "$v" ]]; do read -r -p "$p: " v; [[ -z "$v" ]] && log_warn "required"; done; echo "$v"; }
log_info "Zaya Agent setup"
VPS_REGION=$(prompt "VPS region" "hostinger-europe")
CLIENT_ID=$(ask_nonempty "Client Telegram ID (https://t.me/userinfobot)")
OPENROUTER_KEY=$(ask_nonempty "OpenRouter API key")
BOT_TOKEN=$(ask_nonempty "Bot token (from @BotFather, format: 123456789:ABC...)")
ACCEPTABLE_PRICE=$(prompt "Hourly price" "")

MISSING_INSTALLER=false
command -v docker &>/dev/null || MISSING_INSTALLER=true
command -v docker compose &>/dev/null || MISSING_INSTALLER=true

if $MISSING_INSTALLER; then
  log_info "Installing Docker..."
  if [[ "$EUID" -ne 0 ]]; then
    read -r -p "Run sudo? (y/N): " r
    [[ "$r" =~ ^[Yy]$ ]] || { log_warn "Docker install skipped"; MISSING_INSTALLER=false; }
  fi
  if $MISSING_INSTALLER; then
    sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin || log_warn "Docker install failed"
  fi
fi

cat > "$ZAYA_DIR/.env" << ENVEOF
OPENROUTER_API_KEY=$OPENROUTER_KEY
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_ALLOWED_USERS=$CLIENT_ID
GATEWAY_ALLOWED_USERS=$CLIENT_ID
ACCEPTABLE_PRICE=${ACCEPTABLE_PRICE:-}
ENVEOF
chmod 600 "$ZAYA_DIR/.env"

cat > "$ZAYA_DIR/docker-compose.yml" << 'COMPOSEEOF'
version: "3.8"
services:
  zaya-engine:
    image: uzxia/zaya-engine:latest
    container_name: zaya-engine
    restart: unless-stopped
    env_file: /root/.zaya/.env
    volumes:
      - /root/.zaya/data:/opt/data
    command: ["gateway", "run"]
COMPOSEEOF

cat > /etc/systemd/system/zaya-engine.service << SERVICEEOF
[Unit]
Description=Zaya Agent Engine
After=docker.service
Requires=docker.service
[Service]
Restart=always
RestartSec=5
EnvironmentFile=/root/.zaya/.env
ExecStartPre=-/usr/bin/docker compose -f /root/.zaya/docker-compose.yml down
ExecStart=/usr/bin/docker compose -f /root/.zaya/docker-compose.yml up
ExecStopPost=-/usr/bin/docker compose -f /root/.zaya/docker-compose.yml down
WorkingDirectory=/root/.zaya
[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable --now zaya-engine
log_info "Started. Check: journalctl -u zaya-engine -f"
log_info "Test your bot on Telegram."
