#!/bin/bash
# Строит недельную сводку и дописывает её в заметку из VIBEBAR_VAULT_FILE.
# Использование: vibebar-week.sh [YYYY-MM-DD]
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$BIN")"
[ -f "$ROOT/config.env" ] && . "$ROOT/config.env"
LOG="${VIBEBAR_FILE:-$HOME/vibebar-journal.md}"
DST="${VIBEBAR_VAULT_FILE:?не задан VIBEBAR_VAULT_FILE}"
DIR="${VIBEBAR_DIGEST_DIR:-$ROOT/digests}"
END="${1:-$(date +%Y-%m-%d)}"
mkdir -p "$DIR"
OUT="$DIR/неделя-$END.md"
python3 "$BIN/vibebar-week.py" "$LOG" "$END" > "$OUT"

HEAD="$(head -1 "$OUT")"
cat "$OUT" | python3 "$BIN/_vault_insert.py" "$DST" "$HEAD"
echo "$OUT"
