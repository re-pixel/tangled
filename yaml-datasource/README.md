# Tangled YAML Data Source Plugin

Data source plugin that parses YAML files and constructs graphs.

## Features

- Parses arbitrary YAML documents
- Mappings become nodes, nested mappings/sequences create edges
- Supports cyclic references via id / reference attributes
- Preserves value types (int, float, str, date)

## Installation

```bash
pip install -e /path/to/yaml-datasource
```

## Usage

The plugin is automatically discovered by the platform.

```python
from tangled_platform import Platform

platform = Platform()
workspace = platform.create_workspace()

# Load YAML data
workspace.load_data(
    platform.get_data_source("yaml"),
    file_path="path/to/data.yaml"
)
```

## Cyclic Graph Support

Use id attributes to create references:

```yaml
id: node1
name: Parent
child:
  id: node2
  name: Child
  parent: node1
```

## Example Data

Fixture files for testing and demo:

| File | Description |
|------|-------------|
| `tests/examples/acyclic_tree.yaml` | Acyclic tree (Doe family from spec) |
| `tests/examples/cyclic.yaml` | Cyclic graph with id and parent references |

## Testing

```bash
pytest yaml-datasource/tests/ -v
```

Or from project root: `make test` (runs all plugin tests).
