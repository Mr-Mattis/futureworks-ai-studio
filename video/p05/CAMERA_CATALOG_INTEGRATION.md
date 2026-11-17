# P05 camera-direction catalog integration — stage 1

Current artifact: `Future_Works_Camera_Direction_Catalog_v1.json` (90 codes) delivered in the ChatGPT conversation; the authoritative JSON is **not yet copied into the repository**, so this does not claim the active agents have read the catalog.

`video/p05/camera_direction_contract.py` validates the exact 90-term 1.0 dictionary and compiles a typed camera plan: one movement (MOV), angle (ANG), framing (FRM), optical control (OPT), explicit scene ID, subject and duration. It rejects unknown/duplicated/wrong-category codes. It is provider-agnostic and does not generate imagery or authorize any API use.

## One-time source-file installation (owner can click Download)

Download `Future_Works_Camera_Direction_Catalog_v1.json` from the ChatGPT conversation to the Windows Downloads folder. On Ubuntu:

```bash
mkdir -p ~/futureworks-studio/futureworks-p04-auth-handoff/video/p05/catalog
cp "/mnt/c/Users/yashi/Downloads/Future_Works_Camera_Direction_Catalog_v1.json" \
  ~/futureworks-studio/futureworks-p04-auth-handoff/video/p05/catalog/
python3 ~/futureworks-studio/futureworks-p04-auth-handoff/video/p05/camera_direction_contract.py \
  ~/futureworks-studio/futureworks-p04-auth-handoff/video/p05/catalog/Future_Works_Camera_Direction_Catalog_v1.json
```

Expect a JSON shot instruction containing `MOV-009 + ANG-010 + FRM-003 + OPT-002`. The project will not accept a catalog with fewer than 90 entries, an unexpected version, duplicate IDs or a category mismatch.

## Remaining adapter work (engineer)

1. Commit the **actual 90-entry catalog bytes** only after validating the downloaded source and SHA256.
2. Implement canonical camera-direction JSON contracts at Visual Director -> P05 scene-plan boundary; current `video/p05/engine.py` plans are not yet calling the adapter.
3. Test example S01/S02/S03 camera specs, negative/conflicting codes, consistent time limits and no paid calls; include contracts in isolated regression.
4. Distinguish human-readable examples from binding camera controls. Models/providers may not support exact mechanical camera parameters; prompt instructions are best effort until a rendering provider's actual camera-control API confirms support.

## Safety

This catalog is purely instructional. It does not create permissions for images, likeness, paid provider calls, publication, or production changes.
