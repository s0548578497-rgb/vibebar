#!/bin/bash
# Открывает сводку за день.
# Логика: если ты файл НЕ правил — он автоматически пересобирается из журнала.
#         если правил — правки сохраняются, автопересборки нет.
#         --rebuild — принудительно пересобрать, старое уходит в .bak
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$BIN")"
[ -f "$ROOT/config.env" ] && . "$ROOT/config.env"
LOG="${VIBEBAR_FILE:-$HOME/vibebar-journal.md}"
OPENER="${VIBEBAR_OPENER:-TextEdit}"
DIR="${VIBEBAR_DIGEST_DIR:-$ROOT/digests}"
DAY="$(date +%Y-%m-%d)"; REBUILD=0; NOOPEN=0
for a in "$@"; do
  case "$a" in
    --rebuild) REBUILD=1 ;;
    --no-open) NOOPEN=1 ;;
    [0-9]*)    DAY="$a" ;;
  esac
done
mkdir -p "$DIR"
OUT="$DIR/$DAY.md"; GEN="$DIR/.$DAY.gen"

NEW="$(python3 "$BIN/vibebar-build.py" "$LOG" "$DAY")"

write() { printf '%s\n' "$NEW" > "$OUT"; shasum -a 256 < "$OUT" | awk '{print $1}' > "$GEN"; }

if [ ! -f "$OUT" ]; then
  write
elif [ "$REBUILD" = "1" ]; then
  cp "$OUT" "$OUT.bak"; write
else
  CUR="$(shasum -a 256 < "$OUT" | awk '{print $1}')"
  OLD="$(cat "$GEN" 2>/dev/null || echo -)"
  # файл не правился руками, если его хеш совпадает с последним сгенерированным
  if [ "$CUR" = "$OLD" ]; then write; fi
fi

[ "$NOOPEN" = "1" ] || open -a "$OPENER" "$OUT" 2>/dev/null || open "$OUT"
echo "$OUT"
