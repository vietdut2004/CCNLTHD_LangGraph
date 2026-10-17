$ErrorActionPreference = "Stop"

$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$langgraph = Join-Path $projectDir ".venv\Scripts\langgraph.exe"

if (-not (Test-Path $langgraph)) {
    throw "Khong tim thay .venv\Scripts\langgraph.exe. Hay tao .venv Python 3.11+ va chay: .venv\Scripts\python.exe -m pip install -r requirements.txt"
}

& $langgraph dev --no-browser
