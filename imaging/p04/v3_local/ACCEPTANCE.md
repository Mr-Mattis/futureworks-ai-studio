# P04 V3 — corrective image-quality evidence (November 16, 2026)

Owner rejected the earlier V2 latent-upscale images for distorted/pixelated objects. This V3 approach intentionally restores the **original proven Stable Diffusion 1.5 base-sampling pattern**, generates ten **new** distinct 768×512 source designs locally, and then uses **RealESRGAN x4plus neural image-space super-resolution** followed by Lanczos to deliver ten 1920×1080 PNGs. Outputs remain exclusively on the owner's Windows development machine, not in public Git.

## Verified evidence

- Windows development machine Radeon RX 9070 XT / ComfyUI restarted with the missing ComfyUI requirements dependency `spandrel==0.4.2` installed in the isolated Python environment.
- Original base checkpoint remains pinned to SHA-256 `6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa`.
- Installed Comfy-Org packaged `RealESRGAN_x4plus.safetensors` (~67 MB), SHA-256 `37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb`. Source: `https://huggingface.co/Comfy-Org/Real-ESRGAN_repackaged/resolve/main/RealESRGAN_x4plus.safetensors`. Upstream algorithm repo uses BSD-3-Clause; confirm exact redistributed model terms and third-party rights before commercial distribution.
- 10 distinct local Comfy GPU generation receipts, real 768×512 PNGs, prompts, seeds and immutable SHA-256 metadata, stored locally in `collection-v3/receipts.json`.
- 10 distinct local Comfy neural-upscale receipts, real 1920×1080 PNGs, and output hashes stored locally in `collection-v3/upscale-receipts.json`.
- 20 total V3 assets (10 original native source and 10 upscaled deliverables) independently hash-verified and dimensions checked by `verify_collection_v3.py`; local index `collection-v3/P04_V3_VERIFIED_ASSETS.json`.
- Full-resolution review montage: `C:\Users\yashi\Documents\futureworks-p04-data\collection-v3\P04_V3_ESRGAN_1080P_CONTACT_SHEET.png`.
- The first ten original `P04_GPU_001` assets are **unchanged**, and the failed V2 collection is retained separately for audit only.
- Fresh full **268-test cross-phase offline regression passed** on this V3 review worktree, zero failures, 14 isolated suite invocations, local evidence `/tmp/fwai-v3-full-regression.log`. This validates inherited P01–P05 contracts; it does not replace real-provider tests or owner visual acceptance. V3 imagery is **NOT YET OWNER-APPROVED**; P04's locked approved-manifest exit remains OPEN.

## Runway read-only validation

The user safely installed a Runway Developer API key in WSL at `~/.config/futureworks-ai-studio/secrets/runway_api_key` (directory 0700 / file 0600). A read-only authenticated `GET /v1/organization` returned HTTP 200 and a credit balance of **1000 credits**, equivalent to $10 of prepaid credits as of the probe. **No provider uploads or paid requests** were made. The owner approved a **maximum $5 pilot for three 5s Gen-4.5 clips**, but has **not separately granted the required external source-asset upload permission** or confirmed licensing rights for specific assets; the n8n paid adapter remains disabled. Do not treat possession of 1000 credits as authority to spend more than $5. Rate per official price currently 12 credits/s = 180 credits expected for 15 seconds, excluding taxes/fees.

## Reproducibility

- `generate_collection_v3.py`: local prompt graph, durable Comfy receipt, refusal to blindly resubmit unknown jobs, SHA-indexed native assets. Requires pinned model file and running ComfyUI 127.0.0.1:8188.
- `upscale_collection_v3.py`: exact source SHA check, pinned upscaler SHA, Comfy ImageUpscaleWithModel+ImageScale and durable receipts.
- `verify_collection_v3.py`: hash/dimension validation, collage and machine-readable asset provenance report.
- `runway_account_readonly_probe.py`: safe WSL GET organization, prints balance/tier only, never the credential; no paid operations.

These are **local development helpers**, not production-approved source or complete P04 signed manifest/n8n authenticated writer. Next acceptance steps: owner inspect exact V3 full-size renders; rights and immutable manifest scope review; separately authorize specific original/selected image hashes for Runway uploads; independently sign approval; authenticated P04 n8n receipt/handoff; pilot with strict cap; three real clip QC; full regression rerun; separate PR merge/production/publication approvals. No bypass of fail-closed gates.
