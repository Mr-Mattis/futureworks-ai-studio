# Install the reviewed local VQ04 live geometry extension on Blender 5.3.
# GUI Blender windows must be reopened to load new addon code. Existing files are not overwritten.
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:USERPROFILE 'Documents\futureworks-vq04'
$addon = Join-Path $env:APPDATA 'Blender Foundation\Blender\5.3\scripts\addons'
$blender = Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
if (!(Test-Path $blender)) {throw 'Blender 5.3 executable unavailable'}
New-Item -Path $addon -ItemType Directory -Force | Out-Null
Copy-Item (Join-Path $root 'fwai_live_bridge_addon.py') (Join-Path $addon 'fwai_live_bridge_addon.py') -Force
Copy-Item (Join-Path $root 'fwai_geometry_preview.py') (Join-Path $addon 'fwai_geometry_preview.py') -Force
& $blender --background --python (Join-Path $root 'enable_vq04.py')
if ($LASTEXITCODE -ne 0) {throw 'Blender add-on enable failed'}
Write-Output 'FWAI_VQ04_ADDON_INSTALLED'
Write-Output 'Open the VQ04 scene in a NEW Blender window; use N > Future Works > Live Sync.'
