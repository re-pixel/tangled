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

# Discover components (same order as install.sh): api → platform → others (sorted) → graph-explorer
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

# Uninstall existing packages (use name from each pyproject.toml)
echo "Removing existing installations..."
for dir in $COMPONENTS; do
  pkg=$(get_pkg_name "$dir")
  pip uninstall -y "$pkg" 2>/dev/null || true
done

# Clean build artifacts (only in component dirs, not venv)
echo "Cleaning build artifacts..."
for dir in $COMPONENTS; do
  [ -d "$dir" ] && find "$dir" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
  [ -d "$dir" ] && find "$dir" -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
  [ -d "$dir" ] && find "$dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
done

# Reinstall
echo "Reinstalling components..."
for dir in $COMPONENTS; do
  pip install -e "./$dir" --quiet
done

echo ""
echo "✓ All components reinstalled!"
echo ""
echo "Starting server..."
tangled
