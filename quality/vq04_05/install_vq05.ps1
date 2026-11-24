# Install the isolated Future Works VQ04.05 Blender 5.3 review add-on.
# No production n8n, Blender source file, prior addon or cloud service changed.
$ErrorActionPreference='Stop'
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-05'
$addons=Join-Path $env:APPDATA 'Blender Foundation\Blender\5.3\scripts\addons'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
if(!(Test-Path $blender)){throw 'Blender 5.3 not found'}
New-Item -ItemType Directory -Path $addons -Force|Out-Null
Copy-Item (Join-Path $root 'fwai_vq05_cloth_review.py') (Join-Path $addons 'fwai_vq05_cloth_review.py') -Force
& $blender --background --python (Join-Path $root 'enable_vq05.py')
if($LASTEXITCODE -ne 0){throw 'Could not enable VQ04.05 review panel'}
Write-Output 'FWAI_VQ04_05_CLOTH_ADDON_INSTALLED'
Write-Output 'Open VQ04.05 baked .blend in NEW Blender window; use N > Future Works.'
