#!/bin/sh
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
command -v bwrap >/dev/null
exec bwrap --unshare-all --new-session --die-with-parent \
 --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
 --proc /proc --dev /dev --tmpfs /tmp --ro-bind "$REPO" /mnt \
 --chdir /mnt --clearenv --setenv HOME /tmp --setenv PATH /usr/bin:/bin \
 --setenv PYTHONDONTWRITEBYTECODE 1 \
 /usr/bin/python3 -B -m unittest -v imaging.p04.modular.test_modular
