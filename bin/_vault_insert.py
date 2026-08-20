#!/usr/bin/env python3
# Вставляет блок в заметку так, чтобы свежие записи были сверху.
# Ищет маркер <!-- vibebar:insert -->; если его нет — вставляет перед первым "## ";
# если и его нет — дописывает в конец. Повтор по строке-ключу пропускается.
# Использование: _vault_insert.py <файл> <ключ-дубликата>   (блок читается со stdin)
import sys, os, re

dst = os.path.expanduser(sys.argv[1])
dup = sys.argv[2]
block = sys.stdin.read().strip("\n")
if not block.strip():
    print("пустой блок — нечего вставлять"); raise SystemExit

cur = open(dst, encoding="utf-8").read()
if dup and dup in cur:
    print("уже перенесено — пропускаю"); raise SystemExit

MARK = "<!-- vibebar:insert -->"
if MARK in cur:
    i = cur.index(MARK) + len(MARK)
    rest = cur[i:].lstrip("\n")
    new = cur[:i] + "\n\n" + block + "\n\n" + rest
else:
    m = re.search(r"^## ", cur, flags=re.M)
    if m:
        new = cur[:m.start()] + block + "\n\n" + cur[m.start():]
    else:
        new = cur.rstrip("\n") + "\n\n" + block + "\n"

new = re.sub(r"^updated: .*$", "updated: " + os.environ.get("VIBEBAR_DAY", ""), new, count=1, flags=re.M) \
      if os.environ.get("VIBEBAR_DAY") else new
open(dst, "w", encoding="utf-8").write(new)
print("вставлено сверху")
