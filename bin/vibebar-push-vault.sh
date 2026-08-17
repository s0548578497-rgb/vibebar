#!/bin/bash
# Дописывает сводку за день (вместе с ручными правками) в заметку из VIBEBAR_VAULT_FILE.
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$BIN")"
[ -f "$ROOT/config.env" ] && . "$ROOT/config.env"
LOG="${VIBEBAR_FILE:-$HOME/vibebar-journal.md}"
DST="${VIBEBAR_VAULT_FILE:?не задан VIBEBAR_VAULT_FILE в config.env}"
DIR="${VIBEBAR_DIGEST_DIR:-$ROOT/digests}"
DAY="${1:-$(date +%Y-%m-%d)}"
mkdir -p "$DIR"
SRC="$DIR/$DAY.md"
[ -f "$SRC" ] || python3 "$BIN/vibebar-build.py" "$LOG" "$DAY" > "$SRC"

SRC="$SRC" DST="$DST" DAY="$DAY" python3 - <<'PY'
import os, re
src, dst, day = os.environ["SRC"], os.path.expanduser(os.environ["DST"]), os.environ["DAY"]
body = open(src, encoding="utf-8").read()
body = "\n".join(l for l in body.split("\n")
                 if not l.startswith("# Сводка за") and not l.startswith(">")).strip()
body = body.replace("\n## Идеи", "\n### Идеи").replace("\n## Не забыть", "\n### Не забыть")
cur = open(dst, encoding="utf-8").read()
if ("\n## %s\n" % day) in cur:
    print("сводка за %s уже перенесена — пропускаю" % day); raise SystemExit
open(dst, "a", encoding="utf-8").write("\n## %s\n\n%s\n" % (day, body))
cur = open(dst, encoding="utf-8").read()
open(dst, "w", encoding="utf-8").write(re.sub(r"^updated: .*$", "updated: " + day, cur, count=1, flags=re.M))
print("перенесено:", day)
PY
