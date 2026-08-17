#!/bin/bash
# VibeBar — удаление. Личные файлы (журнал, сводки, блокнот) не трогает.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
for n in clipwatch daily weekly; do
  P="$HOME/Library/LaunchAgents/com.vibebar.$n.plist"
  [ -f "$P" ] && { launchctl unload "$P" 2>/dev/null || true; rm -f "$P"; echo "  ✓ агент $n удалён"; }
done
PD="$(defaults read com.ameba.SwiftBar PluginDirectory 2>/dev/null || true)"
[ -n "$PD" ] && rm -f "$PD"/vibebar.*.sh && echo "  ✓ плагин отключён"
echo "  ! конфиг macrowhisper не трогал — резервные копии рядом с ~/.config/macrowhisper/"
echo "  ! журнал, сводки и блокнот остались на месте"
