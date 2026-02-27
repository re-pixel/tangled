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

# Discover components: direct subdirs with pyproject.toml, order api → platform → others (sorted) → graph-explorer
COMPONENTS="api platform"
MIDDLE=$(for d in */; do
  d="${d%/}"
  [ "$d" = "api" ] || [ "$d" = "platform" ] || [ "$d" = "graph-explorer" ] || [ "$d" = "venv" ] && continue
  [ -f "$d/pyproject.toml" ] && echo "$d"
done | sort)
[ -f "graph-explorer/pyproject.toml" ] && COMPONENTS="$COMPONENTS $MIDDLE graph-explorer" || COMPONENTS="$COMPONENTS $MIDDLE"
COMPONENTS=$(echo $COMPONENTS | xargs)

# Get package name from pyproject.toml (fallback: tangled-<dirname>)
get_pkg_name() {
  local f="$1/pyproject.toml" pkg
  pkg=$(sed -n 's/^name[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "$f" 2>/dev/null)
  [ -z "$pkg" ] && pkg=$(sed -n "s/^name[[:space:]]*=[[:space:]]*'\([^']*\)'.*/\1/p" "$f" 2>/dev/null)
  [ -z "$pkg" ] && pkg="tangled-$1"
  echo "$pkg"
}

# Install components in dependency order
echo ""
echo "Installing components..."
n=0
total=$(echo $COMPONENTS | wc -w)
for dir in $COMPONENTS; do
  n=$((n + 1))
  pkg=$(get_pkg_name "$dir")
  echo "  [$n/$total] Installing $pkg..."
  pip install -e "./$dir" --quiet
  echo "  ✓ $pkg installed"
done

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
