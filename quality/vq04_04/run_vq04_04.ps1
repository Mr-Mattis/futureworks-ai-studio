# Future Works VQ04.04 — reproducible local door-film/gripper evidence.
# No production mutation, automatic deletion, cloud uploads, paid Runway or publishing.
$ErrorActionPreference='Stop'
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-04'
$source=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-03\scene\FWAI_VQ04_03_HAND_CONTACT_V3.blend'
$scene=Join-Path $root 'scene\FWAI_VQ04_04_CONTACT_V2.blend'
$master=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-data\character-library\FWAI-M001\v2.0\FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
$python=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe'
$sender=Join-Path $root 'send_live_command.py'
$out=Join-Path $root 'evidence'
if (!(Test-Path $source) -or !(Test-Path $master) -or !(Test-Path $blender) -or !(Test-Path $python)){throw 'Missing required approved source/runtime'}
if (!(Test-Path $scene)){
 New-Item (Split-Path $scene) -ItemType Directory -Force|Out-Null
 Copy-Item $source $scene
}
$before=Get-FileHash $source -Algorithm SHA256
$derived=Get-FileHash $scene -Algorithm SHA256
$approved=Get-FileHash $master -Algorithm SHA256
if ($approved.Hash -ne '480263BDD7637BFB2D90CC2DEECDEB616EEF03492A35216DBEBFD3B1F44C555C'){throw 'Approved character changed'}
& $blender --background $scene --python (Join-Path $root 'test_film_contact.py')
if($LASTEXITCODE -ne 0){throw 'Door film geometry tests failed'}
& $blender --background $scene --python (Join-Path $root 'test_film_grip.py')
if($LASTEXITCODE -ne 0){throw 'Fingertip BVH and two-sided geometric staging tests failed'}
& $blender --background --factory-startup $scene --python (Join-Path $root 'test_vq04_04_ui.py')
if($LASTEXITCODE -ne 0){throw 'Native Blender UI/safety regression failed'}
& $blender --background $scene --python (Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-03\test_hand_tool.py')
if($LASTEXITCODE -ne 0){throw 'Existing articulated fingers regressed'}
& $blender --background $scene --python (Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-02\test_height_guard.py')
if($LASTEXITCODE -ne 0){throw 'Mech 1.9558m height regressed'}
& $blender --background $scene --python (Join-Path $root 'render_vq04_04.py')
if($LASTEXITCODE -ne 0){throw 'Three stage render proof failed'}
$window=@(Get-Process blender -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*FWAI_VQ04_04_CONTACT_V2*'})
if($window.Count -eq 0){
 Start-Process -FilePath $blender -ArgumentList ('"'+$scene+'"') -WindowStyle Normal
 Start-Sleep -Seconds 4
}
foreach($arg in @('--load-preview','--load-identity','--apply-height-guard','--load-hand','--load-film')){
 & $python $sender $arg
 if($LASTEXITCODE -ne 0){throw ('Live GUI refused '+$arg)}
}
foreach($phase in @(1,72,36)){
 & $python $sender --film-stage $phase
 if($LASTEXITCODE -ne 0){throw ('Live GUI refused film frame '+$phase)}
 & $python $sender --film-door-diagnostic $phase
 if($LASTEXITCODE -ne 0){throw ('Door diagnostic failed at frame '+$phase)}
 & $python $sender --film-finger-diagnostic $phase
 if($LASTEXITCODE -ne 0){throw ('Finger diagnostic failed at frame '+$phase)}
}
& $python $sender --film-stage 36
if($LASTEXITCODE -ne 0){throw 'Could not restore 36 reach stage'}
& $python $sender --calibrate-two-sided
if($LASTEXITCODE -ne 0){throw 'Two-sided kinematic alignment failed'}
& $python $sender --inspect-two-sided
if($LASTEXITCODE -ne 0){throw 'Visible Blender did not report contact target gap'}
$ack=Get-Content (Join-Path $root 'live_bridge_v2\ack.json') -Raw | ConvertFrom-Json
if ($ack.status -ne 'ok' -or $ack.gui_visible -ne $true -or $ack.frame -ne 36 -or $ack.message -notmatch 'gap=([0-9.]+)m'){
 throw 'Live Blender receipt was missing or invalid'
}
$gap=[double]$Matches[1]
if($gap -gt .003){throw 'Two-sided stage index gap exceeds 3mm'}
if((Get-FileHash $source -Algorithm SHA256).Hash -ne $before.Hash){throw 'Prior scene mutated'}
if((Get-FileHash $scene -Algorithm SHA256).Hash -ne $derived.Hash){throw 'Derived .blend auto-saved'}
if((Get-FileHash $master -Algorithm SHA256).Hash -ne $approved.Hash){throw 'Canonical character master mutated'}
Copy-Item (Join-Path $root 'live_bridge_v2\ack.json') (Join-Path $out 'VQ04_04_LIVE_GUI_ACK.json') -Force
$filmResult=Get-Content (Join-Path $out 'VQ04_04_FILM_TESTS.json') -Raw|ConvertFrom-Json
$fingerResult=Get-Content (Join-Path $out 'VQ04_04_FINGER_DIAGNOSTICS.json') -Raw|ConvertFrom-Json
$uiResult=Get-Content (Join-Path $out 'VQ04_04_UI_SECURITY_TESTS.json') -Raw|ConvertFrom-Json
$oldHands=Get-Content (Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-03\evidence\VQ04_03_ENGINEERING_TESTS.json') -Raw|ConvertFrom-Json
$oldHeight=Get-Content (Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-02\evidence\VQ04_02_HEIGHT_GUARD_TEST.json') -Raw|ConvertFrom-Json
$render=Get-Content (Join-Path $out 'VQ04_04_RENDER_MANIFEST.json') -Raw|ConvertFrom-Json
if(!$filmResult.all_pass -or $fingerResult.status -ne 'PASS' -or !$uiResult.all_pass -or !$oldHands.all_pass -or $oldHeight.passed -ne $oldHeight.total){throw 'Combined engineering gate failed'}
if(!$render.verified_kinematic_pair_before_render.two_sided_geometry_pass -or !$render.post_render_pair.two_sided_geometry_pass){throw 'Calibration did not survive Blender render evaluation'}
$sum=[ordered]@{
 schema='FWAI_VQ04_04_COMBINED_ACCEPTANCE_V1'
 scene=$scene
 scene_hash=$derived.Hash
 approved_master_hash=$approved.Hash
 film_vertices=425
 film_thickness_m=.00025
 film_test_count=$filmResult.passed
 fingertip_bvh_tests=$fingerResult.passed
 native_ui_security_tests=$uiResult.passed
 previous_finger_tests=$oldHands.passed
 previous_height_regressions=$oldHeight.passed
 total_tests=($filmResult.passed+$fingerResult.passed+$uiResult.passed+$oldHands.passed+$oldHeight.passed)
 fixed_door_coverage_proxy_fraction=0.2835
 frame36_reach_goal_error_m=$gap
 actual_visible_blender_gui_ack=$ack.gui_visible
 has_two_sided_geometric_stage=$true
 force_tension_adhesion_verified=$false
 mesh_intersection_for_entire_hand_verified=$false
 blender_cloth_baked=$false
 production_cinematic_approved=$false
 paid_services_used=0
 automatic_file_deletion_enabled=$false
 publishing_enabled=$false
}
$sum|ConvertTo-Json -Depth 7 | Set-Content (Join-Path $out 'VQ04_04_COMBINED_ACCEPTANCE.json') -Encoding UTF8
Write-Output ('FWAI_VQ04_04_TECHNICAL_PASS TESTS='+$sum.total_tests+' VISIBLE_GUI='+$sum.actual_visible_blender_gui_ack)
Write-Output ('FILM_DOOR_COVERAGE_PROXY='+$sum.fixed_door_coverage_proxy_fraction+'; INDEX_GAP_M='+$gap)
Write-Output ('REVIEW='+ (Join-Path $out 'VQ04_04_REVIEW.html'))
Write-Output 'CREATIVE_QA=HOLD; BAKED_CLOTH=NO; FORCE_GRIP=NO; PRODUCTION=PROTECTED'
