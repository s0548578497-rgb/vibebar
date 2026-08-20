#!/usr/bin/env python3
# Собирает текст свода за день из журнала. Печатает в stdout. Ничего не пишет.
import sys, re, datetime, os

log = os.path.expanduser(sys.argv[1])
day = sys.argv[2]

lines, inday = [], False
if os.path.exists(log):
    for raw in open(log, encoding="utf-8"):
        s = raw.rstrip("\n")
        if s.strip() == "## " + day: inday = True; continue
        if s.startswith("## "): inday = False
        if inday and s.startswith("- "): lines.append(s[2:])

ideas, todos, ev = [], [], []
for s in lines:
    m = re.match(r"^(\d{2}):(\d{2})\s*·\s*(.*)$", s)
    if not m: continue
    t = datetime.datetime.strptime("%s %s:%s" % (day, m.group(1), m.group(2)), "%Y-%m-%d %H:%M")
    b = m.group(3).strip()
    if b.startswith("💡"): ideas.append((t, b[1:].strip()))
    elif b.startswith("❗"): todos.append((t, b[1:].strip()))
    else: ev.append((t, b))

ev.sort(key=lambda x: x[0])
rows, total = [], datetime.timedelta()
for i, (t, b) in enumerate(ev):
    if i + 1 < len(ev):
        end = ev[i+1][0]
    elif day == datetime.date.today().isoformat():
        end = datetime.datetime.now()          # текущая задача идёт прямо сейчас
    else:
        continue                                # прошлый день, последняя запись не закрыта — не считаем
    if b.startswith("⏸"): continue
    d = end - t
    if d.total_seconds() <= 0: continue
    rows.append((t, end, b, d)); total += d

def hm(d):
    m = int(d.total_seconds() // 60)
    return "%dч %02dм" % (m//60, m%60) if m >= 60 else "%dм" % m

out = ["# Сводка за %s" % day, "",
       "> Этот файл можно править руками. Повторное открытие правки сохраняет.",
       "> Пересобрать из журнала — пункт «Пересобрать свод» (правки будут сохранены в .bak).", "",
       "| Начало | Конец | Длит. | Чем занимался |", "|---|---|---|---|"]
out += ["| %s | %s | %s | %s |" % (t.strftime("%H:%M"), e.strftime("%H:%M"), hm(d), b) for t, e, b, d in rows]
out += ["", "**Итого учтено: %s** · записей: %d" % (hm(total), len(rows))]
out += ["", "## Не забыть", ""]
out += (["- [ ] %s — %s" % (t.strftime("%H:%M"), x) for t, x in todos] or ["_за день ничего не отмечено_"])
out += ["", "## Идеи", ""]
out += (["- %s — %s" % (t.strftime("%H:%M"), x) for t, x in ideas] or ["_за день ничего не отмечено_"])
sys.stdout.write("\n".join(out) + "\n")
