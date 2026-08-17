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

OUT="$OUT" DST="$DST" python3 - <<'PY'
import os, re
src, dst = os.environ["OUT"], os.path.expanduser(os.environ["DST"])
body = open(src, encoding="utf-8").read().strip()
head = body.split("\n", 1)[0]
cur = open(dst, encoding="utf-8").read()
if head in cur:
    print("недельная сводка уже перенесена"); raise SystemExit
open(dst, "a", encoding="utf-8").write("\n" + body + "\n")
print("недельная сводка добавлена")
PY
echo "$OUT"
