#!/bin/bash
# VibeBar — установка. Запускать из папки репозитория: ./install.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
say() { printf '\n\033[1m%s\033[0m\n' "$1"; }
ok()  { printf '  ✓ %s\n' "$1"; }
warn(){ printf '  ! %s\n' "$1"; }

say "1. Проверка окружения"
command -v python3 >/dev/null || { echo "нужен python3"; exit 1; }; ok "python3 $(python3 -V 2>&1 | awk '{print $2}')"
[ -d /Applications/SwiftBar.app ] || warn "SwiftBar не найден — поставьте: brew install --cask swiftbar"
[ -d /Applications/superwhisper.app ] || warn "superwhisper не найден — голосовая часть работать не будет"
command -v macrowhisper >/dev/null || warn "macrowhisper не найден — поставьте: brew install ognistik/formulae/macrowhisper"

say "2. Конфиг"
if [ -f "$ROOT/config.env" ]; then ok "config.env уже есть, не трогаю"
else sed "s|__ROOT__|$ROOT|g" "$ROOT/config.env.example" > "$ROOT/config.env"; ok "создан config.env"; fi
# shellcheck disable=SC1091
. "$ROOT/config.env"

say "3. Плагин SwiftBar"
REFRESH="${1:-3s}"
PLUG="$ROOT/swiftbar/vibebar.$REFRESH.sh"
# битый или самоссылающийся симлинк от прежних запусков — убрать, иначе sed упадёт с ELOOP
[ -L "$PLUG" ] && rm -f "$PLUG"
sed "s|__ROOT__|$ROOT|g" "$ROOT/swiftbar/vibebar.3s.sh.template" > "$PLUG"
chmod +x "$PLUG"
PD="$(defaults read com.ameba.SwiftBar PluginDirectory 2>/dev/null || true)"
PD="${PD/#\~/$HOME}"
if [ -z "$PD" ] || [ ! -d "$PD" ]; then
  warn "папка плагинов SwiftBar не настроена. Создайте ОТДЕЛЬНУЮ папку и укажите её в SwiftBar → Preferences → Plugin Folder:"
  warn "    mkdir -p \"\$HOME/.swiftbar-plugins\""
  warn "    НЕ указывайте $ROOT/swiftbar — туда пишет сам установщик"
elif [ "$(cd "$PD" 2>/dev/null && pwd -P)" = "$(cd "$ROOT/swiftbar" && pwd -P)" ]; then
  ok "плагин на месте: $PLUG"
  warn "папка плагинов SwiftBar совпадает с $ROOT/swiftbar — симлинк не создаю (иначе плагин затрётся ссылкой на себя)"
  warn "рекомендуется вынести папку плагинов отдельно: \$HOME/.swiftbar-plugins"
else
  ln -sf "$PLUG" "$PD/vibebar.$REFRESH.sh"; ok "плагин подключён: $PD"
fi

say "4. Фоновые агенты"
mkdir -p "$HOME/Library/LaunchAgents"
DAILY_HOUR="${VIBEBAR_DAILY_HOUR:-22}"
for n in clipwatch daily weekly; do
  [ "$n" != "clipwatch" ] && [ -z "${VIBEBAR_VAULT_FILE:-}" ] && { warn "$n пропущен: VIBEBAR_VAULT_FILE не задан"; continue; }
  P="$ROOT/launchd/$n.plist"
  sed -e "s|__ROOT__|$ROOT|g" -e "s|__DAILY_HOUR__|$DAILY_HOUR|g" "$ROOT/launchd/$n.plist.template" > "$P"
  cp "$P" "$HOME/Library/LaunchAgents/com.vibebar.$n.plist"
  launchctl unload "$HOME/Library/LaunchAgents/com.vibebar.$n.plist" 2>/dev/null || true
  launchctl load  "$HOME/Library/LaunchAgents/com.vibebar.$n.plist" 2>/dev/null || \
    launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.vibebar.$n.plist" 2>/dev/null || true
  ok "агент com.vibebar.$n"
done

say "5. macrowhisper"
MW="$HOME/.config/macrowhisper/macrowhisper.json"
if [ -f "$MW" ]; then
  cp "$MW" "$MW.bak.$(date +%s)"
  ROOT="$ROOT" MODE="${VIBEBAR_MODE_NAME:-Journal}" python3 - "$MW" <<'PY'
import json, sys, os, collections
p = sys.argv[1]; root = os.environ["ROOT"]; mode = os.environ["MODE"]
cfg = json.load(open(p, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
def action(name, script, modes):
    return collections.OrderedDict([
        ("action", '%s/bin/%s "{{swResult}}"' % (root, script)),
        ("actionDelay", None), ("icon", "📝"), ("moveTo", None), ("nextAction", None),
        ("restoreClipboard", None), ("scriptAsync", True), ("scriptWaitTimeout", None),
        ("triggerApps", None), ("triggerLogic", "or"), ("triggerModes", modes),
        ("triggerUrls", None), ("triggerVoice", None)])
cfg.setdefault("scriptsShell", collections.OrderedDict())
cfg["scriptsShell"]["vibebar"]   = action("vibebar", "vibebar-add.sh", mode)
cfg["scriptsShell"]["dictation"] = action("dictation", "vibebar-mark-dictation.sh", None)
cfg["defaults"]["activeAction"]  = "dictation"
json.dump(cfg, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("  ✓ конфиг macrowhisper обновлён (резервная копия рядом)")
PY
  macrowhisper --restart-service >/dev/null 2>&1 || warn "не удалось перезапустить сервис macrowhisper"
else
  warn "конфиг macrowhisper не найден — запустите 'macrowhisper --start-service' и повторите установку"
fi

say "6. Режим superwhisper"
MODE_NAME="${VIBEBAR_MODE_NAME:-Journal}"
SW_MODES="${VIBEBAR_SW_MODES_DIR:-$HOME/Documents/superwhisper/modes}"
if [ -d "$SW_MODES" ]; then
  if MODE="$MODE_NAME" DIR="$SW_MODES" python3 - <<'PY'
import json, os, glob, sys
mode = os.environ["MODE"]; names = []
for f in sorted(glob.glob(os.path.join(os.environ["DIR"], "*.json"))):
    try:
        n = json.load(open(f, encoding="utf-8")).get("name", "")
        if n: names.append(n)
    except Exception:
        pass
sys.exit(0 if mode in names else 1)
PY
  then
    ok "режим «${MODE_NAME}» найден"
  else
    warn "режим «${MODE_NAME}» в superwhisper НЕ найден — записи в журнал не появятся"
    warn "есть режимы: $(DIR="$SW_MODES" python3 -c 'import json,os,glob;print(", ".join(sorted(json.load(open(f,encoding="utf-8")).get("name","") for f in glob.glob(os.path.join(os.environ["DIR"],"*.json")))))' 2>/dev/null)"
    warn "либо переименуйте режим в «${MODE_NAME}», либо задайте своё имя в config.env → VIBEBAR_MODE_NAME"
  fi
else
  warn "папка режимов superwhisper не найдена ($SW_MODES) — имя режима не проверено"
fi

say "Готово. Осталось руками:"
cat <<TXT
  1. superwhisper → Settings → Modes → создайте режим «${VIBEBAR_MODE_NAME:-Journal}»,
     Auto paste = Off, назначьте горячую клавишу.
     В остальных режимах Auto paste оставьте On.
  2. Для автовставки из блокнота: Системные настройки → Конфиденциальность →
     Универсальный доступ → добавьте SwiftBar.
  3. SwiftBar → Refresh All.
TXT
