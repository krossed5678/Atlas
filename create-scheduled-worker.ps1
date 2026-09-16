param([switch]$Enable)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskName = 'ASTRA Local Safe Worker'
if ($Enable) {
  schtasks.exe /Create /TN $taskName /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$root\run-worker.ps1`"" /SC MINUTE /MO 15 /F | Out-Host
  Write-Host "Scheduled task created: $taskName"
} else { Write-Host 'Dry run only. Re-run with -Enable after reviewing this script.' }
