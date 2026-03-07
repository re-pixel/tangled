# Tangled Block Visualizer Plugin

Detailed visualizer that displays graph nodes as rectangles showing all attributes.

## Features

- Nodes displayed as rectangles/blocks with a colored header
- Header shows the node UUID/ID
- Lists all node attributes as key-value rows
- Alternating row background for readability
- Edges shown as lines connecting blocks (with arrowheads for directed graphs)
- Visibility culling — only nodes in the current viewport are rendered
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

## How It Works

### Python Side (`__init__.py`)

`BlockVisualizer` implements `VisualizerPlugin` and is responsible for serializing the graph into JSON and injecting it into the HTML template.

For each node it produces:

```json
{
  "id": "<node uuid>",
  "label": "<value of first attribute, or node id if no attributes>",
  "attributes": [
    { "name": "attr_name", "value": "attr_value", "type": "string" }
  ]
}
```

For each edge:

```json
{
  "id": "<edge id>",
  "source": "<source node id>",
  "target": "<target node id>",
  "attributes": []
}
```

`datetime` values are automatically converted to ISO 8601 strings via `.isoformat()`.

The template receives:
| Variable | Description |
|----------|-------------|
| `name` | Unique identifier for the SVG element (`id(graph)`) |
| `nodes` | List of serialized node dicts |
| `edges` | List of serialized edge dicts |
| `directed` | Boolean — whether edges have direction |

### Template Side (`template/template.html`)

The template renders an `<svg>` element and a `<script>` block. On load, the script uses D3.js to build the SVG structure:

- One `<g class="block-node" id="<node-id>">` per node containing:
  - A border `<rect>` (white fill, blue stroke)
  - A header `<rect>` (blue fill)
  - A `<text>` for the node ID in the header
  - One row per attribute: alternating background rect, divider line, name text, value text
- One `<line class="plugin-link">` per edge

Node dimensions are computed dynamically based on the number of attributes:

```
node height = HEADER_H (28px) + max(1, attr_count) * ROW_H (20px) + 4px
node width  = max(160px, header_text_width + 2 * PAD_X)
```

The SVG element exposes two `data-` attributes consumed by `GraphRenderer`:

```html
<svg data-node-selector=".block-node" data-link-selector=".plugin-link"></svg>
```

These tell the platform JS which elements are nodes and which are edges, so it can attach the force simulation, drag, zoom, and culling.

### Rendering Pipeline

```
BlockVisualizer.render(graph)
    └── Jinja2 template renders HTML string
            └── Injected into DOM by WorkspaceController
                    └── GraphRenderer.attach() picks up .block-node / .plugin-link
                            └── D3 force simulation + culling takes over
```

## Output

Generates an HTML fragment (no `<html>/<body>`) containing:

- `<style>` block with scoped CSS
- `<svg>` element with data attributes for GraphRenderer
- `<script>` block that renders nodes/edges via D3.js on `document.fonts.ready`

## File Structure

```
block-visualizer/
├── __init__.py          # BlockVisualizer plugin class
└── template/
    └── template.html    # Jinja2 template (style + svg + d3 render script)
```

## Styling

All colors are defined as CSS classes on SVG elements so they can be overridden.
