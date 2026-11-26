$ErrorActionPreference='Stop'
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-04'
$add=Join-Path $env:APPDATA 'Blender Foundation\Blender\5.3\scripts\addons'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
if (!(Test-Path $blender)) {throw 'Blender 5.3 runtime missing'}
New-Item -ItemType Directory -Path $add -Force | Out-Null
foreach($f in @('fwai_film_contact.py','fwai_film_grip.py','fwai_live_bridge_addon.py')){
  Copy-Item (Join-Path $root $f) (Join-Path $add $f) -Force
}
& $blender --background --python (Join-Path $root 'enable_vq04_04.py')
if ($LASTEXITCODE -ne 0) {throw 'VQ04.04 add-on initialization failed'}
Write-Output 'FWAI_VQ04_04_LOCAL_FILM_ADDON_INSTALLED'
Write-Output 'Open a fresh VQ04.04 Blender window; older windows still use older loaded addon modules.'
