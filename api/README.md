# Tangled API

Core abstractions and data model for the Tangled graph visualization platform.

## Overview

This library provides:
- **Graph data model**: `Node`, `Edge`, `Graph` classes supporting directed/undirected, cyclic/acyclic graphs
- **Plugin interfaces**: Abstract base classes for `DataSourcePlugin` and `VisualizerPlugin`
- **Type definitions**: Strong typing for attribute values (`int`, `str`, `float`, `date`)

## Installation

```bash
pip install -e /path/to/api
```

## Usage

```python
from tangled_api.model import Graph, Node, Edge
from tangled_api.plugins import DataSourcePlugin, VisualizerPlugin
```

## For Plugin Developers

Implement `DataSourcePlugin` to create a new data source:

```python
from tangled_api.plugins import DataSourcePlugin

class MyDataSource(DataSourcePlugin):
    ...
```

Implement `VisualizerPlugin` to create a new visualizer:

```python
from tangled_api.plugins import VisualizerPlugin

class MyVisualizer(VisualizerPlugin):
    ...
```
