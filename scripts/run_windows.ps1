# One-step Windows setup + launch. Usage: powershell -ExecutionPolicy Bypass -File scripts/run_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts\train_model.py
.\.venv\Scripts\python -m streamlit run app.py
