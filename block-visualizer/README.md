# Tangled Block Visualizer Plugin

Detailed visualizer that displays graph nodes as rectangles showing all attributes.

## Features

- Nodes displayed as rectangles/blocks
- Shows node ID/name as header
- Lists all attributes with their values
- Edges shown as lines connecting blocks
- Ideal for detailed data inspection

## Installation

```bash
pip install -e /path/to/block-visualizer
```

## Usage

The plugin is automatically discovered by the platform.

```python
from tangled_platform import Platform

platform = Platform()
workspace = platform.create_workspace()
workspace.load_data(...)

# Render with block visualizer
html = workspace.render(platform.get_visualizer("block"))
```

## Output

Generates HTML/SVG structure for D3.js rendering with:
- Rectangle nodes with header and attribute list
- Line edges connecting nodes
- Data attributes for interactivity
