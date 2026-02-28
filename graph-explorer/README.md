# Tangled Graph Explorer

Flask web application for interactive graph visualization.

## Features

- **Main View**: Central graph visualization with pan, zoom, drag-drop
- **Tree View**: Hierarchical expandable/collapsible tree representation
- **Bird View**: Minimap with viewport indicator
- **Search**: Text search across node attributes
- **Filter**: Query-based filtering (attribute comparisons)
- **CLI**: In-browser terminal for graph manipulation
- **Multiple Workspaces**: Work with multiple graphs simultaneously

## Installation

From the repository root, install all components and activate the venv:

**Linux / macOS:**
```bash
./install.sh
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\install.ps1
.\venv\Scripts\Activate.ps1
```

**Or install manually** (any platform): create venv, activate it, then `pip install -e ./api` (and the rest; see main [README](../README.md)).

## Running the Application

```bash
tangled
# Or: flask --app tangled_graph_explorer run --debug
```

Then open http://localhost:5000 in your browser.

## Project Structure

```
graph-explorer/
├── src/
│   └── tangled_graph_explorer/
│       ├── __init__.py          # Flask app factory
│       ├── routes.py            # View routes
│       ├── api.py               # REST API endpoints
│       ├── cli.py               # CLI entry point
│       ├── templates/           # Jinja2 templates
│       │   ├── base.html
│       │   ├── index.html
│       │   └── workspace.html
│       └── static/
│           ├── css/
│           │   └── style.css
│           └── js/
│               ├── main.js
│               ├── graph.js
│               ├── treeview.js
│               └── birdview.js
├── pyproject.toml
└── README.md
```
