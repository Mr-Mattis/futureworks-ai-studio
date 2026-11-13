#!/bin/sh
# No host network, sockets, environment, home, production mounts or writable source.
set -eu
TASK_REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
command -v bwrap >/dev/null
test -x /usr/bin/python3
test -x /usr/bin/node
exec bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$TASK_REPO" /mnt --chdir /mnt --clearenv \
  --setenv PATH /usr/bin:/bin --setenv FWAI_TEST_NODE /usr/bin/node \
  /usr/bin/python3 -B agents/executive_producer/tests/test_planner.py
