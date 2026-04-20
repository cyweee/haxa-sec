#!/bin/bash
HOST="http://63.179.96.42"

echo "=== Проверяем разные пути ==="
for path in / /source /src /app /admin /debug /api /flag /robots.txt /.git/HEAD /package.json /index.js /server.js /app.js /game.js /blackjack.js; do
  echo -n "GET $path => "
  curl -s -o /tmp/resp -w "%{http_code}" "$HOST$path" --max-time 3
  echo " ($(wc -c < /tmp/resp) bytes)"
  # Если не 404, показать содержимое
  code=$(curl -s -o /dev/null -w "%{http_code}" "$HOST$path" --max-time 3)
  if [ "$code" != "404" ] && [ "$code" != "000" ]; then
    echo "  CONTENT: $(cat /tmp/resp | head -c 500)"
  fi
done
