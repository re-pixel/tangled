# Tangled Graph Explorer - Reinstall Script (Windows)
# Use this to reinstall all components after making changes.
# Run in PowerShell: .\reinstall.ps1

$ErrorActionPreference = "Stop"

Write-Host "Reinstalling all Tangled components..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "venv")) {
    Write-Host "Error: Virtual environment not found. Run install.ps1 first." -ForegroundColor Red
    exit 1
}

$pip = ".\venv\Scripts\pip.exe"

# Uninstall existing packages
Write-Host "Removing existing installations..."
& $pip uninstall -y tangled-api tangled-platform tangled-json-datasource tangled-xml-datasource tangled-simple-visualizer tangled-block-visualizer tangled-graph-explorer 2>$null
# pip uninstall may return non-zero if a package wasn't installed; script continues

# Clean build artifacts
Write-Host "Cleaning build artifacts..."
Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Directory -Filter "build" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Reinstall
Write-Host "Reinstalling components..."
$components = @(
    ".\api",
    ".\platform",
    ".\json-datasource",
    ".\xml-datasource",
    ".\simple-visualizer",
    ".\block-visualizer",
    ".\graph-explorer"
)
foreach ($path in $components) {
    & $pip install -e $path --quiet
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Write-Host ""
Write-Host "All components reinstalled!" -ForegroundColor Green
Write-Host ""
Write-Host "Starting server..."
& .\venv\Scripts\tangled.exe
