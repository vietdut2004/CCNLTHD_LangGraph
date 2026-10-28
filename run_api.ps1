$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPython = Join-Path $projectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $projectPython)) { $projectPython = "python" }
$env:PYTHONIOENCODING = "utf-8"
Push-Location $projectDir
try { & $projectPython (Join-Path $projectDir "start_api.py"); $runExitCode = $LASTEXITCODE }
finally { Pop-Location }
exit $runExitCode
