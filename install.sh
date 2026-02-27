#!/bin/bash

# Tangled Graph Explorer - Installation Script
# This script sets up the complete development environment.

set -e  # Exit on error

echo "========================================="
echo "Tangled Graph Explorer - Installation"
echo "========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Check if venv module is available
if ! python3 -c "import venv, ensurepip" 2>/dev/null; then
    echo "Error: python3-venv is not installed."
    echo "Run: sudo apt install python3.${PYTHON_VERSION#*.}-venv"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"

# Install components in dependency order
echo ""
echo "Installing components..."

echo "  [1/7] Installing tangled-api..."
pip install -e ./api --quiet
echo "  ✓ tangled-api installed"

echo "  [2/7] Installing tangled-platform..."
pip install -e ./platform --quiet
echo "  ✓ tangled-platform installed"

echo "  [3/7] Installing tangled-json-datasource..."
pip install -e ./json-datasource --quiet
echo "  ✓ tangled-json-datasource installed"

echo "  [4/7] Installing tangled-xml-datasource..."
pip install -e ./xml-datasource --quiet
echo "  ✓ tangled-xml-datasource installed"

echo "  [5/7] Installing tangled-simple-visualizer..."
pip install -e ./simple-visualizer --quiet
echo "  ✓ tangled-simple-visualizer installed"

echo "  [6/7] Installing tangled-block-visualizer..."
pip install -e ./block-visualizer --quiet
echo "  ✓ tangled-block-visualizer installed"

echo "  [7/7] Installing tangled-graph-explorer..."
pip install -e ./graph-explorer --quiet
echo "  ✓ tangled-graph-explorer installed"

echo ""
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo ""
echo "  source venv/bin/activate"
echo "  tangled"
echo ""
echo "Or:"
echo ""
echo "  source venv/bin/activate"
echo "  flask --app tangled_graph_explorer run --debug"
echo ""
echo "Then open http://localhost:5000 in your browser."
echo ""
