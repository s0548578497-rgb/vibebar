#!/usr/bin/env bash
set -euo pipefail

UID_VALUE="$(id -u)"
for label in com.vibebar.localvoice com.vibebar.absence; do
  launchctl bootout "gui/$UID_VALUE/$label" 2>/dev/null || true
  rm -f "$HOME/Library/LaunchAgents/$label.plist"
done

echo "VibeBar modular services removed. Journal, settings, models and repository were preserved."
