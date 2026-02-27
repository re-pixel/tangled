# Tangled Graph Explorer - Installation Script (Windows)
# This script sets up the complete development environment.
# Run in PowerShell: .\install.ps1

$ErrorActionPreference = "Stop"

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
& $Py $PyArgs -c "import venv, ensurepip" 2>&1 | Out-Null
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

Write-Host "Installing components..."
$components = @(
    @{ n = "1/7"; name = "tangled-api"; path = ".\api" },
    @{ n = "2/7"; name = "tangled-platform"; path = ".\platform" },
    @{ n = "3/7"; name = "tangled-json-datasource"; path = ".\json-datasource" },
    @{ n = "4/7"; name = "tangled-xml-datasource"; path = ".\xml-datasource" },
    @{ n = "5/7"; name = "tangled-simple-visualizer"; path = ".\simple-visualizer" },
    @{ n = "6/7"; name = "tangled-block-visualizer"; path = ".\block-visualizer" },
    @{ n = "7/7"; name = "tangled-graph-explorer"; path = ".\graph-explorer" }
)
foreach ($c in $components) {
    Write-Host "  [$($c.n)] Installing $($c.name)..."
    & $pip install -e $c.path --quiet
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host "  $($c.name) installed" -ForegroundColor Green
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
