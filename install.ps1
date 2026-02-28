# Tangled Graph Explorer - Installation Script (Windows)
# This script sets up the complete development environment.
# Run in PowerShell: .\install.ps1

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\api")) {
    Write-Host "Error: Run this script from the repository root (the folder containing api, platform, etc.)." -ForegroundColor Red
    exit 1
}

Write-Host "========================================="
Write-Host "Tangled Graph Explorer - Installation"
Write-Host "========================================="
Write-Host ""

# Find Python (try 'python', then 'py -3')
$Py = $null
$PyArgs = @()
if (Get-Command python -ErrorAction SilentlyContinue) {
    $Py = "python"
    $PyArgs = @()
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $Py = "py"
    $PyArgs = @("-3")
} else {
    Write-Host "Error: Python not found. Install Python 3.10+ from https://www.python.org/downloads/ and ensure 'Add Python to PATH' is checked." -ForegroundColor Red
    exit 1
}

# Get version (e.g. "Python 3.12.3" -> 3.12)
$versionOutput = & $Py $PyArgs --version 2>&1 | Out-String
if ($versionOutput -match "Python (\d+\.\d+)") {
    $pythonVersion = $Matches[1]
} else {
    Write-Host "Error: Could not detect Python version." -ForegroundColor Red
    exit 1
}

$required = [version]"3.10"
$current = [version]($pythonVersion + ".0")
if ($current -lt $required) {
    Write-Host "Error: Python 3.10 or higher is required (found $pythonVersion)." -ForegroundColor Red
    exit 1
}

Write-Host "Python $pythonVersion detected" -ForegroundColor Green
Write-Host ""

# Check if venv and ensurepip are available
& $Py $PyArgs -c "import venv, ensurepip" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: venv/ensurepip is not available." -ForegroundColor Red
    Write-Host "Reinstall Python from https://www.python.org/downloads/ and run the installer again."
    Write-Host "Ensure you check 'Add Python to PATH' and that pip is installed (default)." -ForegroundColor Yellow
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    & $Py $PyArgs -m venv venv
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host "Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# Use venv's pip directly (no activation needed in script)
$pip = ".\venv\Scripts\pip.exe"
$python = ".\venv\Scripts\python.exe"

Write-Host "Upgrading pip..."
& $pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "pip upgraded" -ForegroundColor Green
Write-Host ""

# Discover components: direct subdirs with pyproject.toml, order api → platform → others (sorted) → graph-explorer
$middle = Get-ChildItem -Directory | Where-Object {
    $_.Name -notin @("api", "platform", "graph-explorer", "venv") -and
    (Test-Path (Join-Path $_.FullName "pyproject.toml"))
} | Select-Object -ExpandProperty Name | Sort-Object
$componentDirs = @("api", "platform") + [array]$middle
if (Test-Path ".\graph-explorer\pyproject.toml") { $componentDirs += "graph-explorer" }
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

Write-Host "Installing components..."
$total = $componentPaths.Count
$n = 0
foreach ($path in $componentPaths) {
    $n++
    $dirName = Split-Path -Leaf $path
    $pkg = Get-PackageName $dirName
    Write-Host "  [$n/$total] Installing $pkg..."
    & $pip install -e $path --quiet
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host "  $pkg installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================="
Write-Host "Installation complete!"
Write-Host "========================================="
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  tangled"
Write-Host ""
Write-Host "Or run without activating:"
Write-Host "  .\venv\Scripts\tangled.exe"
Write-Host ""
Write-Host "Then open http://localhost:5000 in your browser." -ForegroundColor Cyan
Write-Host ""
