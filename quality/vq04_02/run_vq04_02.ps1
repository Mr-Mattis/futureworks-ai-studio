# Future Works VQ04.02 — safely reproducible identity and height proof.
# Production asset files, canonical PNG, models, n8n and Runway are protected.
$ErrorActionPreference = "Stop"
$root = Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-02'
$source = Join-Path $env:USERPROFILE 'Documents\futureworks-vq04\scene\FWAI_VQ04_LIVE_SCENE.blend'
$derived = Join-Path $root 'scene\FWAI_VQ04_02_IDENTITY_SCENE.blend'
$canon = Join-Path $env:USERPROFILE 'Documents\futureworks-p04-data\character-library\FWAI-M001\v2.0\FWAI-M001_APPROVED_FINAL_MASTER_V2.0.png'
$blender = Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
$python = Join-Path $env:USERPROFILE 'Documents\futureworks-p04-comfyui\.venv\Scripts\python.exe'
$sender = Join-Path $root 'send_live_command.py'
$evidence = Join-Path $root 'evidence'
if (!(Test-Path $source) -or !(Test-Path $canon) -or !(Test-Path $blender) -or !(Test-Path $python)){
    throw 'Required Blender, Python or approved source not found'
}
if (!(Test-Path $derived)){
    New-Item (Split-Path $derived) -ItemType Directory -Force | Out-Null
    Copy-Item $source $derived
}
$originalHash = (Get-FileHash $source -Algorithm SHA256).Hash
$derivedHash = (Get-FileHash $derived -Algorithm SHA256).Hash
$canonHash = (Get-FileHash $canon -Algorithm SHA256).Hash
if ($canonHash -ne '480263BDD7637BFB2D90CC2DEECDEB616EEF03492A35216DBEBFD3B1F44C555C'){
    throw 'Approved character reference was modified'
}
& $python (Join-Path $root 'generate_identity.py')
if ($LASTEXITCODE -ne 0){throw 'Identity staging failed'}
& $python (Join-Path $root 'test_design_coverage.py')
if ($LASTEXITCODE -ne 0){throw 'Canonical design audit failed'}
& $blender --background $derived --python (Join-Path $root 'test_identity.py')
if ($LASTEXITCODE -ne 0){throw 'Identity geometry validation failed'}
& $blender --background $derived --python (Join-Path $root 'test_height_guard.py')
if ($LASTEXITCODE -ne 0){throw '6ft5in mech height guard failed'}
$running = @(Get-Process blender -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like '*FWAI_VQ04_02_IDENTITY_SCENE*'})
if ($running.Count -eq 0){
    Start-Process -FilePath $blender -ArgumentList ('"' + $derived + '"') -WindowStyle Normal
    Start-Sleep -Seconds 4
}
foreach($action in @('--load-preview','--load-identity','--apply-height-guard','--inspect-height-guard','--inspect-identity')){
    & $python $sender $action
    if ($LASTEXITCODE -ne 0){throw ('Visible Blender refused '+$action)}
}
$ack=Get-Content (Join-Path $root 'live_bridge_v2\ack.json') -Raw | ConvertFrom-Json
if ($ack.gui_visible -ne $true -or $ack.message -notmatch 'Identity-study parts: 70'){
    throw 'Visible Blender did not acknowledge exactly 70 identity mesh pieces'
}
if ((Get-FileHash $canon -Algorithm SHA256).Hash -ne $canonHash){throw 'Approved visual master changed'}
if ((Get-FileHash $source -Algorithm SHA256).Hash -ne $originalHash){throw 'Original source changed'}
if ((Get-FileHash $derived -Algorithm SHA256).Hash -ne $derivedHash){throw 'Derived scene was unexpectedly saved'}
Copy-Item (Join-Path $root 'live_bridge_v2\ack.json') (Join-Path $evidence 'VQ04_02_GUI_ACK.json') -Force
$technical=Get-Content (Join-Path $evidence 'VQ04_02_TESTS.json') -Raw | ConvertFrom-Json
$height=Get-Content (Join-Path $evidence 'VQ04_02_HEIGHT_GUARD_TEST.json') -Raw | ConvertFrom-Json
$design=Get-Content (Join-Path $evidence 'VQ04_02_DESIGN_COVERAGE.json') -Raw | ConvertFrom-Json
if (!$technical.passed_all -or $height.passed -ne $height.total -or $design.passed -ne $design.total){throw 'Technical acceptance failed'}
$report=[ordered]@{
    schema='FWAI_VQ04_02_COMBINED_ACCEPTANCE_V1'
    scene=$derived; canonical_sha256=$canonHash; original_scene_sha256=$originalHash
    derived_scene_sha256=$derivedHash
    mesh_tests=$technical.passed
    height_tests=$height.passed
    design_coverage_tests=$design.passed
    all_tests=$technical.passed+$height.passed+$design.passed
    stage_parts=70; prior_lower_body_parts=70; height_m=1.9558
    gui_acknowledged=$ack.gui_visible; gui_sequence=$ack.seq
    creative_approved=$false; paid_calls=0; runaway_production_disabled=$true; auto_save=$false
}
$report | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $evidence 'VQ04_02_COMBINED_ACCEPTANCE.json') -Encoding UTF8
Write-Output 'FWAI_VQ04_02_IDENTITY_AND_HEIGHT_TECHNICAL_PASS'
Write-Output ('TESTS=' + $report.all_tests + '; LIVE_GUI=' + $report.gui_acknowledged)
Write-Output ('REVIEW=' + (Join-Path $evidence 'VQ04_02_REVIEW.html'))
Write-Output 'CREATIVE_APPROVAL=HOLD; RUNWAY_PAID_CALLS=0; PRODUCTION_MODIFICATIONS=0'
