# FWAI-B001 — Peripheral Skybridge / Helix B Entrance | Architecture V2

**November 20, 2026 — Design authority:** The owner reviewed and explicitly **loved the genuine 3D V1 design** and delegated the remaining upper-branch design decisions to the assistant. The assistant selected a **right-hand suspended perimeter skybridge** to connect the shared 15-ft-high balcony landing to the far-side entry of Helix B.

## Preserve the approved aesthetic; don't imitate the rejected FWAI-T001 results

- Preserve the V1 double-helix visual, counterclockwise path direction, independent A/B stairs, open central void, original 10×6ft balcony at 15ft, material-free technical geometry style, no environment.
- Preserve exact V1 source as a separate model and hash-bound asset. V2 introduces a NEW model and spec rather than overwriting the old review package.
- Future photorealistic material work MUST originate from robust 3D geometry with physically based materials; **no such rendering was authorized or performed in this checkpoint.**
- The library itself is represented by structural attachment proxies, not a complete facade or surrounding courtyard environment.

## How the skybridge connects both stair entries

The original V1 common upper landing extends from the 10×6ft balcony. Its near-side connection to Stair A is bridged by a short, actual 3D threshold slab. Its other route turns right through a level **180° peripheral promenade** around the *outside* of the 12-ft-wide DNA stair footprint and reaches Stair B via a far-side radial landing.

The promenade is an annular deck spanning radii **7.1–10.6ft** relative to the staircase center at (x=0,y=15.5)ft; its nominal radial walking width is **3.5ft**. The deck's outer diameter is **21.2ft** (not the 12ft stair diameter). Guard centers are offset 0.13ft *outside* the walkway edges, bringing the approximate guard envelope to 21.46ft. This additional perimeter footprint is intentional: the user authorized the designer to optimize for visual/functional quality. These are conceptual nominal dimensions, not certified clear passage.

The promenade has a 0.42ft thick modeled deck, curved torsion edge girders, 3D guards and posts, radial underdeck bracing, a conceptual suspended load path via a pair of ties to upper library-structure anchors, and an upper portal connection to Stair B. The near-side approach overlaps the original shared landing. The far-side radial connector overlaps the curved bridge and first B tread boundary (with a modeled 7.5-inch nominal step down). At the far-side doorway, selected outer B guard segments and first portion of the outer structural ribbon are opened, with a capped ribbon return, a conceptual portal gusset and an articulated handrail return. No geometry from the user's original V1 is overwritten.

## Verified software geometry / explicit remaining limitations

**Automated checks (preliminary, not professional engineering approval):**

- V1 source hash is pinned; original balcony dimensions, both stair paths, open center and helical pitch are unchanged.
- The connection from common landing → perimeter arc → opposite upper B entrance is represented by actual overlapping planar deck solids, including a 3.5ft nominal width at the radial connector.
- Non-entry bridge deck's inner edge is 1.12ft radially outside nominal stair outer support centerline. The guard centers are mounted outside the pedestrian band.
- The upper B gate opens the obstructing handrail and structural ribbon sections; conceptual end support is included.
- Actual 3D OBJ includes named components and surfaces. File bytes and parent spec SHA are recorded.
- Local offline 3D viewer shows balcony, both original helices, and the perimeter skybridge in a separate technical category color.

**Not yet verified:**

- General **3D swept collision detection**, including walkway-to-tread clearances at entrance, cable/rail interference and walking headroom throughout both paths.
- Actual structural design and anchorage: connection capacity, lateral/torsional stiffness, concentrated loads, fire resistance, deflection and beam/ribbon fatigue. Suspended ties are design proxies.
- Physical usability of the outer upper B entry in real-world public circulation.
- Building-code tread/tread-rise/guard compliance, required public library egress, accessible path, ADA routes, accessibility, and safety. Neither double-helix stair can be assumed to serve as an accessible or required exit route.
- Manufacture, physics simulation, aerodynamic behavior or construction authorization.

**Acceptance status: V2 geometric preview ready; final design acceptance pending.** Source code tests are *not* a substitute for viewing the actual 3D model or receiving expert structural review if physical construction is ever considered.

## Owner review on El_Corredor

Open:

`C:\Users\yashi\Documents\futureworks-p04-data\fwai-b001-architecture-v2\FWAI_B001_offline_3d_inspector_v2.html`

Use **Choose File** to open:

`FWAI-B001_parametric_3d_concept_v2.obj`

Both files are in the same folder; rotate, switch top/front/side/isometric views and inspect the outer walkway, entry portal and the original DNA geometry. The **V1 viewer/model are unchanged** in the V1 folder.

Other files:
- `FWAI-B001_geometry_v2.json`: parametric source-of-truth with right-hand peripheral bridge geometry.
- `FWAI-B001_v2_validation_receipt.json`: immutable source/3D mesh receipts.

To regenerate from source:

```bash
cd ~/futureworks-studio/futureworks-b001-skybridge
python3 -m imaging.p04.architecture_b001.parametric_3d_v2 \
  imaging/p04/architecture_b001/FWAI-B001_geometry_v2.json \
  /mnt/c/Users/yashi/Documents/futureworks-p04-data/fwai-b001-architecture-v2
sh imaging/p04/architecture_b001/run-isolated-tests.sh
```

**Restrictions remain:** no new GPU materials, images, production media, environment generation, paid APIs, external uploads, publishing or auto-merges. Next work after owner feedback: real swept-volume geometric interference checks and an independent load-path/attachment engineering study, before any cinematic material work.
