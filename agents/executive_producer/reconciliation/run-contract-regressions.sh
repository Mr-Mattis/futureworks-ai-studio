#!/bin/sh
# Legacy validators use an absolute contract path. Alias ONLY this development
# checkout's read-only contracts there, never the actual workstation home.
set -eu
TASK_REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
exec bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$TASK_REPO" /mnt \
  --ro-bind "$TASK_REPO/contracts" /home/mattis983/futureworks-studio/futureworks-ai-studio/contracts \
  --chdir /mnt --clearenv --setenv PATH /usr/bin:/bin \
  /usr/bin/python3 -B agents/executive_producer/reconciliation/run_contract_regressions.py
