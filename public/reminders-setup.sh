#!/bin/bash
# Vault Reminders Sidecar — auto-setup for macOS
# Run this on any Mac to connect Apple Reminders to Vault.
#
# Usage: curl -fsSL http://YOUR-VAULT-HOST/reminders-setup.sh | bash

set -e

INSTALL_DIR="$HOME/.vault-reminders"
VAULT_HOST="${VAULT_REMINDERS_HOST:-http://localhost:5175}"
PLIST_LABEL="com.vault.reminders-sidecar"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"

echo "=== Vault Reminders Sidecar Setup ==="
echo ""

# Create install directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download files from Vault server
echo "[1/4] Downloading sidecar files..."
curl -fsSL "$VAULT_HOST/reminders-helper.swift" -o reminders-helper.swift
curl -fsSL "$VAULT_HOST/reminders-server.py" -o reminders-server.py

# Compile Swift helper
echo "[2/4] Compiling Swift helper (this may take a moment)..."
swiftc -O reminders-helper.swift -o reminders-helper 2>/dev/null || {
  echo "ERROR: Swift compiler not found. Install Xcode Command Line Tools:"
  echo "  xcode-select --install"
  exit 1
}

# Test it (will trigger macOS Reminders permission dialog)
echo "[3/4] Testing Apple Reminders access..."
echo "  (If prompted, click 'Allow' to grant Reminders access)"
./reminders-helper lists > /dev/null 2>&1 || true

# Create launchd plist for auto-start
echo "[4/4] Setting up auto-start..."
cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$INSTALL_DIR/reminders-server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/sidecar.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/sidecar.log</string>
</dict>
</plist>
PLIST

# Start the service
launchctl bootout gui/$(id -u) "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap gui/$(id -u) "$PLIST_PATH"

echo ""
echo "=== Done! ==="
echo "Reminders sidecar running on http://localhost:5177"
echo "It will auto-start on login."
echo ""
echo "Refresh Vault and click 'Conectar Apple Reminders'."
