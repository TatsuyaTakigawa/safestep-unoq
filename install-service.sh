#!/bin/bash
# Start SafeStep automatically at boot (systemd).
#   ./install-service.sh            install and start
#   ./install-service.sh remove     stop and remove
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
UNIT=/etc/systemd/system/safestep.service

if [ "${1:-}" = "remove" ]; then
    sudo systemctl disable --now safestep.service || true
    sudo rm -f "$UNIT"
    sudo systemctl daemon-reload
    echo "Removed."
    exit 0
fi

sudo tee "$UNIT" >/dev/null <<UNITEOF
[Unit]
Description=SafeStep AI (wrong-way detection on stairs)
After=network.target sound.target

[Service]
Type=simple
User=$USER
SupplementaryGroups=audio video
ExecStart=$DIR/run.sh run
SuccessExitStatus=143
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNITEOF

sudo systemctl daemon-reload
sudo systemctl enable --now safestep.service
echo "Installed. Log: journalctl -u safestep -f"
