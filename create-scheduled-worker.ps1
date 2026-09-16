param([switch]$Enable)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskName = 'ASTRA Local Safe Worker'
if ($Enable) {
  # This task owns its own hidden PowerShell process. It never attaches to, closes,
  # or changes the window state of an interactive terminal/Codex session.
  schtasks.exe /Create /TN $taskName /TR "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$root\run-worker.ps1`"" /SC MINUTE /MO 15 /F | Out-Host
  Write-Host "Hidden background task created: $taskName"
} else { Write-Host 'Dry run only. Re-run with -Enable after reviewing this script.' }
