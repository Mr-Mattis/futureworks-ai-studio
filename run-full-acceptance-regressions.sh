#!/bin/sh
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
run() {
 label=$1; directory=$2; shift 2
 echo "=== $label ==="
 bwrap --unshare-all --new-session --die-with-parent \
 --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \
 --proc /proc --dev /dev --tmpfs /tmp --ro-bind "$REPO" /mnt \
 --dir /home --dir /home/mattis983 --dir /home/mattis983/futureworks-studio \
 --ro-bind "$REPO" /home/mattis983/futureworks-studio/futureworks-ai-studio \
 --chdir "/mnt/$directory" --clearenv \
 --setenv PATH /usr/bin:/bin --setenv PYTHONDONTWRITEBYTECODE 1 \
 /usr/bin/python3 -B -m unittest -v "$@"
}
run P01-manifest contracts/production-manifest/v1.0.0 test_manifest.py
run P01-agent-result contracts/agent-result/v1.0.0 test_agent_result.py
run P01-job-state contracts/job-state/v1.0.0 test_job_state.py
run P01-data-tables contracts/data-tables/v1.0.0 test_storage_evidence.py
run P01-revision contracts/revision-guard/v1.0.0 test_revision_guard.py
run P01-recovery contracts/recovery-policy/v1.0.0 test_recovery.py
sh "$REPO/agents/executive_producer/run-isolated-tests.sh"
sh "$REPO/worker/run-isolated-dev-tests.sh"
run P02-atomic agents/executive_producer/recovery test_atomic_claim.py
sh "$REPO/agents/p02_roles/run-isolated-tests.sh"
sh "$REPO/orchestration/p03/run-isolated-tests.sh"
sh "$REPO/imaging/p04/run-isolated-tests.sh"
sh "$REPO/video/p05/run-isolated-tests.sh"
echo "ALL-SELECTED-SUITES-PASS"
