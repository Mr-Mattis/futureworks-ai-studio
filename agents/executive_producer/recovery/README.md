# P02.01.07 — Atomic claim development proof

**Status: source committed to an isolated Git branch; not deployed or integrated into the running worker.**

This directory implements a small SQLite transactional reference for logical request claims and simulated provider-operation reservations. It has no HTTP, provider, n8n, Docker, spending, publishing, or filesystem production integrations.

`atomic_claim.py` uses `BEGIN IMMEDIATE` and an SQL `PRIMARY KEY(project_id, run_id)` to serialize competing writers and protect logical request identity. Both manifest revision and the original SHA-256 must match for replays. An explicitly interrupted request can resume exactly once; subsequent duplicate claims skip. Provider operations can only be reserved, never dispatched.

The regression suite includes a 12-process race test. Run from this directory with `python3 -m unittest -v test_atomic_claim.py` in a local isolated checkout. The ChatGPT GitHub connector can commit source but cannot execute tests against the user's WSL machine; a GitHub commit is **not** a passing test result.

## Required integration gates

1. Run the tests on the user's actual WSL development worktree under the existing P02.01 offline-isolation policy, without production mounts, secrets, or network access.
2. Review the production worker's existing JSON jobs, paid-operation needs-review behavior, and compatibility with atomic claims. Do not replace the current production persistence without migration and rollback.
3. Verify multiple independent worker processes racing to claim the same job; confirm exactly one persisted identity.
4. Reconcile ambiguous external provider responses using provider receipts/status before any retry; SQLite reservation alone cannot guarantee exactly-once external side effects.
5. Keep all spending, production and publication gates false until separately validated by canonical approval guards.
6. Reconcile the divergent live n8n development draft with repository-tracked workflow source; rerun all canonical contract tests.
7. Record acceptance evidence and obtain human merge approval. Do **not** merge into `main` as part of this reference proof.

Production worker: `worker/worker.py`; original Executive Producer isolation runner: `agents/executive_producer/run-isolated-tests.sh`. This new proof is intentionally not imported by either.
