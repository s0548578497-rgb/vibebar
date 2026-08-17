#!/bin/bash
# Печатает текущую задачу и сколько она идёт. Одна строка.
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$BIN")"
[ -f "$ROOT/config.env" ] && . "$ROOT/config.env"
LOG="${VIBEBAR_FILE:-$HOME/vibebar-journal.md}"
[ -f "$LOG" ] || { echo "журнал пуст"; exit 0; }

python3 - "$LOG" <<'PY'
import sys, re, datetime
log = sys.argv[1]
day = datetime.date.today().strftime("%Y-%m-%d")
inday, last = False, None
for raw in open(log, encoding="utf-8"):
    s = raw.rstrip("\n")
    if s.strip() == f"## {day}": inday = True; continue
    if s.startswith("## "): inday = False
    if inday and s.startswith("- "):
        m = re.match(r"^- (\d{2}):(\d{2}) · (.*)$", s)
        if m and m.group(3)[:1] not in ("💡", "❗"):
            last = m
if not last:
    print("сегодня записей нет"); raise SystemExit
body = last.group(3)
if body.startswith("⏸"):
    print("пауза"); raise SystemExit
start = datetime.datetime.strptime(f"{day} {last.group(1)}:{last.group(2)}", "%Y-%m-%d %H:%M")
m = max(0, int((datetime.datetime.now() - start).total_seconds() // 60))
print(f"{body} · {m//60}ч {m%60:02d}м" if m >= 60 else f"{body} · {m}м")
PY
