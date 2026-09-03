#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
VENV="$ROOT/.venv-macos"
MODEL_DIR="$HOME/Library/Application Support/VibeBar/models"
AGENT="$HOME/Library/LaunchAgents/com.vibebar.localvoice.plist"
ABSENCE_AGENT="$HOME/Library/LaunchAgents/com.vibebar.absence.plist"

"$ROOT/install.sh"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$ROOT/macos/requirements.txt"
"$ROOT/macos/setup-whisper.sh"
"$ROOT/macos/native/build.sh"
mkdir -p "$MODEL_DIR" "$(dirname "$AGENT")"
VIBEBAR_MODEL_DIR="$MODEL_DIR" PYTHONPATH="$ROOT" "$VENV/bin/python" -m vibebar_voice.setup_assets
sed -e "s|__ROOT__|$ROOT|g" -e "s|__PYTHON__|$VENV/bin/python|g" \
  "$ROOT/macos/launchd/voice.plist.template" > "$AGENT"
launchctl bootout "gui/$(id -u)/com.vibebar.localvoice" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$AGENT"

source "$ROOT/config.env"
if [ -n "${VIBEBAR_BLUETOOTH_DEVICE:-}" ]; then
  sed -e "s|__ROOT__|$ROOT|g" -e "s|__PYTHON__|$VENV/bin/python|g" \
    -e "s|__DEVICE__|$VIBEBAR_BLUETOOTH_DEVICE|g" \
    "$ROOT/macos/launchd/absence.plist.template" > "$ABSENCE_AGENT"
  launchctl bootout "gui/$(id -u)/com.vibebar.absence" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$ABSENCE_AGENT"
fi

echo "VibeBar modular macOS installed. Allow Microphone and Accessibility for Python when prompted."
