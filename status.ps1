param([Parameter(Mandatory=$true)][string]$JobId)
$ErrorActionPreference = 'Stop'
$response = Invoke-RestMethod -Method Get -Uri "http://localhost:5678/webhook/futureworks/status?job_id=$JobId"
Write-Host "Status: $($response.status)" -ForegroundColor Cyan
Write-Host "Stage: $($response.stage)"
if ($response.error) { Write-Host "Error: $($response.error)" -ForegroundColor Red }
if ($response.outputs) {
  Write-Host 'Files: copy these paths from the OUTPUT_DIR you set in .env:'
  $response.outputs | Format-List
}
