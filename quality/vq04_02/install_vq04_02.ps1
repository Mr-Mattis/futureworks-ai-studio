$ErrorActionPreference='Stop'
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-02'
$add=Join-Path $env:APPDATA 'Blender Foundation\Blender\5.3\scripts\addons'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
if (!(Test-Path $blender)){throw 'Blender 5.3 missing'}
New-Item -Path $add -ItemType Directory -Force | Out-Null
Copy-Item (Join-Path $root 'fwai_live_bridge_addon.py') (Join-Path $add 'fwai_live_bridge_addon.py') -Force
Copy-Item (Join-Path $root 'fwai_identity_preview.py') (Join-Path $add 'fwai_identity_preview.py') -Force
Copy-Item (Join-Path $root 'fwai_height_guard.py') (Join-Path $add 'fwai_height_guard.py') -Force
& $blender --background --python (Join-Path $root 'enable_vq04_02.py')
if ($LASTEXITCODE -ne 0){throw 'Failed to enable addon'}
Write-Output 'FWAI_VQ04_02_ADDON_INSTALLED'
Write-Output 'Open a NEW Blender window with the VQ04.02 scene; old windows retain their existing modules.'
