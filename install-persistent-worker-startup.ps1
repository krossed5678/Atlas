# Creates a per-user Startup shortcut.  This is used when the existing Task
# Scheduler task was created by an administrator and cannot be replaced by this
# non-elevated session.  The shortcut launches no visible console window.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'ASTRA Persistent Local Worker.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$shortcut.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$root\run-worker-daemon.ps1`""
$shortcut.WorkingDirectory = $root
$shortcut.WindowStyle = 7 # minimized/hidden launch surface; PowerShell also receives WindowStyle Hidden.
$shortcut.Description = 'ASTRA persistent hidden worker, one host per user session'
$shortcut.Save()
Write-Host "Created user-logon startup shortcut: $shortcutPath"
