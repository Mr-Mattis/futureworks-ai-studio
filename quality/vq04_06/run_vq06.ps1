# VQ04.06 - repeat local mech-driven cloth and EP001 production preflight.
# All customer assets and baked scene immutable. No paid cloud calls or publishing.
$ErrorActionPreference="Stop"
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-06'
$scene=Join-Path $root 'scene\FWAI_VQ04_06_COUPLED_CLOTH_BAKED_V2.blend'
$master=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-comfyui\output\FWAI_M001_LOCKED_V2_CHARACTER_KEYFRAME_00002_.png'
$prior=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-04\scene\FWAI_VQ04_04_CONTACT_V2.blend'
$py=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
if(!(Test-Path $scene) -or !(Test-Path $master) -or !(Test-Path $prior) -or !(Test-Path $blender)){throw 'Required scene, master, source or Blender missing'}
$hashScene=(Get-FileHash $scene -Algorithm SHA256).Hash
$hashPrior=(Get-FileHash $prior -Algorithm SHA256).Hash
if((Get-FileHash $master -Algorithm SHA256).Hash -ne '5DCEFD9309510754D7B5DD5DD549EAE6F3244D1A4A3B6F9056C2055D620BA12B'){throw 'Latest owner-approved mech master changed'}
& $blender --background $scene --python (Join-Path $root 'validate_coupling.py')
if($LASTEXITCODE -ne 0){throw 'Real 72 frame coupled-mesh validation failed'}
$diagnostic=Get-Content (Join-Path $root 'evidence\VQ04_06_COUPLING_DIAGNOSTICS.json') -Raw | ConvertFrom-Json
if($diagnostic.frames -ne 72 -or $diagnostic.cache_file_count -ne 72 -or $diagnostic.max_door_surface_intrusions -ne 0 -or $diagnostic.max_offset_residual_m -gt .004){throw 'Mech cloth continuity acceptance failed'}
& $blender --background --factory-startup $scene --python (Join-Path $root 'test_vq06_ui.py')
if($LASTEXITCODE -ne 0){throw 'Native GUI/safety UI regression failed'}
& $py (Join-Path $root 'test_vq06_acceptance.py')
if($LASTEXITCODE -ne 0){throw 'VQ06 independent acceptance failed'}
& $py (Join-Path $root 'producer_preflight.py')
if($LASTEXITCODE -ne 0){throw 'Owner-approved EP001 source lock preflight failed'}
if((Get-FileHash $scene -Algorithm SHA256).Hash -ne $hashScene){throw 'Baked scene mutated'}
if((Get-FileHash $prior -Algorithm SHA256).Hash -ne $hashPrior){throw 'Prior approved scene mutated'}
Write-Output 'FWAI_VQ04_06_HAND_TO_CLOTH_ENGINEERING_PASS'
Write-Output ('REVIEW='+ (Join-Path $root 'evidence\VQ04_06_REVIEW.html'))
Write-Output 'AUTONOMOUS_LOCAL=READY; RUNWAY_PAID=NO; FINAL_FILM=CREATIVE_HOLD; PUBLICATION=OFF'
