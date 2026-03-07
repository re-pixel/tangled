# Tangled Simple Visualizer Plugin

Minimalist visualizer that displays graph nodes as simple shapes (circles).

## Features

- Clean, uncluttered view of graph structure
- Nodes displayed as circles with ID/name label
- Edges shown as lines connecting nodes
- Ideal for understanding overall graph topology

## Installation

```bash
pip install -e /path/to/simple-visualizer
```

## Usage

The plugin is automatically discovered by the platform.

```python
from tangled_platform import Platform

platform = Platform()
workspace = platform.create_workspace()
workspace.load_data(...)

# Render with simple visualizer
html = workspace.render(platform.get_visualizer("simple"))
```

## Output

Generates HTML/SVG structure for D3.js rendering with:
- Circle nodes with ID labels
- Line edges connecting nodes
- Data attributes for interactivity (mouseover, selection)
