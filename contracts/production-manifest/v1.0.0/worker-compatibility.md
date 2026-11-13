# P01.01 — Worker compatibility assessment

Source inspected: **2026-11-04 baseline** `futureworks-ai-studio/worker/worker.py`, bundled in `futureworks-ai-studio-2026-11-04-baseline.zip`. This is **not** proof that the current workstation backup contains identical worker code; compare the live P00.07 `project-source.tar.gz` before implementing an adapter.

## Existing POST /jobs contract (baseline)
- `prompt`: string 8–2000 characters
- `mode`: `dry_run` or `live`; defaults to `dry_run`
- `scene_count`: integer 1–4; defaults to 2
- `scene_duration`: integer 5 or 10 seconds; defaults to 5
- `runway_budget_usd`: number 0–25; defaults to 3
- Paid generation requires separate `ENABLE_PAID_GENERATION=true` environment guard.

The legacy worker creates its **own storyboard** (`make_dry_plan` / `make_live_plan`); it does not consume individual canonical scenes, approved narration, per-scene media providers, or 72-second footage. It targets a 1280x720 / 24-fps render internally. Thus a five-scene, six-minute manifest is **not** compatible with `/jobs` today. A successful dry run proves only the legacy smoke-test path.

## Adapter requirements (separate P01/P08 work)
1. Parse the canonical manifest and validate schema plus cross-field constraints.
2. Fetch and verify approval from authenticated server-side storage; never trust a client-set `approval_state` alone.
3. Preserve project_id and manifest revision on every job and asset.
4. **Reject** unsupported scene counts, durations, voice/asset requirements, or resolution instead of truncating to 1–4 scenes or synthesizing an unrelated script.
5. Implement an explicit, approved production capability path for full per-scene videos, identity, sound and OTIO timeline assembly; do not map the five-scene six-minute spec into a legacy ten-second placeholder.
6. Enforce independent budget caps, idempotency and dry-run defaults before generating assets.

No new production endpoint or adapter implementation is included in P01.01.
