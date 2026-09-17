$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$logDir = Join-Path $root 'data\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$mutex = New-Object System.Threading.Mutex($false, 'Local\ASTRA.Local.SafeWorker')
# Compatibility guard for the old administrator-owned 15-minute task.  Once
# the persistent logon host is present it owns this mutex, so the legacy task
# exits before invoking Python or creating any visible terminal surface.
if (-not $mutex.WaitOne(0, $false)) { exit 0 }
$stamp = Get-Date -Format 'o'
"[$stamp] scheduled worker starting" | Out-File -Append -Encoding utf8 (Join-Path $logDir 'scheduled-worker.log')
try {
  & "$root\.venv\Scripts\python.exe" -m app.worker *>&1 | Out-File -Append -Encoding utf8 (Join-Path $logDir 'scheduled-worker.log')
  $workerExitCode = $LASTEXITCODE
  exit $workerExitCode
} finally { $mutex.ReleaseMutex() | Out-Null; $mutex.Dispose() }
