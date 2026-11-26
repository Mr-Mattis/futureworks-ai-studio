$ErrorActionPreference='Stop'
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-06'
$addons=Join-Path $env:APPDATA 'Blender Foundation\Blender\5.3\scripts\addons'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
if(!(Test-Path $blender)){throw 'Blender 5.3 missing'}
New-Item -ItemType Directory -Path $addons -Force|Out-Null
Copy-Item (Join-Path $root 'fwai_vq06_coupled_review.py') (Join-Path $addons 'fwai_vq06_coupled_review.py') -Force
& $blender --background --python (Join-Path $root 'enable_vq06.py')
if($LASTEXITCODE -ne 0){throw 'VQ06 Blender add-on registration failed'}
Write-Output 'FWAI VQ04.06 live review installed'
