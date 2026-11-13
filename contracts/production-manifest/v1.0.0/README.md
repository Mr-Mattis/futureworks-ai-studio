# Future Works AI Studio — P01.01 canonical manifest (v1.0.0)

**Scope:** schema, example, deterministic validator, and non-destructive unit tests only. No live workflow or Python worker was modified.

**Files:**
- `production_manifest.schema.json`: Draft 2020-12 schema, provider-neutral episode contract.
- `example.valid.json`: one five-scene 360-second AI_CONCEPT plan (sample narration is schematic; **not a finished six-minute script**).
- `example.invalid.*.json`: seven deliberately defective manifests.
- `validate_manifest.py`: schema + cross-field checks; exit 0 success, 1 invalid, 2 invocation/parse error.
- `test_manifest.py`: automated checks.
- `worker-compatibility.md`: observed legacy worker contract and safe adapter restrictions.

## Run (WSL Ubuntu)

From this folder:

```bash
python3 -m pip install jsonschema
python3 test_manifest.py
python3 validate_manifest.py production_manifest.schema.json example.valid.json
```

The invalid fixtures must return `FAIL` and exit code 1.

## Approval and scope boundaries

The `approval_state` JSON field is an *informational snapshot*, **not** authorization to spend or publish. The future approval service must independently authenticate the owner and verify immutable revisions. `revision` is a version identifier; actual immutability is enforced by storage, not by JSON Schema. The example references paid providers but generates nothing and authorizes no costs. Media availability, rights, actual narration length, continuity, and file integrity require later phases.

A schema-valid record may not be handed directly to the existing Python worker, which currently accepts a different limited request contract. The adapter is a future checkpoint and must reject unsupported properties instead of quietly dropping work.
