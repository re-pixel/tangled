# Tangled JSON Data Source Plugin

Data source plugin that parses JSON files and constructs graphs.

## Features

- Parses arbitrary JSON documents
- Objects become nodes, nested objects/arrays create edges
- Supports cyclic references via `@id` / reference attributes
- Preserves value types (int, float, str, date)

## Installation

```bash
pip install -e /path/to/json-datasource
```

## Usage

The plugin is automatically discovered by the platform.

```python
from tangled_platform import Platform

platform = Platform()
workspace = platform.create_workspace()

# Load JSON data
workspace.load_data(
    platform.get_data_source("json"),
    file_path="path/to/data.json"
)
```

## Cyclic Graph Support

Use `@id` attributes to create references:

```json
{
  "@id": "node1",
  "name": "Parent",
  "child": {
    "@id": "node2", 
    "name": "Child",
    "parent": "node1"
  }
}
```
