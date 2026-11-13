# FutureWorks one-prompt submission UI for Windows PowerShell.
# n8n runs only on your own machine at http://localhost:5678.
$ErrorActionPreference = 'Stop'
Write-Host "`nFutureWorks Studio - Create Production Job" -ForegroundColor Cyan
$brief = Read-Host 'Describe your video concept'
if ([string]::IsNullOrWhiteSpace($brief)) { throw 'A video concept is required.' }
$modeEntry = Read-Host 'Mode? [D]ry run (free) or [L]ive (paid); default D'
$mode = if ($modeEntry -match '^[Ll]') { 'live' } else { 'dry_run' }
$scenes = Read-Host 'How many scene clips? 1-4 (default 2)'
if (-not $scenes) { $scenes = '2' }
$sceneCount = [int]$scenes
$budget = Read-Host 'Max Runway video spend in USD (default 3)'
if (-not $budget) { $budget = '3' }
$payload = @{
  prompt = $brief
  mode = $mode
  scene_count = $sceneCount
  scene_duration = 5
  runway_budget_usd = [double]$budget
} | ConvertTo-Json -Compress
Write-Host "`nSubmitting to local n8n..."
$response = Invoke-RestMethod -Method Post -Uri 'http://localhost:5678/webhook/futureworks/produce' -Body $payload -ContentType 'application/json'
$response | Format-List
Write-Host "`nSave this job ID: $($response.id)" -ForegroundColor Green
Write-Host 'To check later, run: .\status.ps1 -JobId YOUR_JOB_ID'
