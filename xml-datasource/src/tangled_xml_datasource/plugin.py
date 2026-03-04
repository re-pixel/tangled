"""
XML Data Source Plugin implementation.

Parses arbitrary XML documents into graphs per specification:
- Elements with child elements become graph nodes
- Leaf elements (text only) become attributes of their parent node
- XML element attributes become node attributes
- Supports cyclic references via XPath-like reference attributes
- Typed values: int, str, float, date (not stored as strings)
"""

import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tangled_api.model import Graph, Node, Edge
from tangled_api.plugins import DataSourcePlugin, PluginParameter

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_KEY_HINTS = ("date", "birth", "time")
_XPATH_STEP_RE = re.compile(r"^([\w][\w.\-]*)(?:\[(\d+)\])?$")


def _try_parse_value(key: str, text: str) -> Optional[Any]:
    """Parse text content to a typed value (int, float, date, or str)."""
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    key_lower = key.lower()
    if any(h in key_lower for h in _DATE_KEY_HINTS) or _ISO_DATE_RE.match(text):
        try:
            return date.fromisoformat(text)
        except ValueError:
            pass
    return text


def _has_child_elements(elem: ET.Element) -> bool:
    """Check if element has any child elements (not just text)."""
    return len(list(elem)) > 0


def _strip_ns(tag: str) -> str:
    """Remove XML namespace prefix ({uri}localname -> localname)."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


class XmlDataSource(DataSourcePlugin):
    """
    Data source plugin that parses XML files into graphs.

    Mapping rules (per specification):
    - Elements with child elements become nodes
    - Leaf elements (text only, no children) become parent's attributes
    - XML element attributes become node attributes
    - Leaf elements with a reference attribute create edges to referenced nodes
      (XPath-like relative paths for cyclic graph support)
    """

    @property
    def name(self) -> str:
        return "XML Data Source"

    @property
    def description(self) -> str:
        return (
            "Parses XML files and constructs graphs. "
            "Supports cyclic references via XPath-like reference attributes."
        )

    @property
    def parameters(self) -> List[PluginParameter]:
        return [
            PluginParameter(
                name="file_path",
                param_type=str,
                description="Path to the XML file",
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
                name="reference_attribute",
                param_type=str,
                description="XML attribute name used for cyclic references (default: reference)",
                required=False,
                default="reference",
            ),
        ]

    def load(self, **params: Any) -> Graph:
        """
        Parse XML file and construct a graph.

        Args:
            file_path: Path to the XML file
            base_path: Base directory for resolving relative paths
            reference_attribute: XML attribute for cyclic refs (default: reference)

        Returns:
            Graph constructed from XML data

        Raises:
            ValueError: If file_path missing, file not found, or invalid XML
        """
        file_path = params.get("file_path")
        base_path = params.get("base_path", ".")
        ref_attr = params.get("reference_attribute", "reference")

        if not file_path:
            raise ValueError("file_path parameter is required")

        resolved = Path(base_path) / file_path
        if not resolved.exists():
            raise ValueError(f"File not found: {resolved}")
        if not resolved.is_file():
            raise ValueError(f"Path is not a file: {resolved}")

        try:
            tree = ET.parse(str(resolved))
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}") from e

        return self._build_graph(tree.getroot(), ref_attr)

    def _build_graph(self, root: ET.Element, ref_attr: str) -> Graph:
        """Build graph from parsed XML element tree."""
        graph = Graph(directed=True)

        parent_map: Dict[ET.Element, ET.Element] = {}
        all_elements: List[ET.Element] = []
        self._walk(root, parent_map, all_elements)

        node_elements = [e for e in all_elements if _has_child_elements(e)]
        if not node_elements:
            node_elements = [root]

        elem_to_id = self._assign_ids(node_elements)

        for elem in node_elements:
            nid = elem_to_id[id(elem)]
            node = Node(id=nid)

            for attr_name, attr_val in elem.attrib.items():
                if attr_name in (ref_attr, "id"):
                    continue
                parsed = _try_parse_value(attr_name, attr_val)
                if parsed is not None:
                    try:
                        node.set_attribute(attr_name, parsed)
                    except (ValueError, TypeError):
                        pass

            for child in elem:
                if _has_child_elements(child) or child.get(ref_attr) is not None:
                    continue
                child_tag = _strip_ns(child.tag)
                text = child.text
                if text and text.strip():
                    parsed = _try_parse_value(child_tag, text.strip())
                    if parsed is not None:
                        try:
                            node.set_attribute(child_tag, parsed)
                        except (ValueError, TypeError):
                            pass

            graph.add_node(node)

        edge_counter = 0
        for elem in node_elements:
            src_id = elem_to_id[id(elem)]
            for child in elem:
                if child.get(ref_attr) is not None and not _has_child_elements(child):
                    target = self._resolve_ref(
                        child, child.get(ref_attr), parent_map  # type: ignore[arg-type]
                    )
                    if target is not None:
                        target_nid = elem_to_id.get(id(target))
                        if target_nid is not None:
                            eid = f"e{edge_counter}"
                            edge_counter += 1
                            graph.add_edge(
                                Edge(id=eid, source_id=src_id, target_id=target_nid)
                            )
                elif id(child) in elem_to_id:
                    eid = f"e{edge_counter}"
                    edge_counter += 1
                    graph.add_edge(
                        Edge(
                            id=eid,
                            source_id=src_id,
                            target_id=elem_to_id[id(child)],
                        )
                    )

        return graph

    def _assign_ids(self, node_elements: List[ET.Element]) -> Dict[int, str]:
        """Assign stable, readable IDs to node elements (tag_N format)."""
        elem_to_id: Dict[int, str] = {}
        used_ids: Set[str] = set()
        tag_counters: Dict[str, int] = {}

        for elem in node_elements:
            tag = _strip_ns(elem.tag)
            explicit = elem.get("id")
            if explicit and explicit not in used_ids:
                nid = explicit
            else:
                count = tag_counters.get(tag, 0) + 1
                tag_counters[tag] = count
                nid = f"{tag}_{count}"
                while nid in used_ids:
                    count += 1
                    tag_counters[tag] = count
                    nid = f"{tag}_{count}"

            used_ids.add(nid)
            elem_to_id[id(elem)] = nid

        return elem_to_id

    def _walk(
        self,
        elem: ET.Element,
        parent_map: Dict[ET.Element, ET.Element],
        all_elements: List[ET.Element],
    ) -> None:
        """Recursively build element-to-parent map and collect all elements."""
        all_elements.append(elem)
        for child in elem:
            parent_map[child] = elem
            self._walk(child, parent_map, all_elements)

    def _resolve_ref(
        self,
        elem: ET.Element,
        path: str,
        parent_map: Dict[ET.Element, ET.Element],
    ) -> Optional[ET.Element]:
        """
        Resolve XPath-like relative reference path.

        Supports .. (parent) navigation and TagName[N] child selection (1-based).
        Example: ../../../../Person[2]
        """
        parts = [p for p in path.split("/") if p]
        current = elem

        i = 0
        while i < len(parts) and parts[i] == "..":
            parent = parent_map.get(current)
            if parent is None:
                return None
            current = parent
            i += 1

        while i < len(parts):
            match = _XPATH_STEP_RE.match(parts[i])
            if not match:
                return None
            tag_name = match.group(1)
            idx_str = match.group(2)
            idx = int(idx_str) if idx_str else 1

            matching = [c for c in current if _strip_ns(c.tag) == tag_name]
            if idx < 1 or idx > len(matching):
                return None
            current = matching[idx - 1]
            i += 1

        return current
