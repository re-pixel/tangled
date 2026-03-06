"""
CLI for graph manipulation.

Supported commands:

  Node operations:
    create node --id=<id> [--property <key>=<value> ...]
    edit   node --id=<id>  --property <key>=<value> [...]
    delete node --id=<id>

  Edge operations:
    create edge --id=<id> <source_id> <target_id> [--property <key>=<value> ...]
    edit   edge --id=<id>  --property <key>=<value> [...]
    delete edge --id=<id>

  Graph-level:
    filter '<expression>'      e.g.  filter 'Age>30 && Height>=150'
    search '<term>'            e.g.  search 'Name=Tom'
    reset                      remove all filters and searches
    clear                      clear all views
    show nodes                 list all nodes
    show edges                 list all edges
    help                       print help text
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import Any


class CLIError(Exception):
    """Raised for user-facing errors (bad syntax, missing node, etc.)"""


@dataclass
class CLIResult:
    output: str = ""
    error: str = ""
    changed: bool = False 

    @classmethod
    def ok(cls, msg: str = "OK", changed: bool = False) -> "CLIResult":
        return cls(output=msg, changed=changed)

    @classmethod
    def err(cls, msg: str) -> "CLIResult":
        return cls(error=msg)

_PROP_RE = re.compile(r"^([\w\-]+)=(.*)$")


def _parse_properties(tokens: list[str]) -> dict[str, str]:
    """Parse a list of ``key=value`` strings into a dict"""
    props: dict[str, str] = {}
    for tok in tokens:
        m = _PROP_RE.match(tok)
        if not m:
            raise CLIError(f"Invalid property format '{tok}' - expected key=value")
        props[m.group(1)] = m.group(2)
    return props


def _consume_flag(tokens: list[str], flag: str) -> tuple[str | None, list[str]]:
    """
    Pull the value of *flag* out of *tokens*

    Supports both ``--flag=value`` and ``--flag value`` forms
    Returns (value_or_None, remaining_tokens)
    """
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
            i += 1          # skip the next token - it is the value
        else:
            remaining.append(tok)
        i += 1
    return value, remaining


def _consume_all_flag(tokens: list[str], flag: str) -> tuple[list[str], list[str]]:
    """
    Like _consume_flag but collects *all* occurrences of *flag*

    Returns (list_of_values, remaining_tokens)
    """
    values: list[str] = []
    remaining: list[str] = []
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

def _coerce_value(value: str, attr_type):
    """Cast a raw string to the Python type expected by *attr_type*"""
    from tangled_api.model.attribute import AttributeValue
    from datetime import date

    if attr_type == AttributeValue.INTEGER:
        try:
            return int(value)
        except ValueError:
            raise CLIError(f"Cannot convert '{value}' to integer")
    if attr_type == AttributeValue.FLOAT:
        try:
            return float(value)
        except ValueError:
            raise CLIError(f"Cannot convert '{value}' to float")
    if attr_type == AttributeValue.DATE:
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise CLIError(f"Cannot convert '{value}' to date (expected YYYY-MM-DD)")
    return value


def _guess_attr_type(value: str):
    """
    Infer the AttributeValue type from a raw string

    Priority: integer → float → date → string
    """
    from tangled_api.model.attribute import AttributeValue
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


def _set_attributes(entity, props: dict[str, str], graph) -> None:
    """
    Write *props* onto a node or edge

    If the attribute already exists, its declared type is preserved and the
    new string value is coerced accordingly.  For new attributes the type is
    inferred via _guess_attr_type
    """
    from tangled_api.model.attribute import Attribute

    for key, raw_value in props.items():
        if key in entity.attributes:
            existing_type = entity.attributes[key].type
            coerced = _coerce_value(raw_value, existing_type)
            entity.attributes[key] = Attribute(key=key, value=coerced, type=existing_type)
        else:
            attr_type = _guess_attr_type(raw_value)
            coerced = _coerce_value(raw_value, attr_type)
            entity.attributes[key] = Attribute(key=key, value=coerced, type=attr_type)

class CLI:
    """
    Stateless command executor.  Instantiate once per workspace and call
    ``execute(command_string)`` for each user input
    """

    def __init__(self, workspace):
        """
        Parameters
        ----------
        workspace:
            The Workspace object whose ``.graph`` will be mutated
            The workspace must also expose ``.filter(query)`` and
            ``.search(query)`` methods (already present in the backend)
        """
        self.workspace = workspace
        if not hasattr(self.workspace, '_cli_cleared'):
            self.workspace._cli_cleared = False

    @property
    def _cleared(self) -> bool:
        return getattr(self.workspace, '_cli_cleared', False)

    @_cleared.setter
    def _cleared(self, value: bool):
        self.workspace._cli_cleared = value

    def execute(self, command: str) -> CLIResult:
        """Parse *command* and dispatch to the correct handler"""
        command = command.strip()
        if not command:
            return CLIResult.ok("")

        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            return CLIResult.err(f"Parse error: {exc}")

        if not tokens:
            return CLIResult.ok("")

        verb = tokens[0].lower()
        rest = tokens[1:]

        if self._cleared and verb not in ("help", "show", "clear", "reset"):
            return CLIResult.err(
                f"Graph is cleared. Only 'help', 'show', 'clear' and 'reset' are available. "
                f"Load data to perform graph operations."
            )

        try:
            if verb == "help":
                return CLIResult.ok(__doc__)
            elif verb == "create":
                return self._create(rest)
            elif verb == "edit":
                return self._edit(rest)
            elif verb == "delete":
                return self._delete(rest)
            elif verb == "filter":
                return self._filter(rest)
            elif verb == "search":
                return self._search(rest)
            elif verb == "reset":
                return self._reset();
            elif verb == "clear":
                return self._clear()
            elif verb == "show":
                return self._show(rest)
            else:
                return CLIResult.err(
                    f"Unknown command '{verb}'. Type 'help' for usage."
                )
        except CLIError as exc:
            return CLIResult.err(str(exc))
        except Exception as exc:
            return CLIResult.err(f"Internal error: {exc}")
        
    def _reset(self) -> CLIResult:
        self.workspace.reset()
        self._cleared = False
        node_count = len(self.workspace.graph.nodes)
        return CLIResult.ok(f"Reset to original graph - {node_count} node(s)", changed=True)

    def _clear(self) -> CLIResult:
        self._cleared = True
        return CLIResult.ok("Views cleared", changed=True)

    def _create(self, tokens: list[str]) -> CLIResult:
        if not tokens:
            raise CLIError("Usage: create node|edge ...")
        kind = tokens[0].lower()
        rest = tokens[1:]
        if kind == "node":
            return self._create_node(rest)
        elif kind == "edge":
            return self._create_edge(rest)
        else:
            raise CLIError(f"Unknown entity '{kind}'. Use 'node' or 'edge'.")

    def _create_node(self, tokens: list[str]) -> CLIResult:
        from tangled_api.model import Node

        self._cleared = False
        node_id, tokens = _consume_flag(tokens, "--id")
        if node_id is None:
            raise CLIError("create node requires --id=<id>")

        prop_tokens, remaining = _consume_all_flag(tokens, "--property")
        for tok in remaining:
            if tok.startswith("--") and "=" in tok:
                prop_tokens.append(tok[2:])

        props = _parse_properties(prop_tokens)
        graph = self.workspace.graph
        if node_id in graph.nodes:
            raise CLIError(f"Node '{node_id}' already exists")

        node = Node(id=node_id)
        _set_attributes(node, props, graph)
        graph.add_node(node)
        return CLIResult.ok(f"Created node '{node_id}'", changed=True)

    def _create_edge(self, tokens: list[str]) -> CLIResult:
        from tangled_api.model import Edge

        self._cleared = False
        edge_id, tokens = _consume_flag(tokens, "--id")
        if edge_id is None:
            raise CLIError("create edge requires --id=<id>")

        prop_tokens, positional = _consume_all_flag(tokens, "--property")
        clean_positional = []
        for tok in positional:
            if tok.startswith("--") and "=" in tok:
                prop_tokens.append(tok[2:])
            else:
                clean_positional.append(tok)

        if len(clean_positional) < 2:
            raise CLIError(
                "create edge requires source and target node ids, "
                "e.g.  create edge --id=e1 node1 node2"
            )

        source_id, target_id = clean_positional[0], clean_positional[1]
        props = _parse_properties(prop_tokens)
        graph = self.workspace.graph

        if source_id not in graph.nodes:
            raise CLIError(f"Source node '{source_id}' does not exist")
        if target_id not in graph.nodes:
            raise CLIError(f"Target node '{target_id}' does not exist")
        if edge_id in graph.edges:
            raise CLIError(f"Edge '{edge_id}' already exists")

        edge = Edge(id=edge_id, source_id=source_id, target_id=target_id)
        _set_attributes(edge, props, graph)
        graph.add_edge(edge)
        return CLIResult.ok(
            f"Created edge '{edge_id}' ({source_id} → {target_id})", changed=True
        )

    def _edit(self, tokens: list[str]) -> CLIResult:
        if not tokens:
            raise CLIError("Usage: edit node|edge --id=<id> --property key=value ...")
        kind = tokens[0].lower()
        rest = tokens[1:]
        if kind == "node":
            return self._edit_node(rest)
        elif kind == "edge":
            return self._edit_edge(rest)
        else:
            raise CLIError(f"Unknown entity '{kind}'. Use 'node' or 'edge'.")

    def _edit_node(self, tokens: list[str]) -> CLIResult:
        node_id, tokens = _consume_flag(tokens, "--id")
        if node_id is None:
            raise CLIError("edit node requires --id=<id>")

        prop_tokens, _ = _consume_all_flag(tokens, "--property")
        if not prop_tokens:
            raise CLIError("edit node requires at least one --property key=value")

        props = _parse_properties(prop_tokens)
        graph = self.workspace.graph
        if node_id not in graph.nodes:
            raise CLIError(f"Node '{node_id}' does not exist")

        _set_attributes(graph.nodes[node_id], props, graph)
        changed_keys = ", ".join(props.keys())
        return CLIResult.ok(f"Updated node '{node_id}': {changed_keys}", changed=True)

    def _edit_edge(self, tokens: list[str]) -> CLIResult:
        edge_id, tokens = _consume_flag(tokens, "--id")
        if edge_id is None:
            raise CLIError("edit edge requires --id=<id>")

        prop_tokens, _ = _consume_all_flag(tokens, "--property")
        if not prop_tokens:
            raise CLIError("edit edge requires at least one --property key=value")

        props = _parse_properties(prop_tokens)
        graph = self.workspace.graph
        if edge_id not in graph.edges:
            raise CLIError(f"Edge '{edge_id}' does not exist")

        _set_attributes(graph.edges[edge_id], props, graph)
        changed_keys = ", ".join(props.keys())
        return CLIResult.ok(f"Updated edge '{edge_id}': {changed_keys}", changed=True)

    def _delete(self, tokens: list[str]) -> CLIResult:
        if not tokens:
            raise CLIError("Usage: delete node|edge --id=<id>")
        kind = tokens[0].lower()
        rest = tokens[1:]
        if kind == "node":
            return self._delete_node(rest)
        elif kind == "edge":
            return self._delete_edge(rest)
        else:
            raise CLIError(f"Unknown entity '{kind}'. Use 'node' or 'edge'.")

    def _delete_node(self, tokens: list[str]) -> CLIResult:
        node_id, _ = _consume_flag(tokens, "--id")
        if node_id is None:
            raise CLIError("delete node requires --id=<id>")

        graph = self.workspace.graph
        if node_id not in graph.nodes:
            raise CLIError(f"Node '{node_id}' does not exist")

        # Guard: node must have no connected edges
        connected = [
            eid for eid, e in graph.edges.items()
            if e.source_id == node_id or e.target_id == node_id
        ]
        if connected:
            edge_list = ", ".join(connected)
            raise CLIError(
                f"Cannot delete node '{node_id}' - it is connected by "
                f"edge(s): {edge_list}. Delete those edges first."
            )

        graph.remove_node(node_id)
        return CLIResult.ok(f"Deleted node '{node_id}'", changed=True)

    def _delete_edge(self, tokens: list[str]) -> CLIResult:
        edge_id, _ = _consume_flag(tokens, "--id")
        if edge_id is None:
            raise CLIError("delete edge requires --id=<id>")

        graph = self.workspace.graph
        if edge_id not in graph.edges:
            raise CLIError(f"Edge '{edge_id}' does not exist")

        graph.remove_edge(edge_id)
        return CLIResult.ok(f"Deleted edge '{edge_id}'", changed=True)

    def _filter(self, tokens: list[str]) -> CLIResult:
        if not tokens:
            raise CLIError("Usage: filter '<expression>'  e.g.  filter 'Age>30'")
        self._cleared = False
        query = " ".join(tokens)
        self.workspace.filter(query)
        node_count = len(self.workspace.graph.nodes)
        return CLIResult.ok(f"Filter applied - {node_count} node(s) remaining", changed=True)

    def _search(self, tokens: list[str]) -> CLIResult:
        if not tokens:
            raise CLIError("Usage: search '<term>'  e.g.  search 'Name=Tom'")
        self._cleared = False
        query = " ".join(tokens)
        self.workspace.search(query)
        node_count = len(self.workspace.graph.nodes)
        return CLIResult.ok(f"Search done - {node_count} node(s) matched", changed=True)

    def _show(self, tokens: list[str]) -> CLIResult:
        if not tokens:
            raise CLIError("Usage: show nodes|edges")
        kind = tokens[0].lower()

        if kind not in ("nodes", "edges"):
            raise CLIError(f"Unknown entity '{kind}'. Use 'nodes' or 'edges'.")

        if self._cleared:
            return CLIResult.ok("(no nodes)" if kind == "nodes" else "(no edges)")

        graph = self.workspace.graph

        if kind == "nodes":
            if not graph.nodes:
                return CLIResult.ok("(no nodes)")
            lines = []
            for nid, node in graph.nodes.items():
                attrs = getattr(node, "attributes", {})
                attr_str = "  ".join(
                    f"{k}={v.value}" for k, v in attrs.items()
                    if v.value is not None and str(v.value).strip() != ""
                ) if attrs else "(no attributes)"
                lines.append(f"{nid}  {attr_str}")
            return CLIResult.ok("\n".join(lines))

        else:
            if not graph.edges:
                return CLIResult.ok("(no edges)")
            lines = []
            for eid, edge in graph.edges.items():
                attrs = getattr(edge, "attributes", {})
                attr_str = "  ".join(
                    f"{k}={v.value}" for k, v in attrs.items()
                    if v.value is not None and str(v.value).strip() != ""
                ) if attrs else "(no attributes)"
                lines.append(f"{eid}  {edge.source_id} → {edge.target_id}  {attr_str}")
            return CLIResult.ok("\n".join(lines))