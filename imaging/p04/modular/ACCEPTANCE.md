# P04.06 — Modular Rendering Architecture | Technology-First Acceptance

**Owner authorization:** 2026-11-17. This is a new, isolated P04 development checkpoint following the previously rejected V5 visual batch and concept-first V6 calibration. It does not overwrite or retroactively close earlier locked P04.06 naming/requirements; this is a distinct extension pending traceability review.

## Creative standard: "Real-life-like," not simply "photorealistic"

The objective is a fictional machine that appears **physically present, tangible, correctly scaled and manufactured**, as though an on-location industrial film crew could photograph it. Sharp pixels, cinematic colors, detailed textures, and optical upscaling are insufficient when the machine looks impossible, toy-sized, painterly, ill-proportioned or mechanically incoherent. Avoid marketing imagery that implies speculative technology is operational in the real world.

## Stage separation and fail-closed order

| Gate | Input | Deliverable | Acceptance | State |
| --- | --- | --- | --- | --- |
| 00 — Technology geometry | Brief & dimensioned machine specification | Orthographic vector design, separate transparent silhouette/mask, SHA receipt | Six truss anchors, exact six connected manipulators, visible crew-scale hatch, shape not military | IMPLEMENTED / technical QA PASS |
| 01 — Mechanical function | Approved geometry | Role, linked kinematic chains, serviceability and power routing | No detached joint, no invalid linkage, six route checks, scale reference; no claim of physics/FEA certification | IMPLEMENTED / heuristic QA PASS |
| 02 — Real-life-like materials | OWNER-APPROVED geometry + mechanical reference | Surface and detail pass; planned local image-to-image/inpaint workflow | Tangible engineering: manufacturable seams, authentic material roughness, load-path plausibility, wear/grease/weathering localized to use | BLOCKED on human Gate 00/01 review |
| 03 — Environment | Approved machine artifact, separate scene brief | Independently rendered setting, lighting/depth reference, separate mask | Believable context and correct subject scale; preserve object identity | NOT STARTED |
| 04 — Physical compositing | Approved technology + environment | Depth-aware placement, shadow/material consistency | One source of scale, no background-induced geometry changes | NOT STARTED |
| 05 — Filmic finish | Approved scene | Cinematography vocabulary and render QC | Camera movement consistency, material detail and temporal stability | NOT STARTED |

The machine is preserved as an independently hashed source artifact. A bad sky, background or landscape must never regenerate approved geometry. A failed actuator/arm must not force regeneration of environmental assets. Device memory consumption is reduced by making expensive stages conditional on lower-cost structural approval; actual speedups must be benchmarked, not assumed.

## Prototype machine — FWAI-T001 Orbital Lattice Weaver

- Fictional **civilian orbital megastructure assembly** platform, no weaponry, no military colors.
- Hexagonal structural truss with **40-meter perimeter-ring diameter**, six independent arms and **12 articulated links**. Arms extend beyond the 40 m truss ring.
- Six anchored radiators, attached 2 m crew-service airlock/hatch for recognizable human scale.
- Each fabrication arm's conceptual chain: truss mount → rotary joint → linear actuator → fabrication tool. Each declares protected power harness and replaceable service cartridge.
- Orthographic top view. Primary blueprint is an **engineering layout reference only**, not a 3D CAD solid, real-life photographic result, validated load calculation, proof of feasible dynamics, thermal simulation or manufacturing certificate.

### Generated local preview

On El_Corredor:

`C:\Users\yashi\Documents\futureworks-p04-data\p04-06-modular-preview\FWAI-T001_blueprint.svg`

Transparent subject-only mask:

`C:\Users\yashi\Documents\futureworks-p04-data\p04-06-modular-preview\FWAI-T001_subject_mask.svg`

Both files and the source spec are SHA256-bound in `FWAI-T001_geometry_receipt.json` under the same folder. View the SVG files in Edge/Chrome or VS Code. This is deliberately a blueprint rather than a deceptive photorealistic image; Stage 02 is blocked until the geometry is approved.

### Run and test from Ubuntu (after merging/reviewing the dev branch)

```bash
cd ~/futureworks-studio/futureworks-p04-06-modular
sh imaging/p04/modular/run-isolated-tests.sh
python3 imaging/p04/modular/geometry.py imaging/p04/modular/FWAI-T001_geometry_spec.json /mnt/c/Users/yashi/Documents/futureworks-p04-data/p04-06-modular-preview
```

## Independent acceptance gates

- Geometry code rejects military purpose/features, an attached environment, missing/duplicate ring anchors, detached manipulators, unbounded links, missing real-world scale and wrong panel count.
- Mechanical code rejects missing operational purpose, cable protection, tool-chain connectivity, maintenance provisions and false engineering certification status.
- A deterministic SVG receipt binds source spec and output files. Human owner review is still required: acceptance `P04.06-GEOMETRY=APPROVE|REVISE` and optionally `NOTES=...`.
- No ComfyUI service, Runway provider, protected n8n credential, external media hosting, production publishing or paid API is invoked by this checkpoint.
- The original ten approved P04 images and three already approved P05 Runway clips remain unchanged. Previous V5 semantic rejections and V6 references remain audit evidence, not production assets.

## Next checkpoint after human review

Render **one approved machine only** with precise contour conditioning (e.g. ControlNet line/depth where supported), several 100%-zoom mechanical crops, a separately approved neutral background, and material passes. Use low-denoise inpainting rather than re-imagining the main silhouette. Review scale, interlocking joints, structural support and tangible real-world materials before any batch or environmental scene.
