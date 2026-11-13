# P01.07 — Full data-validation gate test v1.0.0

The locked P01.07 requirement is to pass one dummy production manifest through every data-validation gate without paid APIs. This checkpoint uses the existing immutable P01.05 revision 1 for `FWAI-P0105-LIVE-TEST` and live job `P0105-LIVE-TEST-R1`. The exact input project ID, revision and file-byte SHA-256 are retained throughout. It does not create another production manifest or revise earlier contracts.

## What ran

`run_full_gate.py` reads the saved immutable manifest and the live n8n readback captured in `live-readback.json`. It validates:

1. P01.01 manifest schema and deterministic invariants, including five unique scenes totaling 360 seconds.
2. P01.05 exact manifest bytes/revision ID and P01.03 draft job snapshot.
3. P01.04 rows in all six live tables, including indexed values versus embedded JSON and job/provider/scene relationships.
4. Ten P01.02 agent-result handoffs, each bound to the same manifest and corresponding registered agent ID. These are synthetic role-native examples adapted to the test project, not model executions.
5. All nine P01.03 state transitions with in-memory synthetic receipts. Each step retains the same job and manifest reference. Missing gate evidence and agent self-approval are rejected. The real live job remains draft; no passed receipt is inserted into n8n.
6. Seven existing invalid manifest examples, six deliberately malformed table rows, a wrong-revision agent result and a changed script under the same immutable revision are all rejected.
7. A real local process interruption after a mock provider accepted one synthetic request but before the provider ID was recorded. Recovery reopens the durable local snapshot, finds the existing mock job by the same key, completes a synthetic artifact, records one zero-amount billing event despite duplicate delivery, and reuses the result on another restart. `simulate_interruption.py` has no network or provider client.

`gate-report.json` records 28 passed checks and 25 expected rejections. `live-readback.json` contains the six exact live rows. The five P01.07 child rows were added to the existing provider_jobs, scene_assets, costs, approvals and errors tables; the production_jobs row came from P01.05 and was only read. All child records are clearly marked `is_test=true`, share the original job's test_run_id and point to that job's exact manifest revision. Their business record IDs start with `P0107-TEST-` for easy identification. They are retained as evidence and must not be treated as production records.

The live approval record is pending, the provider job is not_submitted, and the cost row is a zero estimate. The synthetic passed receipts exist only inside the test process. They prove the data contract's gate decisions, not that a human authorized this episode, paid generation ran, or anything was published. The local process-crash test made one mock submission; actual provider calls and expenses were zero.

Existing rows were compared before/after, and the four workflow IDs, activity settings and modification timestamps were unchanged. The tunnel was connected for all live reads and writes in this checkpoint. The previous P01.06 tunnel verification gap is now closed at the inventory level.

## Run locally

From this installed directory:

```
PYTHONDONTWRITEBYTECODE=1 python3 run_full_gate.py
```

The runner is read-only with respect to n8n. It uses the captured live readback and installed immutable manifest. To refresh live evidence, separately read the same six n8n rows and update `live-readback.json` in a new evidence version; do not modify this accepted v1.0.0 package in place. Tests perform local temporary writes only. No package download is needed.

P01 is 7/7 at its controlled data-architecture acceptance gate. This does **not** claim the ten local Ollama agents or master orchestrator are connected, or that a real provider provides exactly-once billing. Those are later phases in the locked checklist. Existing active production behavior is unchanged.
