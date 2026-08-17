#!/bin/bash
# Транзитный блокнот между окнами.
#   add      — взять текущий буфер обмена и положить в список
#   copy N   — положить N-ю запись обратно в буфер обмена (+ автовставка, если включена)
#   del N    — удалить N-ю запись
#   clear    — очистить всё
set -euo pipefail
export PATH="/usr/bin:/bin:/usr/sbin:/opt/homebrew/bin:${PATH:-}"
# без этого pbpaste отдаёт кириллицу как "?" — у него своя кодировка по умолчанию
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-$LANG}"
export __CF_USER_TEXT_ENCODING="${__CF_USER_TEXT_ENCODING:-0x$(printf '%X' "$(id -u)"):0x8000100:0x8000100}"

BIN="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$BIN")"
[ -f "$ROOT/config.env" ] && . "$ROOT/config.env"
BUF="${VIBEBAR_BUFFER:=$ROOT/clipboard.txt}"
LOGF="$ROOT/buf.log"
PBCOPY="${PBCOPY:-pbcopy}"; PBPASTE="${PBPASTE:-pbpaste}"
touch "$BUF"; chmod 600 "$BUF"
exec 2>>"$LOGF"

case "${1:-list}" in
  add)
    T="$($PBPASTE 2>/dev/null || true)"
    [ -z "$T" ] && exit 0
    printf '%s' "$T" | BUF="$BUF" MAX="${VIBEBAR_BUFFER_MAX:-15}" VIBEBAR_CLEAN_TERMINAL="${VIBEBAR_CLEAN_TERMINAL:-1}" python3 "$BIN/_buf_push.py"
    ;;
  copy)
    N="${2:?нужен номер}"
    sed -n "${N}p" "$BUF" | python3 -c 'import sys,base64
sys.stdout.buffer.write(base64.b64decode(sys.stdin.read().strip()))' | $PBCOPY
    if [ "${VIBEBAR_AUTOPASTE:-0}" = "1" ]; then
      # меню SwiftBar закрывается не мгновенно: пока фокус не вернулся в твоё окно,
      # нажатие ⌘V уходит в пустоту. Задержка настраивается в config.env
      sleep "${VIBEBAR_PASTE_DELAY:-0.8}"
      FRONT="$(osascript -e 'tell application "System Events" to name of first application process whose frontmost is true' 2>&1 || echo "?")"
      CLIP="$($PBPASTE 2>/dev/null | head -c 40 || true)"
      echo "$(date '+%F %T') front=[$FRONT] clip=[$CLIP]" >&2
      # key code 9 = клавиша V. keystroke "v" ломается при активной русской раскладке,
      # key code от раскладки не зависит
      if osascript -e 'tell application "System Events" to key code 9 using command down' >/dev/null 2>>"$LOGF"; then
        echo "$(date '+%F %T') key code 9 ok" >&2
      else
        echo "$(date '+%F %T') key code 9 FAILED" >&2
      fi
    fi
    ;;
  del)
    N="${2:?нужен номер}"
    python3 - "$BUF" "$N" <<'PY'
import sys
p, n = sys.argv[1], int(sys.argv[2])
ls = [l for l in open(p, encoding="utf-8").read().split("\n") if l.strip()]
if 1 <= n <= len(ls): ls.pop(n-1)
open(p, "w", encoding="utf-8").write("\n".join(ls) + ("\n" if ls else ""))
PY
    ;;
  show)
    N="${2:?нужен номер}"
    OUT="/tmp/vibebar-запись-$N.txt"
    sed -n "${N}p" "$BUF" | python3 -c 'import sys,base64
sys.stdout.buffer.write(base64.b64decode(sys.stdin.read().strip()))' > "$OUT"
    open -a "${VIBEBAR_OPENER:-TextEdit}" "$OUT" 2>/dev/null || open "$OUT"
    ;;
  clear) : > "$BUF" ;;
  list)  cat -n "$BUF" ;;
esac
