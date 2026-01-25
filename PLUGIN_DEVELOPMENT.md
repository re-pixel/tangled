# Tangled Plugin Development Manual

This guide explains how to extend the Tangled architecture by creating new plugins. Tangled uses a **Microkernel Architecture** where the core platform is minimal, and strict functionality is added via plugins.

There are currently two types of plugins you can build:
1.  **Data Source Plugins**: Read files (JSON, CSV, XML, etc.) and convert them into a `Graph`.
2.  **Visualizer Plugins**: Take a `Graph` and convert it into a generic representation (HTML/JSON) for rendering.

---

## 1. Prerequisites

Before starting, understand that all plugins share a common language: **`tangled-api`**.
Your plugin **must** depend on this package to access the core data structures:
*   `Graph`
*   `Node`
*   `Edge`
*   `DataSourcePlugin` (Base Class)
*   `VisualizerPlugin` (Base Class)

---

## 2. Project Structure

Every plugin is a standalone Python project. Do not modify the existing `platform` or `api` code. Create a new folder for your plugin at the root of the workspace.

**Recommended Structure:**
```text
my-new-plugin/                  <-- Project Root
├── pyproject.toml              <-- Configuration & Entry Points
├── README.md
└── src/
    └── tangled_my_plugin/      <-- Python Package (use unique name)
        ├── __init__.py
        └── plugin.py           <-- Implementation Logic
```

---

## 3. Creating a Data Source Plugin

**Goal:** Read a file format and return a `Graph` object.

### Step A: Configuration (`pyproject.toml`)
Define your project and declare the dependency on `tangled-api`.

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "tangled-my-datasource"
version = "0.1.0"
dependencies = ["tangled-api"]  # <--- CRITICAL

# Register the plugin so Platform can find it
[project.entry-points."tangled.datasource"]
my_loader = "tangled_my_plugin.plugin:MyDataSource"
```

### Step B: Implementation (`plugin.py`)
Inherit from `DataSourcePlugin` and implement `load()`.

```python
from typing import List, Any
from tangled_api.plugins import DataSourcePlugin, PluginParameter
from tangled_api.model import Graph, Node, Edge

class MyDataSource(DataSourcePlugin):
    @property
    def name(self) -> str:
        return "My Custom Loader"

    @property
    def description(self) -> str:
        return "Loads data from .custom files"

    @property
    def parameters(self) -> List[PluginParameter]:
        # Define arguments the user needs to provide in the UI/API
        return [
            PluginParameter(
                name="filepath", 
                param_type=str, 
                description="Path to the file", 
                required=True
            )
        ]

    def load(self, **params: Any) -> Graph:
        filepath = params.get("filepath")
        
        # 1. Create an empty graph
        graph = Graph(directed=True)
        
        # 2. Your logic to read the file
        # with open(filepath) as f: ...
        
        # 3. Populate the graph
        # graph.add_node(Node(id="a", attributes={"type": "demo"}))
        # graph.add_edge(Edge(id="e1", source_id="a", target_id="b"))
        
        return graph
```

---

## 4. Creating a Visualizer Plugin

**Goal:** Take a `Graph` object and return an HTML string.

### Step A: Configuration (`pyproject.toml`)
Same as above, but register under the `tangled.visualizer` group.

```toml
# ... [project] section same as above ...

[project.entry-points."tangled.visualizer"]
my_viz = "tangled_my_visualizer.plugin:MyVisualizer"
```

### Step B: Implementation (`plugin.py`)
Inherit from `VisualizerPlugin` and implement `render()`.

```python
from tangled_api.plugins import VisualizerPlugin
from tangled_api.model import Graph

class MyVisualizer(VisualizerPlugin):
    @property
    def name(self) -> str:
        return "My Custom Visualizer"

    @property
    def description(self) -> str:
        return "Renders graph as a list of items"

    def render(self, graph: Graph) -> str:
        # Generate HTML representation
        html = ["<ul>"]
        
        for node_id, node in graph.nodes.items():
            label = node.attributes.get("label", node_id)
            html.append(f"<li>{label}</li>")
            
        html.append("</ul>")
        return "\n".join(html)
```

---

## 5. Installing & Verifying

Once your code is written, you must install the plugin in "editable" mode so the Platform can discover the entry points.

1.  **Activate your environment**:
    ```bash
    source venv/bin/activate
    ```

2.  **Install your plugin**:
    ```bash
    cd my-new-plugin
    pip install -e .
    ```

3.  **Verify**:
    Restart the Tangled application. Your new plugin should automatically appear in the API list (`/api/plugins/datasources` or `/api/plugins/visualizers`) and in the generic UI dropdowns.
