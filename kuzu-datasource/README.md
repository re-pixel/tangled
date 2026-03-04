# Tangled Kuzu Data Source

A data source plugin for the [Tangled](https://github.com/re-pixel/tangled) graph visualization platform that reads graph data from [Kuzu](https://kuzudb.com/) embedded graph databases.

## Features

- Reads Kuzu databases in read-only mode (no server required)
- Executes Cypher queries to extract nodes and relationships
- Maps Kuzu types (INT64, DOUBLE, STRING, DATE, BOOLEAN) to Tangled attribute types
- Configurable node ID property and custom queries
- Supports cyclic and acyclic graph structures

## Installation

```bash
pip install tangled-kuzu-datasource
```

Or for development:

```bash
pip install -e "./kuzu-datasource[dev]"
```

## Usage

```python
from tangled_kuzu_datasource import KuzuDataSource

plugin = KuzuDataSource()

# Load with defaults (matches all nodes and relationships)
graph = plugin.load(database_path="/path/to/kuzu/db")

# Load with a custom Cypher query
graph = plugin.load(
    database_path="/path/to/kuzu/db",
    query="MATCH (p:Person)-[r:KNOWS]->(q:Person) RETURN p, r, q",
    node_id_property="name",
)
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `database_path` | str | Yes | — | Path to the Kuzu database directory |
| `query` | str | No | `MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m` | Cypher query to execute |
| `node_id_property` | str | No | `id` | Node property to use as Tangled node ID |

## Running Tests

```bash
pytest kuzu-datasource/tests/ -v
```
