# One hidden, session-scoped worker host.  It runs once immediately after logon
# and stays asleep between safe 15-minute worker cycles; it never owns or
# focuses an interactive terminal window.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$logDir = Join-Path $root 'data\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir 'scheduled-worker.log'
$mutex = New-Object System.Threading.Mutex($false, 'Local\ASTRA.Local.SafeWorker')
if (-not $mutex.WaitOne(0, $false)) { exit 0 }
try {
  while ($true) {
    $stamp = Get-Date -Format 'o'
    "[$stamp] persistent worker cycle starting" | Out-File -Append -Encoding utf8 $log
    & "$root\.venv\Scripts\python.exe" -m app.worker *>&1 | Out-File -Append -Encoding utf8 $log
    "[$(Get-Date -Format 'o')] persistent worker cycle complete; sleeping 900 seconds" | Out-File -Append -Encoding utf8 $log
    Start-Sleep -Seconds 900
  }
} finally {
  $mutex.ReleaseMutex() | Out-Null
  $mutex.Dispose()
}
