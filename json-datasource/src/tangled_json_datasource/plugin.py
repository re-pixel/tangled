"""
JSON Data Source Plugin implementation.

Parses arbitrary JSON documents into graphs per specification:
- Objects become nodes; attributes and references become edges
- Supports cyclic references via @id and string reference semantics
- Typed values: int, str, float, date (not stored as strings)
"""

import json
import re
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tangled_api.model import Graph, Node, Edge
from tangled_api.plugins import DataSourcePlugin, PluginParameter

# ISO date pattern: YYYY-MM-DD
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_KEY_HINTS = ("date", "birth", "time")


def _try_parse_date(key: str, value: str) -> Optional[date]:
    """Try to parse string as date. Key hints (date, birth, time) or ISO format."""
    if not isinstance(value, str):
        return None
    key_lower = key.lower()
    hint = any(h in key_lower for h in _DATE_KEY_HINTS)
    if hint or _ISO_DATE_RE.match(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return None


def _to_attribute_value(key: str, value: Any) -> Optional[Any]:
    """
    Convert JSON value to API attribute type (int, float, str, date).
    Returns None for null (skip). Arrays of primitives become comma-separated string.
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
        parsed = _try_parse_date(key, value)
        return parsed if parsed is not None else value
    if isinstance(value, list):
        if not value:
            return None
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


def _collect_objects(
    data: Any,
    path: str,
    objects: List[Dict[str, Any]],
    obj_to_path: Dict[int, str],
) -> None:
    """Recursively collect all JSON objects. Uses id(obj) to deduplicate."""
    if isinstance(data, dict):
        obj_id = id(data)
        if obj_id not in obj_to_path:
            obj_to_path[obj_id] = path
            objects.append(data)
        for key, val in data.items():
            if isinstance(val, dict):
                _collect_objects(val, f"{path}.{key}", objects, obj_to_path)
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    if isinstance(item, dict):
                        _collect_objects(
                            item, f"{path}.{key}.{i}", objects, obj_to_path
                        )
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                _collect_objects(item, f"{path}.{i}", objects, obj_to_path)


def _collect_from_root(data: Any) -> List[Dict[str, Any]]:
    """Collect all objects from root (object or array of objects)."""
    objects: List[Dict[str, Any]] = []
    obj_to_path: Dict[int, str] = {}

    if isinstance(data, dict):
        _collect_objects(data, "root", objects, obj_to_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                _collect_objects(item, f"root.{i}", objects, obj_to_path)

    return objects


class JsonDataSource(DataSourcePlugin):
    """
    Data source plugin that parses JSON files into graphs.

    Mapping rules (per specification):
    - JSON objects become nodes
    - Nested objects/arrays create edges to child nodes
    - Primitive values become node attributes (typed: int, str, float, date)
    - id_attribute (e.g. @id) marks node identifier for cyclic references
    - String values matching existing node ID create reference edges
    """

    @property
    def name(self) -> str:
        return "JSON Data Source"

    @property
    def description(self) -> str:
        return "Parses JSON files and constructs graphs. Supports cyclic references via @id attributes."

    @property
    def parameters(self) -> List[PluginParameter]:
        return [
            PluginParameter(
                name="file_path",
                param_type=str,
                description="Path to the JSON file",
                required=True,
            ),
            PluginParameter(
                name="base_path",
                param_type=str,
                description="Base path for resolving relative file_path (default: current directory)",
                required=False,
                default=".",
            ),
            PluginParameter(
                name="id_attribute",
                param_type=str,
                description="Attribute name used for node IDs (default: @id)",
                required=False,
                default="@id",
            ),
        ]

    def load(self, **params: Any) -> Graph:
        """
        Parse JSON file and construct a graph.

        Args:
            file_path: Path to the JSON file
            base_path: Base directory for resolving relative paths
            id_attribute: Attribute name for node IDs (default: @id)

        Returns:
            Graph constructed from JSON data

        Raises:
            ValueError: If file_path missing, file not found, or invalid JSON
        """
        file_path = params.get("file_path")
        base_path = params.get("base_path", ".")
        id_attribute = params.get("id_attribute", "@id")

        if not file_path:
            raise ValueError("file_path parameter is required")

        resolved = Path(base_path) / file_path
        if not resolved.exists():
            raise ValueError(f"File not found: {resolved}")
        if not resolved.is_file():
            raise ValueError(f"Path is not a file: {resolved}")

        try:
            with open(resolved, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(data, (dict, list)):
            raise ValueError("JSON root must be an object or array")

        return self._build_graph(data, id_attribute)

    def _build_graph(self, data: Any, id_attribute: str) -> Graph:
        """Build graph from parsed JSON using three-pass approach."""
        directed = True
        if isinstance(data, dict):
            val = data.get("directed", True)
            directed = val if isinstance(val, bool) else val.lower() not in ("false", "0", "no")
            data = data.get("nodes", [])
        graph = Graph(directed=directed)

        # Pass 1: Collect objects and assign node IDs
        objects = _collect_from_root(data)
        obj_to_node_id: Dict[int, str] = {}
        used_ids: Set[str] = set()

        for obj in objects:
            obj_id = id(obj)
            if id_attribute in obj and isinstance(obj[id_attribute], str):
                nid = obj[id_attribute]
                if nid in used_ids:
                    nid = f"{nid}_{uuid.uuid4().hex[:8]}"
                used_ids.add(nid)
            else:
                nid = str(uuid.uuid4())
            obj_to_node_id[obj_id] = nid

        known_ids = set(obj_to_node_id.values())

        # Pass 2: Create nodes with attributes (skip string references)
        for obj in objects:
            node_id = obj_to_node_id[id(obj)]
            node = Node(id=node_id)

            for key, value in obj.items():
                if key == id_attribute:
                    continue
                if value is None:
                    continue
                if isinstance(value, dict):
                    continue
                if isinstance(value, list) and any(
                    isinstance(v, dict) for v in value
                ):
                    continue

                attr_val = _to_attribute_value(key, value)
                if attr_val is not None:
                    if (
                        isinstance(attr_val, str)
                        and attr_val in known_ids
                        and attr_val != node_id
                    ):
                        continue
                    try:
                        node.set_attribute(key, attr_val)
                    except (ValueError, TypeError):
                        pass

            graph.add_node(node)

        # Pass 3: Create edges (structural and reference)
        edge_counter = 0
        for obj in objects:
            node_id = obj_to_node_id[id(obj)]

            for key, value in obj.items():
                if value is None:
                    continue

                if isinstance(value, dict):
                    child_id = obj_to_node_id.get(id(value))
                    if child_id is not None:
                        edge_id = f"e{edge_counter}"
                        edge_counter += 1
                        graph.add_edge(
                            Edge(
                                id=edge_id,
                                source_id=node_id,
                                target_id=child_id,
                            )
                        )
                    continue

                if isinstance(value, list):
                    if any(isinstance(v, dict) for v in value):
                        for item in value:
                            if isinstance(item, dict):
                                child_id = obj_to_node_id.get(id(item))
                                if child_id is not None:
                                    edge_id = f"e{edge_counter}"
                                    edge_counter += 1
                                    graph.add_edge(
                                        Edge(
                                            id=edge_id,
                                            source_id=node_id,
                                            target_id=child_id,
                                        )
                                    )
                    continue

                attr_val = _to_attribute_value(key, value)
                if (
                    attr_val is not None
                    and isinstance(attr_val, str)
                    and attr_val in known_ids
                    and attr_val != node_id
                ):
                    edge_id = f"e{edge_counter}"
                    edge_counter += 1
                    graph.add_edge(
                        Edge(
                            id=edge_id,
                            source_id=node_id,
                            target_id=attr_val,
                        )
                    )

        return graph
