# Tangled Platform

Core platform library for the Tangled graph visualization system.

## Overview

This library provides:
- **Plugin discovery**: Automatic detection of installed data source and visualizer plugins
- **Workspace management**: Multiple workspaces with independent graphs, filters, and searches
- **Search & Filter**: Graph querying with subgraph generation
- **CLI**: Command-line interface for graph manipulation

## Installation

```bash
pip install -e /path/to/platform
```

## Dependencies

- `tangled-api` (must be installed first)

## Usage

```python
from tangled_platform import Platform

# Initialize platform (discovers installed plugins)
platform = Platform()

# List available plugins
print(platform.data_sources)
print(platform.visualizers)

# Create a workspace
workspace = platform.create_workspace()

# Load data using a plugin
workspace.load_data("json-datasource", file_path="data.json")

# Apply filters and search
workspace.filter("age > 25")
workspace.search("John")

# Render with a visualizer
html = workspace.render("simple-visualizer")
```
