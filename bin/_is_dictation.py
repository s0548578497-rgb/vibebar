#!/usr/bin/env python3
# Код 0 — текст из stdin надиктован через superwhisper, в блокнот его не берём.
import sys, os, glob, json, time, hashlib

def norm(t):
    return " ".join(t.split()).strip().strip('"«»').rstrip(".!?…").lower()

txt = sys.stdin.buffer.read().decode("utf-8", "replace")
if not txt.strip():
    sys.exit(1)
n = norm(txt)
h = hashlib.sha256(n.encode()).hexdigest()

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
marks = os.path.join(root, ".dictations")
try:
    if h in open(marks, encoding="utf-8").read().split():
        sys.exit(0)
except FileNotFoundError:
    pass

# запасной путь: свежие meta.json superwhisper (может быть закрыт правами на ~/Documents)
window = float(os.environ.get("VIBEBAR_DICTATION_WINDOW", "180"))
now = time.time()
rec = os.path.expanduser(os.environ.get("SW_RECORDINGS", "~/Documents/superwhisper/recordings"))
try:
    files = glob.glob(os.path.join(rec, "*", "meta.json"))
except Exception:
    files = []
for f in files:
    try:
        if now - os.path.getmtime(f) > window: continue
        j = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    for k in ("result", "rawResult"):
        v = j.get(k) or ""
        if v.strip() and norm(v) == n:
            sys.exit(0)
sys.exit(1)
