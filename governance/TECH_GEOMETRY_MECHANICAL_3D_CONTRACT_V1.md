# Future Works AI Studio — Revised Technology Geometry & Mechanical-Detail Contracts

## Reason for change (November 20, 2026)

The owner rejected earlier FWAI-T001 material images: they read as childish, shallow 2D illustrations despite passing deterministic geometry hashes, heuristic linkage checks, and 1080p model processing. Those technical passes were **not** evidence of visual realism or feasible machinery. The creative quality acceptance remains rejected. **Do not silently transfer previous FWAI-T001 approval to FWAI-B001.**

**New objective:** physically tangible, advanced-yet-coherent architecture, modeled as actual 3D shapes *before* any material/image generation. Begin the redesign using FWAI-B001, a two-strand DNA-inspired spiral staircase at a futuristic library.

## Revised Technology Geometry Agent — mandatory outputs

1. **Unambiguous physical units and world axes.** State meter/feet conversion and orientation. Structural and architectural model coordinates must exist in 3D (x, y, z), never 2D picture-space alone.
2. **Parametric source of truth** committed as JSON with owner decisions, fixed dimensions, constrained ranges, provenance, and unresolved items. Direct changes to owner-approved dimensions must fail validation.
3. **Volumetric independent components** (meshes with faces and thickness or CAD solids) for balcony deck, library anchors, suspension members, helical treads, supporting ribbons, railings and landings. Export standardized 3D exchange file (Wavefront OBJ in meters for this prototype) with named component groups and a content-addressed receipt. Future upgrade: glTF/parametric CAD representation and topology checks.
4. **Multiple views from a single coordinate model.** Front, side, top and oblique perspectives must use the *same* geometry. No view-specific hallucinated components.
5. **True 3D envelopes** for required stair widths, stair turning direction, clearance and reachable landings. Record simplified scalar estimates **separately** from geometric collision checking and safety certification. No declaration of "clearance validated" based on attractive visuals or an incomplete analytic estimate.
6. **Honest unresolved gate:** when a circulation route cannot yet be connected without a geometric or safety conflict, mark the architecture HOLD; do not fabricate an approval.
7. **No GPU material render or environment without a separate explicit owner grant for this design ID.** Prior FWAI-T001 material permission is *not transferable*.

## Revised Structural/Mechanical Design Agent — mandatory outputs

1. **Structural purpose and connections:** identify the cantilever reaction into the building's primary structure, upper suspension load path, anchored tension members, supported balcony slab, helical ribbon/tread connections, bearings, guard infill and courtyard terminal elements.
2. **Each stair strand is physically separate and walkable.** Do not mistake two decorative ribbons attached to one staircase for two independent walking paths.
3. **No central vertical mast** for FWAI-B001; owner delegated an *open central void*. Do not silently add a spine to solve a support problem.
4. **Quantitative envelope checks:** tread count and elevation, approximate angular walkline depth, inner-edge depth, tread thickness, and crossings at matching azimuth. Record uncertainty for unmodeled steelwork, ledgers, handrail terminations, and landing transitions.
5. **Loads, anchors and compliance require independent engineering.** A diagrammatic concept is NOT load-bearing feasibility, stamped structure, code clearance, accessibility, guard-load or egress validation. Never claim compliance without applicable professional assessment.
6. **Engineering credibility is a creative gate:** demonstrate plausible thickness, load-bearing pathways, buildable joints/fasteners and realistic material transitions *once approved for materials*. Reject disconnected sculptural flourishes and physically impossible floating components.
7. **Fail-closed signoff sequence:** geometry proposal → geometric collision/connection development → owner geometry acceptance → independent technical feasibility evaluation (if physical construction is intended) → local materials authorization → cinematic environment and film separately authorized. Each stage is independently reversible.

## FWAI-B001 owner-locked architecture choices

- Balcony: 10 ft long, 6 ft deep, 15 ft above library courtyard.
- Support: building cantilever **plus** overhead suspension to upper structure.
- Spiral center at balcony's exterior edge. Two **independent** helical stairs with counterclockwise descent viewed from above.
- Shared upper landing branches into both routes; separate circulation paths terminate at a common courtyard arrival platform.
- DNA-inspired dramatic hybrid sculpted structural ribbons, exposed precision lattice, composite metallic/transparent treads, glass/sculptural guards.
- Futuristic library, Level 3 civilization / 2500+, precision engineering dominant.
- Open air and open central axis (no vertical spine).
- Diameter may be 9–12 ft; *12 ft is the current modeled envelope*.
- Owner delegated remaining selections: **24=B (3.5 ft per route); 25=C (hybrid load-carrying ribbons); 26=A (open central void); 27=C (balanced monumental and elegant).**

## Initial measurable FWAI-B001 geometry model v1

- World frame: x parallel to facade (right positive), y projecting outward, z vertical; source dimension in feet, export Wavefront OBJ in meters.
- Balcony footprint x = [-5,5] ft, y = [0,6] ft, walking surface at z = 15 ft. Small separate connecting landing y = [6,9.5] ft is an additional circulation element, *not* part of the specified 6ft balcony depth.
- Stair axis (x=0, y=15.5) ft; walking radii 2.4–5.9 ft, radial walk width 3.5 ft, outer ribbon 5.98 ft, approximate helical structural diameter 11.96 ft.
- Two counterclockwise descending helices, azimuth phase difference 180°, one full revolution, 24 wedge treads each, **48 total**, 7.5 inches per riser across 15ft.
- Inner-edge wedge arc per tread = 7.54 in; arc at a radius 12in outward from inner edge = 10.68 in. These are geometric **arc lengths**, not certified building-code tread depths.
- At equal azimuth, the two idealized tread trajectories differ by **7.5 ft** elevation; subtract modeled 0.25ft tread thickness for **7.25ft theoretical tread-only space**. This EXCLUDES handrail/lattice collisions, landing transitions, building structural members, actual head/shoulder clearance, fabrication tolerances and all building-code requirements.
- Cantilever anchors and two overhead tension rods are *visual structural proxies* with no calculated size, stress, buckling, load, or material proof. The central library wall is not generated as scenery.
- Two helical stair cores are generated as actual 3D mesh objects in a static, **unrendered** OBJ. Named groups represent independent treads, curved edge ribbons, handrails, guard posts, support diagonals, cantilever, cables, and the lower terminal slab.
- **UNRESOLVED CRITICAL:** the second strand begins opposite the balcony on the far side of the helix, so the proposed common top landing does not yet safely connect to its entry. A dedicated branch bridge or separate peripheral upper approach is required. No unmodeled link should be silently considered complete. Physical collision and architectural circulation tests remain open.
- At least one **independent accessible entrance/egress route** for the public library must be designed and professionally reviewed. The speculative spiral pair must not be assumed to fulfill those roles.

## Prototype outputs and restrictions

- On the owner's PC: `C:\Users\yashi\Documents\futureworks-p04-data\fwai-b001-architecture-v1\FWAI-B001_parametric_3d_concept_v1.obj`
- Geometry receipt: `FWAI-B001_3d_validation_receipt.json` adjacent to it.
- Parametric source: `imaging/p04/architecture_b001/FWAI-B001_geometry_v1.json`.
- Geometry code and tests: `imaging/p04/architecture_b001/parametric_3d.py` and `test_parametric_3d.py`.
- **No background, material/image rendering, paid calls, external uploads, or publishing performed.**
- Acceptance: `DESIGN_GEOMETRY=HOLD_PENDING_UPPER_BRANCH_AND_COLLISION_CHECK`; final creative acceptance still requires owner review.

## Next development objective

Resolve the **top branching geometry** to make the second staircase actually reachable: compare an upper transfer spine that preserves an open void beneath against a peripheral split-level or ring-side bridge; select based on collision, rail continuity, stair entry width and credible structural support. Regenerate from the same 3D source and verify the complete balcony→A/B→courtyard walking paths before assigning physical materials or requesting aesthetic renders.
