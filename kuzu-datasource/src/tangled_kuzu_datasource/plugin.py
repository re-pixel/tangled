"""
Kuzu Data Source Plugin implementation.

Reads graph data from Kuzu embedded graph databases using Cypher queries.
Nodes and relationships returned by the query are mapped to Tangled's
Graph model with typed attributes (int, float, str, date).
"""

from datetime import date, datetime
from typing import Any, List, Optional, Tuple, Union

import kuzu

from tangled_api.model import Graph, Node, Edge
from tangled_api.plugins import DataSourcePlugin, PluginParameter

_DEFAULT_QUERY = "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m"
_DEFAULT_NODE_ID_PROPERTY = "id"


def _to_attribute_value(key: str, value: Any) -> Optional[Any]:
    """
    Convert a Kuzu property value to a Tangled attribute type (int, float, str, date).

    Returns None for null/unsupported types (skip).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, list):
        if not value:
            return ""
        if all(isinstance(v, (int, float, str, bool)) or v is None for v in value):
            parts = []
            for v in value:
                if v is None:
                    parts.append("")
                elif isinstance(v, bool):
                    parts.append(str(v).lower())
                else:
                    parts.append(str(v))
            return ",".join(parts)
        return None
    return None


def _apply_attributes(entity: Union[Node, Edge], props: dict) -> None:
    """Copy non-internal properties from a Kuzu dict onto a Node or Edge."""
    for key, value in props.items():
        if key.startswith("_"):
            continue
        attr_val = _to_attribute_value(key, value)
        if attr_val is not None:
            try:
                entity.set_attribute(key, attr_val)
            except (ValueError, TypeError):
                pass


def _is_node(value: Any) -> bool:
    """Detect whether a query result value is a Kuzu node."""
    return (
        isinstance(value, dict)
        and "_label" in value
        and "_id" in value
        and "_src" not in value
    )


def _is_relationship(value: Any) -> bool:
    """Detect whether a query result value is a Kuzu relationship."""
    return isinstance(value, dict) and "_src" in value and "_dst" in value


def _to_hashable_id(internal_id: Any) -> Tuple:
    """Convert Kuzu internal IDs (dicts/tuples) to hashable keys for deduplication."""
    if isinstance(internal_id, dict):
        return (internal_id.get("offset"), internal_id.get("table"))
    if isinstance(internal_id, (list, tuple)):
        return tuple(internal_id)
    return (internal_id,)


class KuzuDataSource(DataSourcePlugin):
    """
    Data source plugin that reads graph data from Kuzu embedded graph databases.

    Opens the database in read-only mode and executes a Cypher query to extract
    nodes and relationships, mapping them to Tangled's Graph model.
    """

    @property
    def name(self) -> str:
        return "Kuzu Data Source"

    @property
    def description(self) -> str:
        return "Reads graph data from Kuzu embedded graph databases using Cypher queries."

    @property
    def parameters(self) -> List[PluginParameter]:
        return [
            PluginParameter(
                name="database_path",
                param_type=str,
                description="Path to the Kuzu database directory",
                required=True,
            ),
            PluginParameter(
                name="query",
                param_type=str,
                description="Cypher query to execute (default: match all nodes and relationships)",
                required=False,
                default=_DEFAULT_QUERY,
            ),
            PluginParameter(
                name="node_id_property",
                param_type=str,
                description="Node property to use as Tangled node ID (default: id)",
                required=False,
                default=_DEFAULT_NODE_ID_PROPERTY,
            ),
        ]

    def load(self, **params: Any) -> Graph:
        """
        Read a Kuzu database and construct a graph.

        Args:
            database_path: Path to the Kuzu database directory
            query: Cypher query to execute
            node_id_property: Node property to use as Tangled node ID

        Returns:
            Graph constructed from query results

        Raises:
            ValueError: If parameters are invalid or query fails
        """
        database_path = params.get("database_path")
        query = params.get("query", _DEFAULT_QUERY)
        node_id_property = params.get("node_id_property", _DEFAULT_NODE_ID_PROPERTY)

        if not database_path:
            raise ValueError("database_path parameter is required")

        try:
            db = kuzu.Database(database_path, read_only=True)
        except Exception as e:
            raise ValueError(f"Database not found: {database_path}") from e

        conn = kuzu.Connection(db)

        try:
            result = conn.execute(query)
        except Exception as e:
            raise ValueError(f"Invalid Cypher query: {e}") from e

        graph = Graph(directed=True)
        seen_nodes = set()
        node_id_map = {}
        rels_to_add = []

        # Single pass: process nodes inline, buffer relationships
        while result.has_next():
            row = result.get_next()
            for value in row:
                if value is None:
                    continue
                if _is_node(value):
                    h_id = _to_hashable_id(value.get("_id"))
                    if h_id in seen_nodes:
                        continue
                    seen_nodes.add(h_id)

                    label = value.get("_label", "Unknown")

                    if node_id_property in value:
                        tangled_id = str(value[node_id_property])
                    else:
                        internal_id = value.get("_id")
                        offset = (
                            internal_id.get("offset", 0)
                            if isinstance(internal_id, dict)
                            else 0
                        )
                        tangled_id = f"{label}_{offset}"

                    node_id_map[h_id] = tangled_id
                    node = Node(id=tangled_id)
                    node.set_attribute("_label", label)
                    _apply_attributes(node, value)
                    graph.add_node(node)

                elif _is_relationship(value):
                    rels_to_add.append(value)

        # Second pass: add edges (must happen after all nodes exist)
        seen_edges = set()
        edge_counter = 0

        for rel_dict in rels_to_add:
            src_id = _to_hashable_id(rel_dict.get("_src"))
            dst_id = _to_hashable_id(rel_dict.get("_dst"))
            rel_internal_id = _to_hashable_id(rel_dict.get("_id"))

            edge_key = (src_id, rel_internal_id, dst_id)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            source_tangled_id = node_id_map.get(src_id)
            target_tangled_id = node_id_map.get(dst_id)

            if source_tangled_id is None or target_tangled_id is None:
                continue

            edge = Edge(
                id=f"e{edge_counter}",
                source_id=source_tangled_id,
                target_id=target_tangled_id,
            )
            edge_counter += 1

            edge.set_attribute("_type", rel_dict.get("_label", "Unknown"))
            _apply_attributes(edge, rel_dict)
            graph.add_edge(edge)

        return graph
