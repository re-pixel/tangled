"""
Command Line Interface for graph manipulation

Provides commands for:
- Node CRUD operations
- Edge CRUD operations
- Filter and search
- Graph clearing
"""

from typing import Any, Dict, List, Optional
import re
import shlex

from tangled_api.model import Graph, Node, Edge
from tangled_api.model.attribute import Attribute, AttributeValue


_PROP_RE = re.compile(r"^([\w\-]+)=(.*)$")


def _guess_attr_type(value: str) -> AttributeValue:
    """Infer AttributeValue type from a raw string. Priority: int → float → date → str"""
    from datetime import date

    try:
        int(value)
        return AttributeValue.INTEGER
    except ValueError:
        pass
    try:
        float(value)
        return AttributeValue.FLOAT
    except ValueError:
        pass
    try:
        date.fromisoformat(value)
        return AttributeValue.DATE
    except ValueError:
        pass
    return AttributeValue.STRING


def _coerce(value: str, attr_type: AttributeValue) -> Any:
    """Cast a raw string to the Python type expected by attr_type"""
    from datetime import date

    if attr_type == AttributeValue.INTEGER:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to integer")
    if attr_type == AttributeValue.FLOAT:
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to float")
    if attr_type == AttributeValue.DATE:
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to date (expected YYYY-MM-DD)")
    return value


def _parse_props(prop_tokens: List[str]) -> Dict[str, str]:
    """Parse ['Key=Value', ...] into {'Key': 'Value', ...}"""
    props = {}
    for tok in prop_tokens:
        m = _PROP_RE.match(tok)
        if not m:
            raise ValueError(f"Invalid property format '{tok}' — expected key=value")
        props[m.group(1)] = m.group(2)
    return props


def _consume_flag(tokens: List[str], flag: str):
    """Extract a single --flag=value (or --flag value) from tokens list"""
    remaining = []
    value = None
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        prefix = f"{flag}="
        if tok.startswith(prefix):
            value = tok[len(prefix):]
        elif tok == flag and i + 1 < len(tokens):
            value = tokens[i + 1]
            i += 1
        else:
            remaining.append(tok)
        i += 1
    return value, remaining


def _consume_all_flag(tokens: List[str], flag: str):
    """Extract all occurrences of --flag=value from tokens list"""
    values = []
    remaining = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        prefix = f"{flag}="
        if tok.startswith(prefix):
            values.append(tok[len(prefix):])
        elif tok == flag and i + 1 < len(tokens):
            values.append(tokens[i + 1])
            i += 1
        else:
            remaining.append(tok)
        i += 1
    return values, remaining


def _set_attributes(entity, props: Dict[str, str]) -> None:
    """Write props onto a node or edge, preserving existing attribute types"""
    for key, raw_value in props.items():
        if key in entity.attributes:
            existing_type = entity.attributes[key].type
            coerced = _coerce(raw_value, existing_type)
            entity.attributes[key] = Attribute(key=key, value=coerced, type=existing_type)
        else:
            attr_type = _guess_attr_type(raw_value)
            coerced = _coerce(raw_value, attr_type)
            entity.attributes[key] = Attribute(key=key, value=coerced, type=attr_type)


class CLI:
    """
    Command-line interface for direct graph manipulation

    Works directly with a Graph object (no workspace/filter chain)
    For workspace-aware CLI (filter, search history), use tangled_web.cli.CLI

    Commands:
        create node --id=<id> [--property <key>=<value> ...]
        create edge --id=<id> <source_id> <target_id> [--property <key>=<value> ...]
        edit   node --id=<id> --property <key>=<value> [...]
        edit   edge --id=<id> --property <key>=<value> [...]
        delete node --id=<id>
        delete edge --id=<id>
        filter '<attribute> <op> <value>'
        search '<query>'
        clear
        show nodes|edges
        help
    """

    def __init__(self, graph: Graph):
        self._graph = graph

    def execute(self, command: str) -> str:
        """
        Execute a CLI command and return a result message

        Args:
            command: The command string to execute

        Returns:
            Result message string (error messages are prefixed with 'Error: ')
        """
        command = command.strip()
        if not command:
            return ""

        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            return f"Error: Parse error — {exc}"

        if not tokens:
            return ""

        verb = tokens[0].lower()
        rest = tokens[1:]

        try:
            if verb == "help":
                return self.__doc__
            elif verb == "create":
                return self._create(rest)
            elif verb == "edit":
                return self._edit(rest)
            elif verb == "delete":
                return self._delete(rest)
            elif verb == "filter":
                return self._filter(" ".join(rest))
            elif verb == "search":
                return self._search(" ".join(rest))
            elif verb == "clear":
                return self._clear()
            elif verb == "show":
                return self._show(rest)
            else:
                return f"Error: Unknown command '{verb}'. Type 'help' for usage."
        except ValueError as exc:
            return f"Error: {exc}"
        except Exception as exc:
            return f"Error: Internal error — {exc}"

    def _create(self, tokens: List[str]) -> str:
        if not tokens:
            raise ValueError("Usage: create node|edge ...")
        kind = tokens[0].lower()
        if kind == "node":
            return self._create_node(tokens[1:])
        elif kind == "edge":
            return self._create_edge(tokens[1:])
        else:
            raise ValueError(f"Unknown entity '{kind}'. Use 'node' or 'edge'.")

    def _edit(self, tokens: List[str]) -> str:
        if not tokens:
            raise ValueError("Usage: edit node|edge --id=<id> --property key=value ...")
        kind = tokens[0].lower()
        if kind == "node":
            return self._edit_node(tokens[1:])
        elif kind == "edge":
            return self._edit_edge(tokens[1:])
        else:
            raise ValueError(f"Unknown entity '{kind}'. Use 'node' or 'edge'.")

    def _delete(self, tokens: List[str]) -> str:
        if not tokens:
            raise ValueError("Usage: delete node|edge --id=<id>")
        kind = tokens[0].lower()
        if kind == "node":
            return self._delete_node(tokens[1:])
        elif kind == "edge":
            return self._delete_edge(tokens[1:])
        else:
            raise ValueError(f"Unknown entity '{kind}'. Use 'node' or 'edge'.")

    def _create_node(self, tokens: List[str]) -> str:
        """Handle 'create node' command"""
        node_id, tokens = _consume_flag(tokens, "--id")
        if node_id is None:
            raise ValueError("create node requires --id=<id>")

        prop_tokens, remaining = _consume_all_flag(tokens, "--property")
        for tok in remaining:
            if tok.startswith("--") and "=" in tok:
                prop_tokens.append(tok[2:])

        props = _parse_props(prop_tokens)

        if node_id in self._graph.nodes:
            raise ValueError(f"Node '{node_id}' already exists")

        node = Node(id=node_id)
        _set_attributes(node, props)
        self._graph.add_node(node)
        return f"Created node '{node_id}'"

    def _edit_node(self, tokens: List[str]) -> str:
        """Handle 'edit node' command"""
        node_id, tokens = _consume_flag(tokens, "--id")
        if node_id is None:
            raise ValueError("edit node requires --id=<id>")

        prop_tokens, _ = _consume_all_flag(tokens, "--property")
        if not prop_tokens:
            raise ValueError("edit node requires at least one --property key=value")

        if node_id not in self._graph.nodes:
            raise ValueError(f"Node '{node_id}' does not exist")

        props = _parse_props(prop_tokens)
        _set_attributes(self._graph.nodes[node_id], props)
        return f"Updated node '{node_id}': {', '.join(props.keys())}"

    def _delete_node(self, tokens: List[str]) -> str:
        """Handle 'delete node' command. Node must have no connected edges"""
        node_id, _ = _consume_flag(tokens, "--id")
        if node_id is None:
            raise ValueError("delete node requires --id=<id>")

        if node_id not in self._graph.nodes:
            raise ValueError(f"Node '{node_id}' does not exist")

        connected = [
            eid for eid, e in self._graph.edges.items()
            if e.source_id == node_id or e.target_id == node_id
        ]
        if connected:
            raise ValueError(
                f"Cannot delete node '{node_id}' — connected by edge(s): "
                f"{', '.join(connected)}. Delete those edges first."
            )

        self._graph.remove_node(node_id)
        return f"Deleted node '{node_id}'"

    def _create_edge(self, tokens: List[str]) -> str:
        """Handle 'create edge' command"""
        edge_id, tokens = _consume_flag(tokens, "--id")
        if edge_id is None:
            raise ValueError("create edge requires --id=<id>")

        prop_tokens, positional = _consume_all_flag(tokens, "--property")
        clean_positional = []
        for tok in positional:
            if tok.startswith("--") and "=" in tok:
                prop_tokens.append(tok[2:])
            else:
                clean_positional.append(tok)

        if len(clean_positional) < 2:
            raise ValueError(
                "create edge requires source and target node ids, "
                "e.g.  create edge --id=e1 node1 node2"
            )

        source_id, target_id = clean_positional[0], clean_positional[1]

        if source_id not in self._graph.nodes:
            raise ValueError(f"Source node '{source_id}' does not exist")
        if target_id not in self._graph.nodes:
            raise ValueError(f"Target node '{target_id}' does not exist")
        if edge_id in self._graph.edges:
            raise ValueError(f"Edge '{edge_id}' already exists")

        props = _parse_props(prop_tokens)
        edge = Edge(id=edge_id, source_id=source_id, target_id=target_id)
        _set_attributes(edge, props)
        self._graph.add_edge(edge)
        return f"Created edge '{edge_id}' ({source_id} → {target_id})"

    def _edit_edge(self, tokens: List[str]) -> str:
        """Handle 'edit edge' command"""
        edge_id, tokens = _consume_flag(tokens, "--id")
        if edge_id is None:
            raise ValueError("edit edge requires --id=<id>")

        prop_tokens, _ = _consume_all_flag(tokens, "--property")
        if not prop_tokens:
            raise ValueError("edit edge requires at least one --property key=value")

        if edge_id not in self._graph.edges:
            raise ValueError(f"Edge '{edge_id}' does not exist")

        props = _parse_props(prop_tokens)
        _set_attributes(self._graph.edges[edge_id], props)
        return f"Updated edge '{edge_id}': {', '.join(props.keys())}"

    def _delete_edge(self, tokens: List[str]) -> str:
        """Handle 'delete edge' command"""
        edge_id, _ = _consume_flag(tokens, "--id")
        if edge_id is None:
            raise ValueError("delete edge requires --id=<id>")

        if edge_id not in self._graph.edges:
            raise ValueError(f"Edge '{edge_id}' does not exist")

        self._graph.remove_edge(edge_id)
        return f"Deleted edge '{edge_id}'"

    def _filter(self, query: str) -> str:
        """Handle 'filter' command. Delegates to Graph.filter_by_query"""
        if not query:
            raise ValueError("Usage: filter '<attribute> <op> <value>'  e.g.  filter 'Age > 30'")
        result = self._graph.filter_by_query(query)
        self._graph._nodes = result._nodes
        self._graph._edges = result._edges
        self._graph._adj_out = result._adj_out
        self._graph._adj_in = result._adj_in
        return f"Filter applied — {len(self._graph.nodes)} node(s) remaining"

    def _search(self, query: str) -> str:
        """Handle 'search' command. Finds nodes whose attribute names or values contain query"""
        if not query:
            raise ValueError("Usage: search '<term>'")
        query_lower = query.lower()
        matching_ids = []
        for node_id, node in self._graph.nodes.items():
            for attr_name, attr in node.attributes.items():
                if query_lower in attr_name.lower() or query_lower in str(attr.value).lower():
                    matching_ids.append(node_id)
                    break
        result = self._graph.create_subgraph(matching_ids)
        self._graph._nodes = result._nodes
        self._graph._edges = result._edges
        self._graph._adj_out = result._adj_out
        self._graph._adj_in = result._adj_in
        return f"Search done — {len(self._graph.nodes)} node(s) matched"

    def _clear(self) -> str:
        """Handle 'clear' command. Removes all nodes and edges from the graph"""
        self._graph._nodes.clear()
        self._graph._edges.clear()
        self._graph._adj_out.clear()
        self._graph._adj_in.clear()
        return "Graph cleared"

    def _show(self, tokens: List[str]) -> str:
        """Handle 'show nodes|edges' command"""
        if not tokens:
            raise ValueError("Usage: show nodes|edges")
        kind = tokens[0].lower()
        if kind == "nodes":
            if not self._graph.nodes:
                return "(no nodes)"
            lines = []
            for nid, node in self._graph.nodes.items():
                attrs = node.attributes
                attr_str = "  ".join(
                    f"{k}={v.value}" for k, v in attrs.items()
                    if v.value is not None and str(v.value).strip() != ""
                ) if attrs else "(no attributes)"
                lines.append(f"{nid}  {attr_str}")
            return "\n".join(lines)
        elif kind == "edges":
            if not self._graph.edges:
                return "(no edges)"
            lines = []
            for eid, edge in self._graph.edges.items():
                attrs = edge.attributes
                attr_str = "  ".join(
                    f"{k}={v.value}" for k, v in attrs.items()
                    if v.value is not None and str(v.value).strip() != ""
                ) if attrs else "(no attributes)"
                lines.append(f"{eid}  {edge.source_id} → {edge.target_id}  {attr_str}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unknown entity '{kind}'. Use 'nodes' or 'edges'.")