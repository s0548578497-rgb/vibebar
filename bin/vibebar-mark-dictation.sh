#!/bin/bash
# Помечает расшифровку superwhisper и, если наблюдатель успел её утащить,
# вычищает её из блокнота задним числом.
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$BIN")"
[ -f "$ROOT/config.env" ] && . "$ROOT/config.env"
BUF="${VIBEBAR_BUFFER:=$ROOT/clipboard.txt}"
T="${1:-}"
[ -z "$T" ] && [ ! -t 0 ] && T="$(cat)"
[ -z "${T//[[:space:]]/}" ] && exit 0

printf '%s' "$T" | MARKS="$ROOT/.dictations" BUF="$BUF" LOGF="$ROOT/clip.log" python3 -c '
import sys, os, base64, hashlib, datetime

def norm(t):
    return " ".join(t.split()).strip().strip("\"«»").rstrip(".!?…").lower()

txt   = sys.stdin.buffer.read().decode("utf-8", "replace")
marks = os.environ["MARKS"]; buf = os.environ["BUF"]; logf = os.environ["LOGF"]
h = hashlib.sha256(norm(txt).encode()).hexdigest()

# 1. метка на будущее
try:    old = open(marks, encoding="utf-8").read().split()
except FileNotFoundError: old = []
old.append(h)
open(marks, "w", encoding="utf-8").write("\n".join(old[-80:]) + "\n")

# 2. если запись уже просочилась в блокнот — убрать
try:    lines = [l.strip() for l in open(buf, encoding="utf-8").read().split("\n") if l.strip()]
except FileNotFoundError: lines = []
keep, removed = [], 0
for l in lines:
    try: t = base64.b64decode(l).decode("utf-8", "replace")
    except Exception: keep.append(l); continue
    if hashlib.sha256(norm(t).encode()).hexdigest() == h: removed += 1
    else: keep.append(l)
if removed:
    open(buf, "w", encoding="utf-8").write("\n".join(keep) + ("\n" if keep else ""))
    with open(logf, "a", encoding="utf-8") as f:
        f.write("%s убрал диктовку из блокнота: %s\n"
                % (datetime.datetime.now().strftime("%F %T"), " ".join(txt.split())[:40]))
'
