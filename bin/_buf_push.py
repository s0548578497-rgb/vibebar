#!/usr/bin/env python3
# Читает текст со stdin, чистит терминальный мусор и кладёт в блокнот:
# без дублей, свежее в конец, с ограничением длины списка.
import sys, os, re, base64

CLEAN   = os.environ.get("VIBEBAR_CLEAN_TERMINAL", "1") == "1"
ANCHORS = ["--- OTVET NIZHE ---", "КОПИРОВАТЬ ОТСЮДА И НИЖЕ"]
PROMPT  = re.compile(os.environ.get(
    "VIBEBAR_PROMPT_RE",
    r"^\s*(?:🍏\s*)?[A-Za-z0-9._-]*-?iMac:\S*\s+[A-Za-z0-9._-]+\$\s?"))
CONT    = re.compile(r"^>\s?")

ECHO = re.compile(r"^echo\s")

def clean(text):
    lines = text.split("\n")

    # 1. Якорь считается только если он стоит ОТДЕЛЬНОЙ строкой — то есть это вывод
    #    терминала. Внутри `echo "--- OTVET NIZHE ---"` это ещё команда, её резать нельзя:
    #    иначе копия моего блока команд превращается в одну кавычку.
    cut = -1
    for i, l in enumerate(lines):
        t = l.strip()
        if ECHO.match(t):
            continue
        for a in ANCHORS:
            if t == a or (t.endswith(a) and not t.startswith("echo")):
                cut = i
    after_anchor = cut != -1
    if after_anchor:
        lines = lines[cut + 1:]

    out = []
    for line in lines:
        was_prompt = bool(PROMPT.match(line))
        line = PROMPT.sub("", line)
        line = CONT.sub("", line)
        line = line.rstrip()
        if was_prompt and not line:
            continue
        # после якоря всё набранное — это эхо моих же команд, суть только в выводе
        if after_anchor and (was_prompt or ECHO.match(line)):
            continue
        out.append(line)

    res, blank = [], 0
    for l in out:
        if l.strip():
            blank = 0; res.append(l)
        else:
            blank += 1
            if blank == 1: res.append("")
    body = "\n".join(res).strip()
    # Вывод терминала, вставленный в чат, часто начинается с "/" — поле ввода
    # принимает это за слэш-команду («Unknown skill: Users/…»). Оборачиваем в
    # блок кода: и команда не срабатывает, и текст читается как вывод.
    if after_anchor and body and os.environ.get("VIBEBAR_WRAP_CODE", "1") == "1":
        if "\n" in body or body.startswith("/"):
            body = "```\n" + body + "\n```"
    return body

raw = sys.stdin.buffer.read().rstrip(b"\r\n")
if not raw.strip():
    raise SystemExit
txt = raw.decode("utf-8", "replace")
if CLEAN:
    c = clean(txt)
    # страховка: если после чистки остался огрызок (одни кавычки, пара символов),
    # значит правило сработало не на том — сохраняем оригинал
    if len(c.strip()) >= 12 and re.search(r"\w", c):
        txt = c

buf = os.environ["BUF"]
mx  = int(os.environ.get("MAX", "15"))
enc = base64.b64encode(txt.encode("utf-8")).decode()
try:
    lines = [l.strip() for l in open(buf, encoding="utf-8").read().split("\n") if l.strip()]
except FileNotFoundError:
    lines = []
if enc in lines:
    lines.remove(enc)
lines.append(enc)
open(buf, "w", encoding="utf-8").write("\n".join(lines[-mx:]) + "\n")
