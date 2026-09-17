param([switch]$Enable)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskName = 'ASTRA Local Safe Worker'
if ($Enable) {
  # One hidden host starts at user logon, immediately runs a cycle, then sleeps.
  # It never attaches to, opens, closes, or focuses an interactive terminal.
  schtasks.exe /End /TN $taskName 2>$null | Out-Null
  schtasks.exe /Create /TN $taskName /TR "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$root\run-worker-daemon.ps1`"" /SC ONLOGON /RL LIMITED /F | Out-Host
  Write-Host "One hidden persistent worker host created for logon; cycles run every 15 minutes."
} else { Write-Host 'Dry run only. Re-run with -Enable after reviewing this script.' }
