#!/bin/sh
# Strict offline P03 acceptance: no host network, secrets, Docker sockets or
# production mounts; source is bound read-only. Abort if isolation unavailable.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
command -v bwrap >/dev/null
test -x /usr/bin/python3
test -x /usr/bin/node
exec bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$REPO" /mnt --chdir /mnt/orchestration/p03 --clearenv \
  --setenv PATH /usr/bin:/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 -B -m unittest -v test_engine.py test_api.py test_n8n_source.py test_n8n_transport.py
