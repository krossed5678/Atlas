$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$logDir = Join-Path $root 'data\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format 'o'
"[$stamp] scheduled worker starting" | Out-File -Append -Encoding utf8 (Join-Path $logDir 'scheduled-worker.log')
& "$root\.venv\Scripts\python.exe" -m app.worker *>&1 | Out-File -Append -Encoding utf8 (Join-Path $logDir 'scheduled-worker.log')
$workerExitCode = $LASTEXITCODE
exit $workerExitCode
