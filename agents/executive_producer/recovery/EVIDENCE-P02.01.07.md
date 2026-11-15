# P02.01.07 — Transactional claim integration evidence (development only)

Date: 2026-11-15. Phase status: **OPEN**. This evidence record does not amend the locked master checklist.

## Verified GitHub source state

- GitHub App repository write access restored; branch `dev/p02.01-atomic-proof` created from `dev/p02.01-executive-producer`.
- The branch contains `atomic_claim.py`, `test_atomic_claim.py`, and README. Contents were fetched back through the GitHub connector after creation.
- A development-only GitHub Actions workflow `.github/workflows/p02-atomic-tests.yml` was committed, running the SQLite unit tests on branch pushes with read-only repository permissions.
- A concurrent provider-operation reservation test was subsequently committed.
- Latest test-code commit at the time of this record: `3bc7e26a6438cca9d434875f8a05c1292d7ae023`.

## Test evidence

- Prior sandbox artifact `fwai_p0201_atomic` (a different pre-commit implementation) passed ten unit tests on 2026-11-15, including a parallel claim test. Do **not** transfer that result to this branch's implementation.
- The current branch's test suite contains eleven test methods, including a 12-process logical claim test and a 12-process provider-reservation test.
- The branch's eleven tests are **not yet independently verified as passing**. The GitHub connector's combined-status response was empty for the latest commit, which does not constitute either success or failure.
- Existing isolated n8n recovery harness `QBVsaXHigHIP5cbi` confirmed sequential claim/resume/replay/conflict behavior in executions 45–48; four near-simultaneous manual tests 49–52 left one persistent test record. That does **not** prove atomic storage guarantees.

## Deployment boundaries

- The SQLite module is a **separate reference implementation**, not imported into `worker/worker.py` or its Docker image. No production migrations, stack changes, or provider calls were performed.
- The canonical production state/data-table gates are independent of this proof. Do not wire them together before a migration/rollback design and real worker acceptance tests.
- No direct Windows/WSL terminal channel is exposed in this ChatGPT conversation. GitHub can alter remote branches but cannot create a Git worktree inside the user's PC.
- Provider-side exactly-once operation cannot be guaranteed by a local SQLite key alone, especially following an ambiguous timeout.

## Outstanding P02.01.07 acceptance

1. Obtain successful CI or independently executed tests of the **committed** code.
2. Use an authorized desktop/WSL computer-use session to create a local development worktree; preserve production checkout and local changes.
3. Implement a reviewed migration/interface to the development worker; test concurrent end-to-end submissions and interruption recovery without paid API calls.
4. Handle unknown provider results by reconciliation before retrying, and enforce authorization separately.
5. Reconcile the live n8n Executive Producer draft with repository-managed source, rerun canonical contract and permission checks.
6. Record final evidence and seek explicit human acceptance before merging.
