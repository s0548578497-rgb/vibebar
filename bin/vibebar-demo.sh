#!/bin/bash
# Демо-режим для скриншотов: подменяет журнал и блокнот нейтральными примерами.
# vibebar-demo.sh on|off
set -euo pipefail
BIN="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$BIN")"
C="$ROOT/config.env"; B="$ROOT/config.env.real"; D="$ROOT/demo"

case "${1:-}" in
  on)
    [ -f "$B" ] || cp "$C" "$B"
    mkdir -p "$D"
    python3 - "$D" <<'PY'
import sys, datetime, base64, os
d = sys.argv[1]; now = datetime.datetime.now()
def t(m): return (now - datetime.timedelta(minutes=m)).strftime("%H:%M")
open(os.path.join(d, "journal.md"), "w", encoding="utf-8").write("\n".join([
 "", "## " + now.strftime("%Y-%m-%d"),
 "- %s · Разбираю архитектуру платежей" % t(212),
 "- %s · 💡 Вынести конфиг в отдельный файл" % t(168),
 "- %s · Ревью пулл-реквеста по авторизации" % t(151),
 "- %s · ❗ Обновить сертификат до пятницы" % t(96),
 "- %s · ⏸ обед" % t(74),
 "- %s · Пишу тесты на модуль оплаты" % t(41), ""]))
items = ["npm run build -- --watch",
         "SELECT id, status FROM orders WHERE created_at > now() - interval '1 day';",
         "https://github.com/swiftbar/SwiftBar",
         "docker compose up -d\ndocker compose logs -f api",
         "Готово, задеплоил на стейдж. Проверь, пожалуйста, форму оплаты.",
         "export API_BASE_URL=https://api.example.com",
         "git rebase -i HEAD~3"]
open(os.path.join(d, "clipboard.txt"), "w", encoding="utf-8").write(
    "\n".join(base64.b64encode(i.encode()).decode() for i in items) + "\n")
PY
    chmod 600 "$D/clipboard.txt"
    cat > "$C" <<CFG
: "\${VIBEBAR_FILE:=$D/journal.md}"
: "\${VIBEBAR_BUFFER:=$D/clipboard.txt}"
: "\${VIBEBAR_DIGEST_DIR:=$D}"
: "\${VIBEBAR_OPENER:=TextEdit}"
: "\${VIBEBAR_AUTOPASTE:=0}"
CFG
    echo "демо-режим ВКЛЮЧЁН. Настоящий конфиг сохранён в config.env.real"
    echo "Обновите SwiftBar (Refresh All) и снимайте скриншот."
    ;;
  off)
    if [ -f "$B" ]; then mv "$B" "$C"; echo "демо-режим выключен, конфиг возвращён"
    else echo "резервной копии нет — похоже, уже выключен"; fi
    ;;
  *) echo "использование: vibebar-demo.sh on|off"; exit 1 ;;
esac
