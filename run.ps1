# Start Ghost Job Radar on http://127.0.0.1:8000 (creates the virtual environment on first run).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv")) {
    py -3.13 -m venv .venv
    .\.venv\Scripts\python -m pip install --quiet -r requirements.txt
}
if (-not (Test-Path "data\ba_engpass.csv")) {
    .\.venv\Scripts\python scripts\update_baselines.py
}
Start-Process "http://127.0.0.1:8000"
.\.venv\Scripts\python -m uvicorn ghostradar.main:app --port 8000
