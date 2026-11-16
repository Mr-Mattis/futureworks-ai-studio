#!/bin/sh
# P04 zero-network acceptance. No model download, host GPU or local server.
# Read-only source, clear environment, private tmp; fail if sandbox unavailable.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
command -v bwrap >/dev/null
test -x /usr/bin/python3 && test -x /usr/bin/node
exec bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$REPO" /mnt --chdir /mnt/imaging/p04 --clearenv \
  --setenv PATH /usr/bin:/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 -B -m unittest -v \
  test_engine.py test_n8n.py test_visual_bridge.py test_api.py
