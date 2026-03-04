"""
Kuzu Data Source Plugin for Tangled.

Reads graph data from Kuzu embedded graph databases using Cypher queries.
"""

__version__ = "0.1.0"

from tangled_kuzu_datasource.plugin import KuzuDataSource

__all__ = ["KuzuDataSource"]
