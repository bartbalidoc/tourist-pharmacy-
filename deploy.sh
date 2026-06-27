#!/usr/bin/env bash
# =============================================================================
# Tourist Pharmacy — review-site deploy (runs ON the droplet).
# Pulls the latest main from GitHub, rebuilds the container, health-checks it.
# Idempotent: if nothing changed it does nothing. Safe to run anytime; only ever
# touches the tourist-review container — never the other apps on the box.
#
#   ./deploy.sh                 # deploy if there's something new (verbose)
#   ./deploy.sh --quiet-if-noop # silent when already up to date (used by cron)
# =============================================================================
set -euo pipefail
QUIET_NOOP=0; [ "${1:-}" = "--quiet-if-noop" ] && QUIET_NOOP=1

# Single-flight: stop cron and a manual run from rebuilding at the same time.
exec 9>/tmp/tp-deploy.lock
flock -n 9 || { [ "$QUIET_NOOP" = 1 ] || echo "[deploy] another deploy is already running"; exit 0; }

cd "$(dirname "$0")"
git fetch --quiet origin main
before=$(git rev-parse --short HEAD)
after=$(git rev-parse --short origin/main)

if [ "$before" = "$after" ]; then
  [ "$QUIET_NOOP" = 1 ] || echo "[deploy] already up to date ($before)"
  exit 0
fi

echo "[deploy] $(date -u +%FT%TZ) $before -> $after — rebuilding…"
git merge --ff-only origin/main
docker compose up -d --build
sleep 3
code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/login || echo "000")
if [ "$code" = "200" ]; then
  echo "[deploy] ✅ live on $after (/login -> $code)"
else
  echo "[deploy] ❌ health check failed (/login -> $code) — check: docker compose logs"
  exit 1
fi
