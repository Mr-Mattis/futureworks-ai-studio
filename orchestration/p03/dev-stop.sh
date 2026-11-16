#!/bin/sh
# Stop ONLY this temporary P03 dev bridge. Does not touch n8n/production.
set -eu
STATE=/tmp/fwai-p03
if [ -f "$STATE/pid" ]; then
  PID=$(cat "$STATE/pid")
  case "$PID" in *[!0-9]*|'') echo "Invalid development PID"; exit 1;; esac
  if kill -0 "$PID" 2>/dev/null; then
    case "$(ps -p "$PID" -o args= 2>/dev/null)" in
      *orchestration/p03/api.py*) kill "$PID";;
      *) echo "Refusing to terminate unrelated process"; exit 1;;
    esac
  fi
  rm -f "$STATE/pid"
fi
# Ephemeral bearer is invalidated; archived isolated SQLite evidence is retained.
rm -f "$STATE/token"
echo "P03 isolated bridge stopped; temporary bearer rotated out"
