# Tangled - Graph Visualization Platform

A modular, plugin-based graph visualization platform supporting multiple data sources and visualization styles.

## Project Structure

```
tangled/
├── api/                      # Core API library (tangled-api)
│   └── src/tangled_api/      # Graph model, plugin interfaces
├── platform/                 # Platform library (tangled-platform)
│   └── src/tangled_platform/ # Plugin discovery, workspaces, CLI
├── json-datasource/          # JSON data source plugin
│   └── src/tangled_json_datasource/
├── xml-datasource/           # XML data source plugin
│   └── src/tangled_xml_datasource/
├── simple-visualizer/        # Simple circle-based visualizer
│   └── src/tangled_simple_visualizer/
├── block-visualizer/         # Block/rectangle visualizer with attributes
│   └── src/tangled_block_visualizer/
├── graph-explorer/           # Flask web application
│   └── src/tangled_graph_explorer/
├── install.sh                # Installation script
└── README.md                 # This file
```

## Features

- **Multiple Data Sources**: Load graphs from JSON, XML (extensible via plugins)
- **Multiple Visualizers**: Simple and Block views (extensible via plugins)
- **Three View Modes**: Main View, Tree View, Bird View (synchronized)
- **Search & Filter**: Query-based graph filtering
- **CLI**: In-browser terminal for graph manipulation
- **Workspaces**: Multiple independent graph sessions

## Team

- Member 1: [Name] - [Role/Components]
- Member 2: [Name] - [Role/Components]
- Member 3: [Name] - [Role/Components]
- Member 4: [Name] - [Role/Components]

## Requirements

- Python 3.10+
- pip

## Installation

### Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd tangled

# Run the install script
./install.sh

# Start the application
tangled
# or: flask --app tangled_graph_explorer run --debug
```

### Manual Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install components in dependency order
pip install -e ./api
pip install -e ./platform
pip install -e ./json-datasource
pip install -e ./xml-datasource
pip install -e ./simple-visualizer
pip install -e ./block-visualizer
pip install -e ./graph-explorer

# Run the application
tangled
```

## Development

### Reinstalling After Changes

When you modify a component, reinstall it:

```bash
pip install -e ./platform  # or whichever component you changed
```

Or use the reinstall script:

```bash
./reinstall.sh
```

### Adding a New Plugin

1. Create a new directory (e.g., `csv-datasource/`)
2. Follow the structure of existing plugins
3. Implement the appropriate interface (`DataSourcePlugin` or `VisualizerPlugin`)
4. Register via entry point in `pyproject.toml`
5. Install with `pip install -e ./csv-datasource`

### Running Tests

```bash
# Install dev dependencies
pip install -e "./api[dev]"
pip install -e "./platform[dev]"

# Run tests
pytest
```

## Usage

1. Open http://localhost:5000 in your browser
2. Create a new workspace
3. Select a data source and load data
4. Use search/filter to explore the graph
5. Switch visualizers to see different representations
6. Use the CLI for advanced manipulation

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/workspace/new` | GET | Create workspace |
| `/workspace/<id>` | GET | Workspace view |
| `/api/plugins/datasources` | GET | List data sources |
| `/api/plugins/visualizers` | GET | List visualizers |
| `/api/workspace/<id>/load` | POST | Load data |
| `/api/workspace/<id>/render` | GET | Render graph |
| `/api/workspace/<id>/search` | POST | Search nodes |
| `/api/workspace/<id>/filter` | POST | Filter nodes |
| `/api/workspace/<id>/reset` | POST | Reset filters |
| `/api/workspace/<id>/cli` | POST | Execute CLI command |

## License

MIT
