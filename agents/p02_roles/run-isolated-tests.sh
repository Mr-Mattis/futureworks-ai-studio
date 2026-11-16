#!/bin/sh
# P02.02–P02.10: exact role and n8n VM regressions in a credential-free namespace.
# No fallback to host testing when Bubblewrap/user namespaces fail.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
command -v bwrap >/dev/null
test -x /usr/bin/python3
test -x /usr/bin/node
exec bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$REPO" /mnt --chdir /mnt/agents/p02_roles --clearenv \
  --setenv PATH /usr/bin:/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
  /usr/bin/python3 -B -m unittest -v \
  test_role_validation.py test_n8n_wrappers.py test_live_results.py
