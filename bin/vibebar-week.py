#!/usr/bin/env python3
# Недельная сводка: последние 7 дней, включая сегодня.
import sys, re, os, datetime
from collections import defaultdict

log = os.path.expanduser(sys.argv[1])
end = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.date.today()
days = [end - datetime.timedelta(days=i) for i in range(6, -1, -1)]
dayset = {d.isoformat() for d in days}

raw = defaultdict(list)
cur = None
if os.path.exists(log):
    for line in open(log, encoding="utf-8"):
        s = line.rstrip("\n")
        m = re.match(r"^##\s*(\d{4}-\d{2}-\d{2})\s*$", s)
        if m: cur = m.group(1); continue
        if cur in dayset and s.startswith("- "): raw[cur].append(s[2:])

per_day, totals, ideas, todos = {}, defaultdict(datetime.timedelta), [], []
for day, lines in raw.items():
    ev = []
    for s in lines:
        m = re.match(r"^(\d{2}):(\d{2})\s*·\s*(.*)$", s)
        if not m: continue
        t = datetime.datetime.strptime("%s %s:%s" % (day, m.group(1), m.group(2)), "%Y-%m-%d %H:%M")
        b = m.group(3).strip()
        hhmm = "%s:%s" % (m.group(1), m.group(2))
        if   b.startswith("💡"): ideas.append((day, hhmm, b[1:].strip()))
        elif b.startswith("❗"): todos.append((day, hhmm, b[1:].strip()))
        else: ev.append((t, b))
    ev.sort(key=lambda x: x[0])
    dtot = datetime.timedelta()
    for i, (t, b) in enumerate(ev):
        if i + 1 < len(ev): end_t = ev[i+1][0]
        elif day == datetime.date.today().isoformat(): end_t = datetime.datetime.now()
        else: continue                      # последняя запись прошлого дня без закрытия — не считаем
        if b.startswith("⏸"): continue
        d = end_t - t
        if d.total_seconds() <= 0: continue
        dtot += d
        totals[" ".join(b.split())] += d
    per_day[day] = dtot

def hm(d):
    m = int(d.total_seconds() // 60)
    return "%dч %02dм" % (m//60, m%60) if m >= 60 else "%dм" % m

week_total = sum(per_day.values(), datetime.timedelta())
RU = ["пн","вт","ср","чт","пт","сб","вс"]
out = ["## Неделя %s — %s" % (days[0].strftime("%d.%m"), days[-1].strftime("%d.%m.%Y")), ""]
out += ["**Итого за неделю: %s**" % hm(week_total), "", "| День | Дата | Учтено |", "|---|---|---|"]
for d in days:
    k = d.isoformat()
    out.append("| %s | %s | %s |" % (RU[d.weekday()], d.strftime("%d.%m"), hm(per_day.get(k, datetime.timedelta()))))

out += ["", "### На что ушло время", ""]
top = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:15]
if top:
    out += ["| Занятие | Всего | Доля |", "|---|---|---|"]
    for name, d in top:
        share = (d.total_seconds() / week_total.total_seconds() * 100) if week_total.total_seconds() else 0
        out.append("| %s | %s | %d%% |" % (name, hm(d), round(share)))
else:
    out.append("_записей нет_")

out += ["", "### Не забыть за неделю", ""]
out += (["- [ ] %s %s — %s" % (d[8:10]+"."+d[5:7], t, x) for d, t, x in sorted(todos)] or ["_пусто_"])
out += ["", "### Идеи за неделю", ""]
out += (["- %s %s — %s" % (d[8:10]+"."+d[5:7], t, x) for d, t, x in sorted(ideas)] or ["_пусто_"])
sys.stdout.write("\n".join(out) + "\n")
