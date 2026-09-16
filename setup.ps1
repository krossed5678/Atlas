$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = 'C:\Users\koanr\AppData\Local\Programs\Python\Python312\python.exe'
if (!(Test-Path $python)) { throw 'Python 3.12 is required. Install it, then rerun this script.' }
& $python -m venv "$root\.venv"
& "$root\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$root\.venv\Scripts\python.exe" -m pip install -r "$root\requirements.txt"
New-Item -ItemType Directory -Force -Path "$root\data", "$root\data\properties", "$root\data\logs" | Out-Null
Copy-Item "$root\.env.example" "$root\.env" -ErrorAction SilentlyContinue
Write-Host 'ASTRA setup complete. Add credentials to Windows Credential Manager or .env, then run start.ps1.'
