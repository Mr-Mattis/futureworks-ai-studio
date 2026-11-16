#!/bin/sh
# Read-only source, private temp DBs, no home, credentials, sockets or host network.
set -eu
TASK_REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
command -v bwrap >/dev/null
exec bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$TASK_REPO" /mnt --chdir /mnt/worker --clearenv \
  --setenv PATH /usr/bin:/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 -B -m unittest -v test_dev_worker.py test_live_reconciliation.py
