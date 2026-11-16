# Future Works AI Studio — P03 Isolated Master Orchestration

Development branch: `dev/p03.01-p03.08-orchestration` (from the merged P02 development branch).

The **actual** n8n production workflows, legacy worker, Docker Compose,
YouTube, spending providers, and `main` remain unaffected. This directory
is a deliberately synthetic, independently validated P03 implementation.

## Modules and boundaries

| File | Function |
| --- | --- |
| `engine.py` | Durable SQLite plan/claim queue, immutable manifests, seven specialist stages, dependency-aware parallel execution, fenced recovery, pending approval gates, mock-only provider polling, dashboard. |
| `model.py` | Three explicit choices: offline synthetic replay of P02 archived real Ollama outputs; fresh local Ollama; exact-manifest cached P02 Creative Director plus fresh local specialists. No network except `host.docker.internal:11434` for fresh local Ollama. |
| `cli.py` | Controlled synthetic concept demonstration or explicit local-inference session. |
| `status.py` | Read-only human-readable state and cost/asset/approval report. |
| `api.py` | Strictly token-guarded development `/v1/intake`, `/v1/drive`, `/v1/dashboard`, plus optional one-time synthetic-only smoke path. No provider, publishing or approval mutation routes. |
| `workflow.inactive.sdk.js` | Saved inactive P03 webhook/API orchestration design. **Credentials are placeholders**; it is not deployable until an approved n8n credential binding is completed. |
| `workflow.one-shot-transport.sdk.js` | Separate inactive n8n transport smoke-test graph; accepts exactly one frozen concept; endpoint works only when dev-only demo explicitly enabled. |
| `dev-start.sh` and `dev-stop.sh` | Temporary bridge lifecycle; ephemeral bearer lives outside the repository, and stop invalidates it. |
| `test_*.py`, `check_p03_wrapper.cjs`, `run-isolated-tests.sh` | Bubblewrap/Node-VM execution and negative acceptance regression tests. |

### Locked development flow

`Frozen approved creative brief → canonical P01 manifest bytes and SHA →`
`Executive Producer plan revalidation → research → Creative Director →`
`(visual ∥ avatar) → budget → editing → QC → awaiting_human_approval`.

The local model is a **planning advisor**, not an execution authority. Every
role output passes the accepted role-specific policy and P01.02 canonical
envelope validator. Visual and avatar are eligible concurrently only after
the Creative Director has passed. The budget stage depends on both.
No downstream stage can advance while a prerequisite is missing.

SQL transactions provide atomic intake, duplicate replay suppression,
immutable revision enforcement, single-owner process fencing, and durable
recovery. A failed *local* model task can retry once; uncertain or exhausted
work becomes `needs_review`. A queued *mock* provider operation is never
submitted and cannot establish actual provider-side exactly-once behavior.

### Approval gates

Human production approval, spending approval, and publication approval are
three separate persistent `pending` records. There is **no endpoint to
auto-approve them**. The final dashboard reports the same three false
authorization flags and `dispatch_performed=false`.

### Synthetic/live evidence distinctions

- Synthetic replay uses prior real Ollama role output **as a simulation**.
  When recorded roles originated from a different synthetic P02 manifest,
  their project identifiers are adapted only inside the test model. This is
  **not** fresh inference or proof of new research/asset generation.
- One-shot n8n → WSL HTTP transport (execution **69**) verified real network
  transport and automatically completed the **synthetic replay** to the
  approval gate; it did not freshly call seven role models.
- `workflow.inactive.sdk.js` has explicit bearer-auth placeholders and
  must not be activated without approved secure credential provisioning.
- A direct fresh Ollama test initially passed Research and twice rejected
  Creative for narration pacing; the job appropriately stopped at
  `needs_review`. This failure remains useful negative evidence.
- A separate hybrid local test can reuse the **exact same immutable**
  Creative Director output from P02.02 execution 59 while invoking the other
  six roles freshly through Ollama. Its provenance is explicitly recorded in
  the CLI `mode` field.

### Reproduction, authorized local terminal

Run the strictly isolated regression runner only in the P03 dev worktree:

`sh orchestration/p03/run-isolated-tests.sh`

For a synthetic development proof, run the CLI with an explicitly chosen
temporary SQLite path and run ID. The CLI **does not** perform paid or
production work. For full production capability, the later P04–P12 gates
must separately pass, and secure n8n transport credentials, real provider
status receipts and owner approvals are still required.

### Warning

The synthetic-only smoke route deliberately has **no bearer** because it
accepts one exact known fixture and never has external side effects. It is
disabled by default, exists solely for an isolated development test, and
must be turned off promptly after testing. Never enable it for real briefs.
