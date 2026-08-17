#!/bin/bash
# Дописывает запись в журнал. Текст: аргументом или со stdin.
# Классификация по первому слову — на python3, чтобы не зависеть от локали и tr/awk с UTF-8.
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$BIN")"
[ -f "$ROOT/config.env" ] && . "$ROOT/config.env"
LOG="${VIBEBAR_FILE:-$HOME/vibebar-journal.md}"
TEXT="${1:-}"
if [ -z "$TEXT" ] && [ ! -t 0 ]; then TEXT="$(cat)"; fi
[ -z "$TEXT" ] && exit 0

"$BIN/vibebar-mark-dictation.sh" "$TEXT" 2>/dev/null || true

LOG="$LOG" python3 - "$TEXT" <<'PY'
import sys, os, re, datetime

text = sys.argv[1] if len(sys.argv) > 1 else ""
log  = os.path.expanduser(os.environ["LOG"])

text = re.sub(r"\s+", " ", text.replace("\n", " ").replace("\r", " ")).strip()
text = text.strip('"\'«»').strip()
text = re.sub(r"[.!]+$", "", text).strip()
if not text:
    raise SystemExit

IDEA  = {"идея", "идеи", "идею", "мысль", "мысли", "заметка", "заметку"}
TODO  = {"незабыть", "напомнить", "напоминание", "важно", "запомнить", "todo"}
PAUSE = {"перерыв", "пауза", "стоп", "конец", "финиш", "обед"}

first = re.split(r"[\s,.;:!?]+", text, 1)[0].lower().strip('"\'«».,:;!?')
rest  = text[len(text.split(" ", 1)[0]):].lstrip(" ,.:;—-").strip() if " " in text else ""

low = text.lower()
if low.startswith("не забыть") or low.startswith("не забудь"):
    kind, body = "todo", text.split(" ", 2)[2].lstrip(" ,.:;—-").strip() if len(text.split(" ")) > 2 else text
elif first in TODO:
    kind, body = "todo", (rest or text)
elif first in IDEA:
    kind, body = "idea", (rest or text)
elif first in PAUSE:
    kind, body = "stop", text
else:
    kind, body = "task", text
if not body:
    raise SystemExit

now = datetime.datetime.now()
day, hm = now.strftime("%Y-%m-%d"), now.strftime("%H:%M")

open(log, "a", encoding="utf-8").close()
content = open(log, encoding="utf-8").read()
with open(log, "a", encoding="utf-8") as f:
    if ("\n## %s\n" % day) not in ("\n" + content):
        f.write("\n## %s\n" % day)
    mark = {"idea": "💡 ", "todo": "❗ ", "stop": "⏸ ", "task": ""}[kind]
    f.write("- %s · %s%s\n" % (hm, mark, body))
print(kind, "|", body)
PY
