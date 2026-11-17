# P04/P05 quality remediation and WSL Runway credential setup

**Owner decision recorded:** Owner accepts the P01 concept manifest and likes the original ten P04 images; explicitly **REJECTS** P04 Collection V2 image quality due to pixelation/distortion. Original P01 frozen example remains immutable and `pending_review` in source, so an independently signed approved successor revision is required. This approval **does not certify all source rights or grant external upload/publishing/budget permission**.

## Why Collection V2 failed

The V2 script (separate draft PR #13) changed generation from the original 512x512 / 768x512 SD1.5 pipeline to 1024x576, then used `LatentUpscale` to 1536x864 with a low-denoise second pass, and finally resized to 1920x1080. Stable Diffusion 1.5 was not designed to create detailed 1080p imagery in that configuration; upscaled pixels do not imply additional reliable fine detail. The observed distortion is consistent with excessive resolution, latent interpolation and repeated diffusion rather than simply a broken 1080p PNG. It should **not** be accepted as P04 imagery.

## Corrective plan (not yet executed)

1. Retain **original ten high-quality P04_GPU_001 PNGs unchanged** and treat the V2 batch as rejected. Protect and verify original SHA hashes.
2. Generate ten additional distinct concepts at the **original proven SD1.5 native resolution**, with prompt/seed diversity but the same approved rendering process; do not change aspect ratio and denoising simultaneously. Use the original pipeline's image integrity and metadata tests.
3. Upscale accepted base renders using a **validated image-space super-resolution** model (e.g. properly sourced/hashed ESRGAN or equivalent) and apply a conservative final Lanczos fit/pad/crop to exactly 1920x1080. Do not call nearest-neighbor latent scaling a high-quality upscaler. Benchmarks must inspect 100% crops of mechanical edges, metal textures and background objects. Standard image enlargement alone does not create actual detail.
4. Run small A/B comparison: original base image vs upscale vs conservative sharpening; reject double-limbs, fused wheels, warped structures and invented detail. Human reviews the **full-resolution** images, not just a montage. If local GPU constraints prevent quality, keep native image dimensions and report blocked rather than counterfeit 1080p quality.
5. Preserve V2 failed results as isolated audit evidence; never replace the original approved images or silently promote new ones to the original ten-image signed approval bundle.

## WSL key setup — no paid calls

Prerequisites: Open **Ubuntu (WSL)**, do not use a PowerShell prompt for these commands; ensure local git checkout exists and is up to date. After this PR is merged/reviewed, execute in Ubuntu:

```bash
cd ~/futureworks-studio/futureworks-ai-studio
python3 tools/runway_key_setup.py
python3 tools/runway_key_setup.py --status
```

The first command privately prompts for the **Runway Developer API** key without echoing it and saves it outside Git at `~/.config/futureworks-ai-studio/secrets/runway_api_key` with a `0700` secret directory and `0600` key-file permissions. Second command verifies safe local storage **without displaying the key**. Do not paste the key in ChatGPT, shell history, screenshots, GitHub, n8n workflow code, or .env in source. Do not `cat` the secret. Never commit this folder.

For immediate use before merge, the reviewed script is readable on the PR branch. Do not reset production or change global git configuration to reach it.

**Important:** WSL filesystem secrets are not automatically available inside n8n Docker. The independent n8n integration must be configured using a dedicated **n8n credential** in the n8n UI or a manager (not with plaintext workflow headers), scoped to the development workflow. No credentials were inserted into n8n by this document, and both paid adapters remain disabled.

## Exact remaining approval and acceptance requirements

- Manifest: create a **new immutable approved revision** with owner identity/record, hashes and explicitly specified allowed use. Do not mutate the frozen P01 test fixture. Rewrite the P04 independent signed verifier to bind the new revision and ten **actually selected** approved image hashes; test fail-closed negative and positive paths.
- Rights: owner confirms no disallowed third-party references, likenesses or trademarks, and explicitly selects `local-only` vs `upload-to-Runway` vs `commercial publication`. Separate owner consent required for uploading exact chosen image hashes to a paid external provider. No blanket rights certification from approving creative direction.
- P04 authenticated writer: provision an isolated managed n8n credential, run one real **approved-manifest** generation and verified automatic handoff. n8n workflow remains inactive until explicitly authorized.
- Runway: verify account has API **credits**; API key alone is not enough. Per official provider, first credits purchase requires minimum $10. The prior recommended 3x5-second gen4.5 720p pilot costs 180 credits / $1.80 at current listed pricing; costs and model capabilities must be rechecked immediately before any paid call. The **owner has not yet expressly approved a USD cap, external uploads or publication**.
- After owner authorizes exact model, duration, 3 scenes, max total charge and expiry, implement guarded real upload + submit + receipt + polling + archived MP4. No automatic retry after unknown HTTP acknowledgement. Show 3 clips for human continuity signoff, collect actual costs, run complete regressions and close only when literal locked P04/P05 exit conditions pass.

Official setup: https://docs.dev.runwayml.com/guides/setup/ ; API: https://docs.dev.runwayml.com/api/ ; price: https://docs.dev.runwayml.com/guides/pricing/ .
