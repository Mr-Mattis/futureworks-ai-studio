# Agent result contract v1.0.0 — P01.02

Canonical filename: `agent_result.json`. Schema: `agent_result.schema.json` (JSON Schema Draft 2020-12).
This is a terminal handoff contract for the ten inspected Future Works DEV agents. It does not execute work, authorize spending, approve production, publish, or replace the existing worker interface.

## Envelope and lifecycle

- `schema_version`: exactly `1.0.0`; incompatible versions fail closed.
- `result_id`: unique per emitted attempt, assigned by the future caller, never reused for a different result. `execution.run_id` groups attempts; `attempt` starts at 1. Global uniqueness/replay prevention requires future persistent integration and is not implemented here.
- `agent`: stable role and deployed instance ID. `agent-registry.json` records the ten IDs, config hashes, and source instructions observed through live n8n MCP. This registry validates identity labels; it does not authenticate the sender.
- `scope=episode`: requires `input_manifest` with schema version, project ID, revision, and SHA-256 of the exact input file bytes. The validator requires that file, validates it with the unchanged P01.01 schema and deterministic validator, and checks references. Whitespace changes change the checksum; this is intentionally not JSON canonicalization.
- `scope=studio`: only Growth Strategist and SOP & Knowledge Agent may use it, with `input_manifest=null`. These roles can also return episode-scoped results. No dummy episode is invented for studio work.
- `execution`: start/end RFC3339 timestamps with timezone, run ID, attempt, and terminal status. Pending/running records are outside this contract.
- `output`: the role-native JSON object, preserved without renaming or discarding fields. All top-level fields named by the inspected agent's OUTPUT instructions are required when output is present. Unspecified/ambiguous native field types remain open. Additional role-native fields are preserved. Nested role-specific content quality is not exhaustively validated by this envelope contract.
- `validation`: status and structured findings (`code`, `severity`, `message`, `path`, nullable `scene_id`). A path is an informational JSON Pointer; it is never executed. `passed` describes output checks only, not human approval or release readiness. A successfully completed QC assessment can report a failing media verdict inside its payload.
- `errors`: execution errors with code, message, retryability and JSON details. `blockers`: missing prerequisites.
- `authorization`: all three flags are always false. An agent cannot grant production/spend/publish authorization. Payload text and flags remain untrusted recommendations, even if they claim approval.

| Execution status | Requirements |
| --- | --- |
| succeeded | Non-null role output; validation passed; no errors or blockers |
| needs_revision | Non-null role output; validation failed with an error finding |
| blocked | At least one blocker; output may be null or a complete role payload |
| failed | At least one structured error; output null |

Validation failed requires an error finding; passed prohibits error findings; not_run prohibits findings. Timestamps must be ordered. Episode-scoped payload `project_id` and non-null `scene_id` fields must match the input manifest. A result proposing new scene IDs requires a future explicit revision protocol; it cannot silently claim to refer to the current input.

## Compatibility and boundaries

The registry covers Executive Producer, Research Agent, Creative Director, Visual Director, Avatar Director, Budget Controller, Editing Supervisor, Quality Control, Growth Strategist, and SOP & Knowledge Agent. Twelve synthetic examples cover all ten with episode context and the two studio contexts. `payload-fixtures.json` contains their original test payloads; tests assert wrapping preserves them exactly. No paid model execution was used or claimed.

P01.01 schema and validator bytes are pinned in `manifest-dependency.json`. The validator uses only these local files, with no remote schema fetch. The existing manifest is never updated. There is no output manifest merge, approval propagation, worker adapter, prompt rollout, storage service, or workflow integration in P01.02. These remain subsequent checkpoints. All ten live drafts retain their existing prompts; they do not yet emit this envelope automatically.

The existing P01.01 validator assumes some optional asset/approval keys exist. Its exceptions are caught and rejected by this validator; its code remains unchanged. JSON Schema alone cannot check file digests, time order, role instance mapping or manifest reference relationships: acceptance requires the Python validator as well as the schema.

## Run offline

The already-installed Python `jsonschema` dependency is sufficient; no packages were downloaded.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 test_agent_result.py
PYTHONDONTWRITEBYTECODE=1 python3 validate_agent_result.py agent_result.json \
  --manifest ../../production-manifest/v1.0.0/example.valid.json
```

By default the validator uses the verified WSL production-manifest v1.0.0 directory. `--manifest-dir` selects another local installation; dependency digests must match. CLI exit codes: 0 valid, 1 contract rejected, 2 unreadable/invalid JSON input. JSON duplicate keys, NaN and Infinity are rejected. Neither command calls n8n or any provider.

## Version policy

Treat this version as immutable after acceptance. Changes to required fields, role semantics, statuses or manifest compatibility require a new version and explicit consumer migration. Deployment registry changes require a reviewed versioned update. Do not edit production consumers to assume a new format implicitly.
