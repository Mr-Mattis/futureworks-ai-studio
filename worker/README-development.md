# P02.01 isolated development worker

This is a separate Python/CLI adapter, not a replacement for `worker.py`, an HTTP
service, or a production deployment. It imports the atomic claim primitive and
accepted canonical validators. The existing worker, Dockerfile and compose are
unchanged. Use synthetic inputs and a dedicated local database only.

## Behavior

- `submit(manifest_path, plan, run_id)` validates exact manifest bytes and the
  canonical blocked agent-result envelope. The project/run identity, immutable
  revision/hash, frozen payload and durable queued intent commit together.
  Same identity with changed revision, bytes or planning payload is rejected.
- `take()` atomically transfers one queued intent to a unique ownership token.
  Independent processes share the SQLite queue; there is no enqueue crash gap.
- `finish(ticket)` checks ownership, frozen bytes, role/dependency/gate semantics
  and the canonical envelope again. It reserves deterministic scene/provider/kind
  keys and marks only the planning handoff blocked, in one transaction.
  All 25 operations in the five-scene test fixture remain not_submitted.
- `recover(ticket)` is an explicit zero-side-effect requeue. It invalidates the old
  token and increments the attempt. There is no time-based takeover. An operator
  recovering a lost ticket must inspect the dedicated database's current token;
  do not infer ownership from elapsed time.
- `flag_ambiguous(key, reason)` injects a reconciliation flag and moves the parent
  to needs_review. Duplicate submissions cannot schedule it again. There is no
  provider submission, reconciliation-clear or paid retry API.

Run only in the documented Bubblewrap namespace. The public methods accept a
database path; the isolation runner, not a path string, keeps production storage,
credentials, sockets and the host network unavailable. SQLite must be on a single
machine's local filesystem shared by the processes, not a network share or one
independent database per worker.

## Verification

From the worktree:

```sh
sh worker/run-isolated-dev-tests.sh
sh agents/executive_producer/run-isolated-tests.sh
sh agents/executive_producer/reconciliation/run-contract-regressions.sh
```

The worker runner includes concurrent full submissions/consumers, actual process
exits after submit and take, stale-token rejection, rollback injection, immutable
revision conflicts, invalid metadata, reservation reuse, ambiguity blocking and
the exact n8n JavaScript wrapper in Node VM. It creates only temporary databases.

Inside an equivalent isolated namespace, the CLI is:

```sh
python3 -B worker/dev_worker.py --database /tmp/dev.sqlite3 submit \
  --manifest contracts/production-manifest/v1.0.0/example.valid.json \
  --plan agents/executive_producer/tests/fixtures/plan.valid.json --run-id dev-trial
python3 -B worker/dev_worker.py --database /tmp/dev.sqlite3 drain-one
```

Input files remain within the read-only checkout. Schema validation does not imply
a plan is factually correct or approved. The legacy request table's completed
status means this development planning task ended; dev_jobs and its result remain
blocked. It never means paid generation or publication completed.

## Compatibility and rollback

Legacy JSON jobs are neither read nor migrated. No production mounts, image build,
service restart or provider credentials are needed. Stop the development process
to roll back and retain its database for inspection. Future production integration
requires a separately reviewed migration, rollback and per-provider receipt/
idempotency design. Real external exactly-once delivery remains unverified; an
uncertain real provider response must require independent reconciliation.

The n8n development workflow remains manually triggered and inactive. Its
candidate crosses canonical Python validation before entering this adapter.
There is deliberately no permanent n8n-to-worker production service or dispatch.
