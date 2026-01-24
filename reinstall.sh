#!/bin/bash

# Tangled Graph Explorer - Reinstall Script
# Use this to reinstall all components after making changes.

set -e

echo "Reinstalling all Tangled components..."

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Run install.sh first."
    exit 1
fi

source venv/bin/activate

# Uninstall existing packages
echo "Removing existing installations..."
pip uninstall -y tangled-api tangled-platform tangled-json-datasource tangled-xml-datasource tangled-simple-visualizer tangled-block-visualizer tangled-graph-explorer 2>/dev/null || true

# Clean build artifacts
echo "Cleaning build artifacts..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Reinstall
echo "Reinstalling components..."
pip install -e ./api --quiet
pip install -e ./platform --quiet
pip install -e ./json-datasource --quiet
pip install -e ./xml-datasource --quiet
pip install -e ./simple-visualizer --quiet
pip install -e ./block-visualizer --quiet
pip install -e ./graph-explorer --quiet

echo ""
echo "✓ All components reinstalled!"
echo ""
echo "Starting server..."
tangled
