# Tangled Graph Explorer - Reinstall Script (Windows)
# Use this to reinstall all components after making changes.
# Run from repo root: .\scripts\reinstall.ps1  or  make reinstall

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\api")) {
    Write-Host "Error: Run this script from the repository root (the folder containing api, platform, etc.)." -ForegroundColor Red
    exit 1
}

Write-Host "Reinstalling all Tangled components..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "venv")) {
    Write-Host "Error: Virtual environment not found. Run scripts/install.ps1 or make install first." -ForegroundColor Red
    exit 1
}

$pip = ".\venv\Scripts\pip.exe"

# Discover components (same order as install.ps1): api → platform → others (sorted) → graph-explorer
$middle = Get-ChildItem -Directory | Where-Object {
    $_.Name -notin @("api", "platform", "graph-explorer", "graph-explorer-django", "venv") -and
    (Test-Path (Join-Path $_.FullName "pyproject.toml"))
} | Select-Object -ExpandProperty Name | Sort-Object
$componentDirs = @("api", "platform") + [array]$middle
if (Test-Path ".\graph-explorer\pyproject.toml") { $componentDirs += "graph-explorer" }
if (Test-Path ".\graph-explorer-django\pyproject.toml") { $componentDirs += "graph-explorer-django" }
$componentPaths = $componentDirs | ForEach-Object { ".\$_" }

# Get package name from pyproject.toml (fallback: tangled-<dirname>)
function Get-PackageName($dir) {
    $pyproject = Join-Path $dir "pyproject.toml"
    if (-not (Test-Path $pyproject)) { return "tangled-$dir" }
    $content = Get-Content $pyproject -Raw -ErrorAction SilentlyContinue
    if ($content -match 'name\s*=\s*"([^"]+)"') { return $Matches[1] }
    if ($content -match "name\s*=\s*'([^']+)'") { return $Matches[1] }
    return "tangled-$dir"
}

# Uninstall existing packages (use name from each pyproject.toml)
$packageNames = $componentDirs | ForEach-Object { Get-PackageName $_ }
Write-Host "Removing existing installations..."
& $pip uninstall -y @packageNames 2>$null
# pip uninstall may return non-zero if a package wasn't installed; script continues

# Clean build artifacts (only in component dirs, not venv)
Write-Host "Cleaning build artifacts..."
foreach ($path in $componentPaths) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Recurse -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $path -Recurse -Directory -Filter "build" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $path -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Reinstall
Write-Host "Reinstalling components..."
foreach ($path in $componentPaths) {
    & $pip install -e $path --quiet
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

Write-Host ""
Write-Host "All components reinstalled!" -ForegroundColor Green
Write-Host ""
Write-Host "Starting server..."
& .\venv\Scripts\tangled.exe
