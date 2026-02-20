#!/bin/bash
set -e
command -v curl >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq curl)
REPO="greenbutton75/webgen-service"
URL="https://raw.githubusercontent.com/${REPO}/main/startup.sh?ts=$(date +%s)"
curl -fsSL -H "Cache-Control: no-cache" -H "Pragma: no-cache" "$URL" -o /tmp/startup.sh
chmod +x /tmp/startup.sh
exec /tmp/startup.sh
