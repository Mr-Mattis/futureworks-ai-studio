#!/bin/sh
# P04 remediation + P05 no-spend development acceptance. Strict Bubblewrap.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
command -v bwrap >/dev/null
test -x /usr/bin/python3
test -x /usr/bin/node

bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$REPO" /mnt --chdir /mnt/imaging/p04 --clearenv \
  --setenv PATH /usr/bin:/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 -B -m unittest -v test_approval_gate.py test_signed_review_n8n.py

bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$REPO" /mnt --chdir /mnt/video/p05 --clearenv \
  --setenv PATH /usr/bin:/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 -B -m unittest -v \
  test_engine.py test_download.py test_n8n.py
