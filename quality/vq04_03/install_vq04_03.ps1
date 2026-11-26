$ErrorActionPreference='Stop'
$root=Join-Path $env:USERPROFILE 'Documents\futureworks-vq04-03'
$add=Join-Path $env:APPDATA 'Blender Foundation\Blender\5.3\scripts\addons'
$blender=Join-Path $env:ProgramFiles 'Blender Foundation\Blender 5.3\blender.exe'
if (!(Test-Path $blender)){throw 'Blender 5.3 executable missing'}
New-Item -Path $add -ItemType Directory -Force | Out-Null
foreach($file in @('fwai_live_bridge_addon.py','fwai_hand_tool_preview.py','fwai_grip_contact.py')){
    Copy-Item (Join-Path $root $file) (Join-Path $add $file) -Force
}
& $blender --background --python (Join-Path $root 'enable_vq04_03.py')
if ($LASTEXITCODE -ne 0){throw 'VQ04.03 add-on enable failed'}
Write-Output 'FWAI_VQ04_03_BLENDER_ADDON_INSTALLED'
Write-Output 'Open a NEW Blender window with VQ04.03 scene; preexisting windows retain their old loaded addon modules.'
