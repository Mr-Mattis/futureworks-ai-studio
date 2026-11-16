# P04/P05 Closeout: current execution and owner decisions

Date: 2026-11-16. Development only; no deployment, publishing, likeness, external upload or paid API calls authorized.

## P04 Collection V2 generated locally

- Owner approved the broad creative direction of the first ten reference images, and requested ten additional unique designs and better-quality 1080p deliveries. This **does not** approve commercial rights, exact existing image hashes, new images or future Runway upload.
- Created ten new locally generated ComfyUI designs on the owner's AMD GPU using a 1024x576 draft pass, a second *actual latent diffusion refinement* at 1536x864, and Lanczos delivery resize to 1920x1080. Thus 1080p **output dimensions**, **not native 1080p inference**.
- Real GPU task receipts, prompts, seeds, raw and delivered asset hashes retained locally: `C:\Users\yashi\Documents\futureworks-p04-data\collection-v2\receipts.json`.
- Full resolution assets and contact sheet: `C:\Users\yashi\Documents\futureworks-p04-data\collection-v2\P04_V2_CONTACT_SHEET.png`.
- Original ten images and original run `P04_GPU_001` remain untouched. V2 is **an expansion collection**, not a silently substituted image set.
- Visual check is still owner-required. Prompt compliance varies; check all ten individually, especially morphology/continuity before accepting video usage. Even if visual quality passes, model/source rights and exact manifest approval remain separate.
- Local script `imaging/p04/collection_v2_local.py` is an evidence-producing development tool with current owner-machine paths. Adapt to parametrized paths, strict model-hash gate, and automated tests before it is incorporated as a production pipeline. Do not treat this script as the authenticated n8n batch writer.

## Rights review (owner decision, no legal representation)

The pinned baseline uses Stable Diffusion 1.5 weights under CreativeML OpenRAIL M. The model card permits commercial use subject to license restrictions; that is not an unconditional guarantee that any particular generated image is free of third-party rights.

Owner reviews:
1. Confirm all source images, prompts and reference materials were generated in this project or legitimately licensed. No unauthorized real-person identity, likeness, brand/logo, third-party copyrighted characters, trademark or private materials.
2. Confirm use scope: `local development only`, `external Runway pilot upload` (separate, explicit), or `commercial YouTube publication` (still requires separate final asset rights and publish approval).
3. Read the model license and Runway provider terms applicable to uploads/output use; retain URLs and date of review. For commercial release, obtain professional legal review if material risks remain.
4. Review exactly named asset hashes and separately authorize a new derivative manifest; DO NOT alter the frozen P01 sample manifest in place. The current P04 `approval_gate.py` binds the frozen sample path and requires `approved`, while that sample remains `pending_review`. That code path cannot honestly pass yet: an isolated immutable approved-manifest derivative plus tests are required.
5. Signing record (HMAC key managed privately, never in repository, MCP request or chat) must bind reviewer ID, timestamp, exact source/new-manifest hash, ten-or-twenty selected image hashes, rights scope, actual human visual/consistency decisions, and expiration. Existing verifier only supports exactly ten assets; 20-asset collection must be treated as two independent batches or a reviewed schema change.

## Authenticated P04 gateway

P04 n8n workflow `XhXS6pgYziLrSIgy` is inactive and its batch writer disabled/disconnected. No managed credential currently wired. Engineer must provision a dedicated restricted n8n credential to the isolated P04 batch service with no production path, run a true authenticated synthetic approved-manifest batch, verify exactly one job/receipt/automatic P05 reference intake, and revoke test secrets as appropriate. Negative approval test n8n execution 76 failed closed as intended. Do not equate mock requests with live writer acceptance.

## Runway P05

Owner has confirmed a Developer account and a pre-generated API key. **No key is present in n8n's accessible Runway-named credential inventory** at the time of audit. Owner must input it privately via n8n UI/approved secure secret manager; do not place it in Git/chat/logs. The currently inactive P05 workflow `IAkOGqIN72HnqBWe` has a disabled/disconnected credentialless provider node.

Current official Gen-4.5 price is 12 credits/sec, 1 credit = $0.01, per Runway developer pricing; 3 x 5s ~180 credits/$1.80 base. Proposed hard cap $5 *only after explicit owner budget approval* with expiry and zero blind repeats. No real clips, uploads or charges before owner explicit scope: provider/model/scenes/duration, dollar cap, expiry, and which asset hashes can be uploaded. If owner approves, verify API quota and endpoint contract, securely configure credentials, submit exactly three jobs, collect actual task receipts, preserve expiring outputs in isolated storage, verify hashes/video codec/runtime, present three videos for human continuity acceptance. Distinguish image output resolution from Runway generated video resolution (model-specific).

## Closeout state

P04: ten original images real, ten new v2 images real, owner reviewed only original creative direction; locked approved-manifest/rights/authenticated handoff still open.

P05: no real Runway clips; image-backed intents and offline adapters only. Locked exit open.

Regression: On Nov 16, reran both isolated P04 and P05 shell test runners; P05 suite 35/35 passed, P04 base and signed-review suites passed (see local log `/tmp/fwai-p04p05-regression-20261116.log`). This is partial latest-suite validation, not an assertion that the historical 268-test full portfolio was newly rerun.

Source-control: no merge, production activation, payment or publish authority conferred by this document. Branch for review `dev/p04p05-acceptance-evidence`; run formal code/test and approved-manifest integration review before acceptance closure.
