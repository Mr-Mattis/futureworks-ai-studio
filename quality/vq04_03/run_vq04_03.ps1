# VQ04.03: reproducible local-only three-pose finger/tool and one-pose contact proof.
# No paid services, publishing, production modification, or scene autosaving.
$ErrorActionPreference='Stop'
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-03'
$source=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-02\scene\FWAI_VQ04_02_IDENTITY_SCENE.blend'
$derived=Join-Path $root 'scene\FWAI_VQ04_03_HAND_CONTACT_V3.blend'
$canon=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-data\character-library\FWAI-M001\v2.0\FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
$py=Join-Path $env:USERPROFILE 'Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe'
$sender=Join-Path $root 'send_live_command.py'
$out=Join-Path $root 'evidence'
if (!(Test-Path $source) -or !(Test-Path $canon) -or !(Test-Path $blender) -or !(Test-Path $py)){
    throw 'Missing required approved scene or Blender/Python runtime'
}
if (!(Test-Path $derived)){
    New-Item -ItemType Directory -Path (Split-Path $derived) -Force | Out-Null
    Copy-Item $source $derived
}
$canonsha=(Get-FileHash $canon -Algorithm SHA256).Hash
$oldscene=(Get-FileHash $source -Algorithm SHA256).Hash
$derivedsha=(Get-FileHash $derived -Algorithm SHA256).Hash
if ($canonsha -ne '480263BDD7637BFB2D90CC2DEECDEB616EEF03492A35216DBEBFD3B1F44C555C'){
    throw 'Approved V2 image SHA changed'
}
& $blender --background $derived --python (Join-Path $root 'test_hand_tool.py')
if ($LASTEXITCODE -ne 0){throw 'Articulated-hand tests failed'}
& $blender --background $derived --python (Join-Path $root 'test_grip_contact.py')
if ($LASTEXITCODE -ne 0){throw 'Contact reach calibration tests failed'}
& $blender --background $derived --python (Join-Path $root 'test_bridge_vq04_03.py')
if ($LASTEXITCODE -ne 0){throw 'Live bridge safety tests failed'}
& $blender --background --factory-startup $derived --python (Join-Path $root 'test_ui_vq04_03.py')
if ($LASTEXITCODE -ne 0){throw 'Native Blender hand UI tests failed'}
$heightTest=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-02\test_height_guard.py'
& $blender --background $derived --python $heightTest
if ($LASTEXITCODE -ne 0){throw '6ft5in height regression failed'}
$visible=@(Get-Process blender -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*FWAI_VQ04_03_HAND_CONTACT_V3*'})
if ($visible.Count -eq 0){
    Start-Process -FilePath $blender -ArgumentList ('"'+$derived+'"') -WindowStyle Normal
    Start-Sleep -Seconds 4
}
foreach($arg in @('--load-preview','--load-identity','--apply-height-guard','--load-hand')){
    & $py $sender $arg
    if ($LASTEXITCODE -ne 0){throw ('Blender refused '+$arg)}
}
& $py $sender --hand-stage 1
if ($LASTEXITCODE -ne 0){throw 'Open-hand pose failed'}
& $py $sender --hand-stage 72
if ($LASTEXITCODE -ne 0){throw 'Tool-deployed pose failed'}
& $py $sender --hand-stage 36
if ($LASTEXITCODE -ne 0){throw 'Reach pose failed'}
& $py $sender --calibrate-contact
if ($LASTEXITCODE -ne 0){throw 'Kinematic contact calibration failed'}
& $py $sender --inspect-contact
if ($LASTEXITCODE -ne 0){throw 'No Blender GUI contact acknowledgement'}
$ack=Get-Content (Join-Path $root 'live_bridge_v3\ack.json') -Raw | ConvertFrom-Json
if ($ack.gui_visible -ne $true -or $ack.status -ne 'ok' -or $ack.message -notmatch 'gap=([0-9.]+)m'){
    throw 'Live contact report absent'
}
$gap=[double]$Matches[1]
if ($gap -gt .003){throw ('Contact gap larger than 3mm: '+$gap)}
if ((Get-FileHash $canon -Algorithm SHA256).Hash -ne $canonsha){throw 'Approved character master changed'}
if ((Get-FileHash $source -Algorithm SHA256).Hash -ne $oldscene){throw 'Previous scene was saved unexpectedly'}
if ((Get-FileHash $derived -Algorithm SHA256).Hash -ne $derivedsha){throw 'Active .blend source was auto-saved'}
Copy-Item (Join-Path $root 'live_bridge_v3\ack.json') (Join-Path $out 'VQ04_03_VISIBLE_GUI_ACK.json') -Force
$hand=Get-Content (Join-Path $out 'VQ04_03_ENGINEERING_TESTS.json') -Raw|ConvertFrom-Json
$contact=Get-Content (Join-Path $out 'VQ04_03_CONTACT_TEST.json') -Raw|ConvertFrom-Json
$bridge=Get-Content (Join-Path $out 'VQ04_03_BRIDGE_TESTS.json') -Raw|ConvertFrom-Json
$uitest=Get-Content (Join-Path $out 'VQ04_03_UI_TESTS.json') -Raw|ConvertFrom-Json
$height=Get-Content (Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-02\evidence\VQ04_02_HEIGHT_GUARD_TEST.json') -Raw | ConvertFrom-Json
if (!$hand.all_pass -or !$bridge.all_pass -or !$uitest.all_pass -or $contact.passes -ne $contact.total -or $height.passed -ne $height.total){
    throw 'Full VQ04.03 acceptance failed'
}
$summary=[ordered]@{
    schema='FWAI_VQ04_03_COMBINED_ACCEPTANCE_V1'
    identity_approved_v2_sha256=$canonsha
    source_scene_sha256=$oldscene
    derivative_scene_sha256=$derivedsha
    finger_segments=30
    finger_hinges=30
    hand_articulation_tests=$hand.passed
    contact_solver_tests=$contact.passes
    security_bridge_tests=$bridge.passed
    native_ui_tests=$uitest.passed
    legacy_height_tests=$height.passed
    total_tests=($hand.passed+$contact.passes+$bridge.passed+$uitest.passed+$height.passed)
    gui_acknowledged=$ack.gui_visible
    frame36_center_to_target_gap_m=$gap
    film_clamping_friction_verified=$false
    physical_adhesion_verified=$false
    cinematic_approved=$false
    paid_calls=0
    published=$false
    automatic_save=$false
}
$summary|ConvertTo-Json -Depth 7|Set-Content (Join-Path $out 'VQ04_03_COMBINED_ACCEPTANCE.json') -Encoding UTF8
Write-Output 'FWAI_VQ04_03_TECHNICAL_POC_PASS'
Write-Output ('TESTS='+$summary.total_tests+'; CONTACT_TARGET_GAP_M='+$gap)
Write-Output ('REVIEW='+ (Join-Path $out 'VQ04_03_REVIEW.html'))
Write-Output 'CREATIVE_QA=HOLD; PAID_SERVICES=NONE; PHYSICAL_CLAMPING=NOT_VERIFIED'
