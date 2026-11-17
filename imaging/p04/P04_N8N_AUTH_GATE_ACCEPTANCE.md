# Future Works AI Studio — P04 authenticated n8n integration acceptance

## Current results (2026-11-17)

**Tunnel RESTORED:** Existing outbound tunnel-client is running; connected MCP integration can read n8n workflows. `futureworks-studio-n8n-1` is running; no production workflow was edited or activated.

**New isolated n8n workflow:** `Fxda6MLJBavUMoMu`, `FWAI-DEV — P04 Authenticated Reference Handoff (isolated, no media spend)`. Created in owner's personal n8n project. Four nodes: manual trigger -> immutable exact P04 scope -> local isolated service health -> credentialed POST (initially DISABLED). Manual execution **77** returned success for local service health and deliberately skipped the credentialed POST. This is not acceptance of the final n8n authentication gate.

**Local scoped handoff gateway:** `imaging/p04/p04_n8n_handoff_server.py` listening at `0.0.0.0:18741` in WSL. The n8n Docker container successfully reached `http://host.docker.internal:18741/healthz` (HTTP 200). An isolated 0600 secret stored outside Git at `~/.config/futureworks-ai-studio/secrets/p04_n8n_gateway_token` is required on every POST. Do not expose port publicly or commit the token.

**Actual signed asset handoff:** A direct authorized WSL client POST to the gateway verified exact `P04_GPU_001` source imagery, approved P01-schema derivative manifest, independent HMAC integrity chain, three owner-authorized SHA256 image references and expiry. First POST returned HTTP 201 and atomically wrote an immutable, non-publishing P05 reference handoff at `C:\Users\yashi\Documents\futureworks-p05-data\real-runway-pilot-001\P04_AUTHENTICATED_N8N_REFERENCE_HANDOFF.json`. Repeat was idempotent HTTP 200. Invalid bearer token failed HTTP 401. **No Comfy generation, Runway paid call, publication or production workflow activation was performed.**

**Important distinction:** Above is a **three-reference owner-approved handoff**, NOT an authenticated ten-image Comfy batch-generation writer. It closes reference-authentication infrastructure testing, not the locked full P04 ten-image writer acceptance.

## One owner action needed for true n8n-to-gateway POST

1. Open the **isolated development** workflow: `http://localhost:5678/workflow/Fxda6MLJBavUMoMu`.
2. Open its final node `AUTH P04 handoff POST — ENABLE ONLY WITH MANAGED CREDENTIAL`.
3. Create a **Custom Auth** (HTTP templated custom auth) credential named `FWAI P04 Isolated Handoff Auth`. In the credential template enter JSON of the form `{"headers":{"Authorization":"Bearer <paste-gateway-token-here>"}}`. The actual token should only be pasted into the credential editor, never the workflow graph, shell history, ChatGPT or Git.
4. On Ubuntu, copy the token directly to clipboard **without displaying it**: `cat ~/.config/futureworks-ai-studio/secrets/p04_n8n_gateway_token | clip.exe`. After saving, clear the clipboard via `printf '' | clip.exe`.
5. Assign that credential to the final HTTP Request node. Leave workflow **inactive**; after credential is assigned we can enable only this final node in the isolated manual-test workflow and run a bounded no-cost handoff acceptance test through n8n.
6. Confirm workflow run reached final POST with HTTP 200 and `idempotent_replay=true` (receipt already exists). Re-check three source SHAs and owner-scope signature; no duplicate write or paid job. Afterwards disable node again, keeping the production workflow untouched.

No n8n credential secret can be provisioned through the currently connected MCP workflow tools, which expose only credential metadata and assignment; the owner must supply the secret via n8n's protected credential UI.

## Regression and exit

- Local gateway unit tests: 5 passing, including reject unauthorized operation, immutable idempotent receipt and no provider code.
- Original P01–P05 isolated suite and original P04/P05 scoped security tests rerun before merge.
- Production P04 signed image writer still requires true authenticated ten-image approved-manifest generation and automatic P05 intake, not merely three-reference handoff. P04 stays OPEN.
- Human-approved 3 real Runway clips remain accepted for P05; no new paid permission granted. P05 formal closure dependent on explicit locked acceptance checklist, not only this test.
