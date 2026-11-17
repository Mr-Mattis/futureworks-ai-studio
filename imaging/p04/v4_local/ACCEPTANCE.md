# Future Works AI Studio — P04 V4 photographic mechanical realism acceptance profile

**Owner creative direction (2026-11-16):** V3 generated and RealESRGAN-upscaled images are cleaner than rejected V2, but still look too much like *concept art*. Upgrade the creative standard from generic sci-fi illustration to **credible cinematic industrial/product photography of fictional technology**. Original P04 ten-image reference batch remains immutable and is separately authorized for the one-time $5 Runway pilot. V4 tests are local and do not grant external upload, spending or publishing rights.

## Visual target and rejection checklist

1. **Tires/tracks:** Individual tread blocks visible at 100% crop, consistent tire width, realistic deformation/contact patch, convincing suspension pivot locations. REJECT melted tread textures, concentric loops pretending to be tires, extra wheels or impossible linkage geometry.
2. **Metal panels and fasteners:** Distinguishable aluminum vs steel roughness, machined chamfers, gasket/shadow gaps, realistic hinge/fastener positions, hex bolts, screws and panel alignment; subtle edge highlights. REJECT fused armor plates, smeared seams, inconsistent scale.
3. **Robotic internals:** Plausible pistons, motors/servos, exposed bearings, insulated cabling, connectors, brackets and protected wire routes; joints should have logical endpoints. REJECT hallucinated gears/pistons without mechanical relationships, redundant limbs.
4. **Weathering and materials:** Worn edges, dust collecting in recesses, micro-scratches in direction of use, oxidation, grime/grease near actuators, fingerprints/oil streaks on exposed metal; avoid uniform plastic shine. REJECT same texture applied everywhere or stylized glowing haze obscuring hardware.
5. **Photographic look:** Natural perspective, consistent contact shadows, lens/focal-length realism (35–85mm), physically plausible lighting, restrained depth of field and environmental context. REJECT painterly edges, cel shading, comic/sci-fi illustration, washed-out CGI fog.
6. **Evidence disclosure:** All images are fictional AI_CONCEPT visualizations, not fabricated proof of actual physical prototypes or functioning mechanisms. Never add unlicensed brands/logos/people or third-party characters.

## Engineering A/B experiment

- V3 baseline: SD1.5 at 768x512 + pinned RealESRGAN x4plus neural upscale to 1920x1080.
- V4 A: Original photo-real robotics prompting using licensed Realistic Vision V6.0 B1 fp16 SD1.5 checkpoint (Hugging Face SG161222; CreativeML OpenRAIL M) with independently pinned checkpoint SHA256, MIT-licensed SD VAE fp-mse, then existing RealESRGAN x4plus to 1080p.
- V4 B: Image-to-image photorealization of V3 robot/rover source with conservative denoising to preserve useful composition while refining materials, same pinned checkpoint/VAE/super-resolution.
- Source model and VAE must be acquired from publisher, SHA256 verified before use. Keep separate source prompts, seeds, model IDs, local task UUIDs and PNG hashes; no external AI provider calls.
- Compare A vs B vs V3 at full 1920x1080 at 100% (not montage alone). If source model fails to produce physically plausible details, mark blocked and revisit base model/prompt architecture instead of labeling resized low-quality art 'photoreal'.

## Human acceptance record

For each final V4 image: `V4_IMAGE_<id>=APPROVE|REVISE|HOLD`, with a short note for any rejection (e.g. `TIRE_TREAD_DISTORTED`, `PANEL_FASTENERS_UNREALISTIC`, `ROBOTIC_INTERIOR_MELTED`). V4 images do not supersede the original ten or become Runway upload inputs until the owner approves exact pixel hashes and rights scope.

No production activation, external upload, publication or paid model inference is implied by this local photoreal A/B proof.

## Actual local A/B results — acceptance pending

- **V4 A**: new text-to-image realism render, featuring physically grounded close-up undercarriage/tread geometry. Native 768×512 and RealESRGAN 1920×1080 PNGs generated and SHA-verified.
- **V4 B**: image-to-image material/structure refinement from the V3 #04 rover composition, preserving more of the full subject while improving tread, panel and weathering textures. Native 768×512 and RealESRGAN 1920×1080 PNGs generated and SHA-verified.
- Local comparison sheet: `C:\Users\yashi\Documents\futureworks-p04-data\collection-v4-photoreal-ab\V4_PHOTOREAL_AB_CONTACT_SHEET.png`.
- Source and upscale task UUIDs, prompts and asset hashes: `collection-v4-photoreal-ab/receipts.json` (local only). Metadata-only summary in `imaging/p04/evidence/P04_V4_PHOTOREAL_AB_VERIFICATION.json`.
- Model SHA verified against publisher's official file listing: `c48bfd159cd7a6507b128685e963c398fa72399cefafaf603781df50ce836cc7`. External VAE SHA `735e4c3a447a3255760d7f86845f09f937809baa529c17370d83e4c3758f3c75`, upscaler SHA `37f9a931c215f040aa6d50f711f2cb115f713c46df1d0d6469a8bd7bfe9a60bb`. Original SD1.5 checkpoint and P04_GPU_001 assets unchanged.
- **272/272 isolated regressions passed** on the V4 branch: existing P01–P05 268 + four V4-specific technical contract tests, zero failures.
- Creative-quality result remains **HOLD until the owner reviews both actual full-size PNGs**. Preferred production direction may be B, but do not infer owner approval from this technical proof. No Runway uploads, API spend or production activation for V4.
