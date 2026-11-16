#!/bin/sh
# Development-only bridge lifecycle. Never alters production compose/workflows.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
STATE=/tmp/fwai-p03
umask 077
mkdir -p "$STATE"
chmod 700 "$STATE"
if [ ! -f "$STATE/token" ]; then
  openssl rand -hex 32 > "$STATE/token"
  chmod 600 "$STATE/token"
fi
if [ -f "$STATE/pid" ] && kill -0 "$(cat "$STATE/pid")" 2>/dev/null; then
  echo "P03 development bridge already running"
  exit 0
fi
(
  cd "$REPO"
  P03_DEV_TOKEN=$(cat "$STATE/token") P03_ALLOW_PRIVATE_BIND=1 \
    P03_ALLOW_ONE_SHOT_DEMO=${P03_ALLOW_ONE_SHOT_DEMO:-0} \
    nohup /usr/bin/python3 -B orchestration/p03/api.py \
      --database "$STATE/orchestrator.sqlite3" --bind 0.0.0.0 --port 18731 \
      > "$STATE/server.log" 2>&1 < /dev/null &
  echo $! > "$STATE/pid"
)
sleep 1
if ! kill -0 "$(cat "$STATE/pid")" 2>/dev/null; then
  echo "Development bridge failed; check restricted log"
  exit 1
fi
echo "P03 development-only bridge running on port 18731"
echo "Access requires a 64-character bearer token held outside the Git repository."
