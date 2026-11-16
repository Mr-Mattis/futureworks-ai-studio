# P04 — Local AMD ComfyUI Image Pipeline (Development Only)

**State:** ten actual ROCm images generated and Visual Director received ten SHA-verified reference *metadata* records; production-grade locked phase exit is not yet accepted.

## Isolated machine paths

Windows ComfyUI clone: `C:\Users\yashi\Documents\futureworks-p04-comfyui`, source SHA `e9afbccc2669677076feb08e52658f129cd8c12b`. Installed local checkpoint: `models\checkpoints\v1-5-pruned-emaonly.safetensors`; its SHA must match the pinned `model-catalog.json`. Artifacts/SQLite live outside the Git repo under `C:\Users\yashi\Documents\futureworks-p04-data`. Development WSL worktree: `~/futureworks-studio/futureworks-p04-images`. Generated images, checkpoints, credentials, database and human likeness assets **must never enter Git**.

ComfyUI started from the isolated Windows virtual environment in offline mode, no custom nodes:
```powershell
cd C:\Users\yashi\Documents\futureworks-p04-comfyui
.\.venv\Scripts\python.exe main.py --offline --disable-all-custom-nodes --disable-auto-launch --disable-pinned-memory --port 8188 --listen 127.0.0.1
```
The ComfyUI HTTP API responds on localhost:8188; n8n Docker can read it via `http://host.docker.internal:8188`. The temporary engine is intentionally not managed by production Compose.

## Modules

- `model-catalog.json`: baseline SD1.5 license and verified model SHA. SDXL is merely a future candidate and has no verified local digest.
- `engine.py`: ten deterministic scene-specific prompt jobs, four templates, exact frozen P01 manifest/seed/model identity, SQLite atomic queued/submitting/submitted/needs_review/complete state, Comfy `/prompt`, `/history` and `/view` receipts, full PNG CRC validation, SHA output index. Ambiguous submissions require reconciliation, not a blind retry.
- `cli.py`: controlled one-command ten-image local Comfy generation and automatic Visual handoff file. For a repeat run use **new** run_id and isolated storage; same run_id is immutable/idempotent.
- `api.py`: development-only token-protected asynchronous image batch API on port 18741, disabled unless intentionally started. Real secure n8n credential binding is NOT done.
- `visual_bridge.py`: read ten actual image paths, verify SHA and provenance, send metadata (not pixels) to local Ollama Visual Director. Requires ten canonical role shots, retains P01 blocked result, and appends P04 lineage in a *separate transport envelope*.
- `repack_visual.py`: migrate initially generated real Visual result from older added-root-keys format into unchanged P01 canonical role result nested inside P04 metadata bundle, without extra paid/model calls.
- `contact_sheet.py`: build a montage from ten actual PNGs for independent human QA.
- `workflow.inactive.sdk.js`: source-controlled **inactive**, credential-placeholder n8n scheduled image submit/poll adapter; n8n executions 70/71 were pinned simulated HTTP data only.
- `workflow.gpu-probe.sdk.js`: inactive n8n real Comfy GPU/queue HTTP read test, executed 72.
- `workflow.real-image-history.sdk.js`: inactive n8n real Comfy ten-receipt `/history` audit, executed 74.
- `evidence/`: canonical metadata receipts, never image bytes.
- `test_*.py`, `check_n8n_wrapper.cjs`, `run-isolated-tests.sh`: offline Bubblewrap isolation, no network/credentials/production mounts, async mock safety tests and exact n8n Code VM tests.

## Actual acceptance examples

The local Windows generation, ten-image indexing and Visual Director local Ollama outcome are fully documented in `P04-ACCEPTANCE.md`. The locked synthetic concept is intentionally NOT a human-approved production manifest. The local Visual Director produced metadata-only shot planning; it did not see the actual pixels or approve rights/engineering accuracy. This is not automated video generation.

## Security / next gate

The async adapter's HTTP Authorization header contains an obvious placeholder; **do not activate it or replace it with a literal secret in Git**. Provision a managed n8n credential in a separately authorized integration, add an authenticated actual n8n `POST /v1/start` test, then prove a *human-approved* immutable manifest can drive ten properly licensed reference assets onward to the locked video-generation adapter. A manifest with `approval_state.status=pending_review` must not be treated as production authorized. Retest live ComfyUI after backend/model updates.

**Do not merge PR, publish workflows, use paid providers, or begin P05 without explicit authorization.**
