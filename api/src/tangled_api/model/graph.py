"""Graph data structure supporting directed/undirected and cyclic/acyclic graphs."""

import copy
import re
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from tangled_api.model.attribute import AttributeValue
from tangled_api.model.node import Node
from tangled_api.model.edge import Edge

_FILTER_QUERY_RE = re.compile(r'(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+)')
_TOKEN_RE = re.compile(r'(&&|\|\||\(|\)|!(?!=))')

_TOKEN_MAP = {'&&': 'AND', '||': 'OR', '!': 'NOT', '(': 'LPAREN', ')': 'RPAREN'}


def _tokenize_filter(query: str) -> List[Tuple[str, str]]:
    """Tokenize a filter expression into (type, value) pairs.

    Token types: AND, OR, NOT, LPAREN, RPAREN, PRED.
    """
    parts = _TOKEN_RE.split(query)
    tokens: List[Tuple[str, str]] = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        tok_type = _TOKEN_MAP.get(stripped)
        if tok_type:
            tokens.append((tok_type, stripped))
        else:
            tokens.append(('PRED', stripped))
    return tokens


class Graph:
    """
    Graph data structure supporting:
    - Directed and undirected graphs
    - Cyclic and acyclic graphs
    - Typed attribute values (int, str, float, date)

    This is the core data model passed between platform and plugins.
    """

    def __init__(self, directed: bool = True):
        """
        Initialize an empty graph.

        Args:
            directed: If True, edges are directed by default
        """
        self._directed = directed
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._adj_out: Dict[str, List[str]] = {}
        self._adj_in: Dict[str, List[str]] = {}


    @property
    def directed(self) -> bool:
        return self._directed

    @property
    def nodes(self) -> Dict[str, Node]:
        """ All nodes in the graph, keyed by ID """
        return dict(self._nodes)

    @property
    def edges(self) -> Dict[str, Edge]:
        """ All edges in the graph, keyed by ID """
        return dict(self._edges)

    def get_node_ids(self) -> List[str]:
        """ Get list of all node IDs """
        return list(self._nodes.keys())

    def get_edge_ids(self) -> List[str]:
        """ Get list of all edge IDs """
        return list(self._edges.keys())

    def add_node(self, node: Node) -> None:
        """ Add node to graph """
        if node.id in self._nodes:
            raise ValueError(f"Node with id {node.id} already exists")
        self._nodes[node.id] = node
        self._adj_out[node.id] = []
        self._adj_in[node.id] = []

    def remove_node(self, node_id: Union[str, int]) -> None:
        """
        Remove node from graph.
        Raises exception if node has edges.
        """
        node_id = str(node_id)
        if node_id not in self._nodes:
            raise ValueError(f"Node {node_id} not found")

        connected_edges = [
            e for e in self._edges.values()
            if e.source_id == node_id or e.target_id == node_id
        ]

        if connected_edges:
            raise ValueError(
                f"Cannot remove node {node_id}: has {len(connected_edges)} connected edges. "
                f"Remove edges first."
            )

        del self._nodes[node_id]
        del self._adj_out[node_id]
        del self._adj_in[node_id]

    def add_edge(self, edge: Edge) -> None:
        """ Add edge to graph """
        if edge.source_id not in self._nodes:
            raise ValueError(f"Source node {edge.source_id} not found")
        if edge.target_id not in self._nodes:
            raise ValueError(f"Target node {edge.target_id} not found")

        if edge.id in self._edges:
            raise ValueError(f"Edge with id {edge.id} already exists")

        self._edges[edge.id] = edge

        self._adj_out[edge.source_id].append(edge.target_id)
        self._adj_in[edge.target_id].append(edge.source_id)

        if not self.directed:
            self._adj_out[edge.target_id].append(edge.source_id)
            self._adj_in[edge.source_id].append(edge.target_id)

    def remove_edge(self, edge_id: str) -> None:
        """ Remove edge from graph """
        if edge_id not in self._edges:
            raise ValueError(f"Edge {edge_id} not found")

        edge = self._edges[edge_id]

        self._adj_out[edge.source_id].remove(edge.target_id)
        self._adj_in[edge.target_id].remove(edge.source_id)

        if not self.directed:
            self._adj_out[edge.target_id].remove(edge.source_id)
            self._adj_in[edge.source_id].remove(edge.target_id)

        del self._edges[edge_id]

    def update_node(self, node_id: str, updates: Dict[str, Any]) -> None:
        """
        Update multiple attributes of a node.

        Args:
            node_id: Node ID
            updates: Dictionary of {attribute_name: new_value}

        Raises:
            ValueError: If node not found
        """
        node = self.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        for key, value in updates.items():
            node.set_attribute(key, value)

    def update_edge(self, edge_id: str, updates: Dict[str, Any]) -> None:
        """
        Update multiple attributes of an edge.

        Args:
            edge_id: Edge ID
            updates: Dictionary of {attribute_name: new_value}
        """
        edge = self.get_edge(edge_id)
        if not edge:
            raise ValueError(f"Edge {edge_id} not found")

        for key, value in updates.items():
            edge.set_attribute(key, value)

    def get_node(self, node_id: str) -> Optional[Node]:
        """ Get node by ID """
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """ Get edge by ID """
        return self._edges.get(edge_id)

    def get_successors(self, node_id: str) -> List[Node]:
        return [self._nodes[n_id] for n_id in self._adj_out[node_id]]

    def get_predecessors(self, node_id: str) -> List[Node]:
        return [self._nodes[n_id] for n_id in self._adj_in[node_id]]

    def get_neighbors(self, node_id: str) -> List[Node]:
        if self.directed:
            neighbors = set(self._adj_out[node_id]) | set(self._adj_in[node_id])
        else:
            neighbors = set(self._adj_out[node_id])

        return [self._nodes[n] for n in neighbors]

    def get_edges_for_node(self, node_id: Union[str, int]) -> List[Edge]:
        """ Get all edges connected to node """
        node_id = str(node_id)
        return [
            e for e in self._edges.values()
            if e.source_id == node_id or e.target_id == node_id
        ]

    def has_cycle(self) -> bool:
        """ Check if graph contains cycles (DFS) """
        if not self.directed:
            return self._has_cycle_undirected()
        else:
            return self._has_cycle_directed()

    def _has_cycle_directed(self) -> bool:
        """ Detect cycle in directed graph (DFS) """
        visited = set()
        rec_stack = set()

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in self._adj_out[node_id]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self._nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        return False

    def _has_cycle_undirected(self) -> bool:
        """ Detect cycle in undirected graph """
        visited = set()

        def dfs(node_id, parent_id):
            visited.add(node_id)

            for neighbor_id in self._adj_out[node_id]:
                if neighbor_id not in visited:
                    if dfs(neighbor_id, node_id):
                        return True
                elif neighbor_id != parent_id:
                    return True
            return False

        for node_id in self._nodes:
            if node_id not in visited:
                if dfs(node_id, None):
                    return True
        return False

    def clone(self) -> 'Graph':
        """ Create a deep copy of the graph """
        return copy.deepcopy(self)

    def to_dict(self) -> Dict[str, Any]:
        """ Convert to dictionary for serialization """
        return {
            'directed': self.directed,
            'nodes': [node.to_dict() for node in self._nodes.values()],
            'edges': [edge.to_dict() for edge in self._edges.values()]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Graph':
        """ Create Graph from dictionary """
        graph = cls(directed=bool(data['directed']))

        for node_data in data.get('nodes', []):
            node = Node.from_dict(node_data)
            graph.add_node(node)

        for edge_data in data.get('edges', []):
            edge = Edge.from_dict(edge_data)
            graph.add_edge(edge)

        return graph

    def __len__(self):
        """ Return number of nodes """
        return len(self._nodes)

    def create_subgraph(self, node_ids: List[str]) -> 'Graph':
        """
        Create subgraph containing only specified nodes and edges between them.

        Args:
            node_ids: List of node IDs to include

        Returns:
            New Graph object with selected nodes and edges
        """
        subgraph = Graph(directed=self.directed)
        node_id_set = set(node_ids)

        for node_id in dict.fromkeys(node_ids):
            if node_id in self._nodes:
                node = self._nodes[node_id]
                new_node = Node(id=node.id)
                new_node.attributes = copy.deepcopy(node.attributes)
                subgraph.add_node(new_node)

        for edge in self._edges.values():
            if edge.source_id in node_id_set and edge.target_id in node_id_set:
                new_edge = Edge(
                    id=edge.id,
                    source_id=edge.source_id,
                    target_id=edge.target_id
                )
                new_edge.attributes = copy.deepcopy(edge.attributes)
                subgraph.add_edge(new_edge)

        return subgraph

    def filter_by_query(self, query: str) -> 'Graph':
        """
        Filter graph by attribute query. Supports compound boolean expressions.

        Simple:   <attribute> <op> <value>       e.g. age > 25
        Compound: <pred> && <pred>               e.g. age > 25 && salary >= 100
                  <pred> || <pred>               e.g. age > 30 || name == Alice
                  !<pred>  or  !(<expr>)         e.g. !(age > 50)
                  (<expr>) for grouping

        Comparison operators: ==, !=, >, >=, <, <=
        Logical operators:    && (AND), || (OR), ! (NOT)
        Precedence:           ! > && > ||

        Raises ValueError if query format is invalid or value has wrong type.
        """
        query = query.strip()
        if not query:
            raise ValueError("Filter query cannot be empty")

        tokens = _tokenize_filter(query)
        if not tokens:
            raise ValueError("Filter query cannot be empty")

        matching_ids, pos = self._parse_or(tokens, 0)
        if pos != len(tokens):
            raise ValueError("Unexpected tokens after filter expression")

        return self.create_subgraph(list(matching_ids))

    def _eval_predicate(self, pred_str: str) -> Set[str]:
        """Evaluate a single comparison predicate, returning matching node IDs."""
        pred_str = pred_str.strip()
        if not pred_str:
            raise ValueError("Empty predicate in filter expression")

        match = _FILTER_QUERY_RE.match(pred_str)
        if not match:
            raise ValueError(
                "Invalid filter format. Use: <attribute> <op> <value> "
                "(e.g. age > 25). Operators: ==, !=, >, >=, <, <="
            )

        attr_name, op, value_str = match.groups()
        attr_name = attr_name.strip()
        value_str = value_str.strip()

        expected_type = None
        for node in self._nodes.values():
            attr = node.get_attribute(attr_name)
            if attr is not None:
                expected_type = attr.type
                break

        if expected_type is None:
            raise ValueError(f"Attribute '{attr_name}' not found in graph")

        try:
            converted = self._parse_filter_value(value_str, expected_type)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Value {value_str!r} is not a valid {expected_type.value} for attribute '{attr_name}'"
            ) from e

        matching: Set[str] = set()
        for node_id, node in self._nodes.items():
            attr = node.get_attribute(attr_name)
            if attr is None:
                continue
            if self._compare(attr.value, op, converted):
                matching.add(node_id)

        return matching

    def _parse_or(self, tokens: List[Tuple[str, str]], pos: int) -> Tuple[Set[str], int]:
        """or_expr = and_expr ('||' and_expr)*"""
        result, pos = self._parse_and(tokens, pos)
        while pos < len(tokens) and tokens[pos][0] == 'OR':
            pos += 1
            right, pos = self._parse_and(tokens, pos)
            result = result | right
        return result, pos

    def _parse_and(self, tokens: List[Tuple[str, str]], pos: int) -> Tuple[Set[str], int]:
        """and_expr = not_expr ('&&' not_expr)*"""
        result, pos = self._parse_not(tokens, pos)
        while pos < len(tokens) and tokens[pos][0] == 'AND':
            pos += 1
            right, pos = self._parse_not(tokens, pos)
            result = result & right
        return result, pos

    def _parse_not(self, tokens: List[Tuple[str, str]], pos: int) -> Tuple[Set[str], int]:
        """not_expr = '!' not_expr | '(' or_expr ')' | predicate"""
        if pos >= len(tokens):
            raise ValueError("Unexpected end of filter expression")

        tok_type, tok_val = tokens[pos]

        if tok_type == 'NOT':
            result, pos = self._parse_not(tokens, pos + 1)
            return set(self._nodes.keys()) - result, pos

        if tok_type == 'LPAREN':
            result, pos = self._parse_or(tokens, pos + 1)
            if pos >= len(tokens) or tokens[pos][0] != 'RPAREN':
                raise ValueError("Unmatched parenthesis in filter expression")
            return result, pos + 1

        if tok_type == 'PRED':
            return self._eval_predicate(tok_val), pos + 1

        raise ValueError(f"Unexpected token in filter expression: {tok_val!r}")

    def search(self, query: str) -> 'Graph':
        """
        Search graph by text query. Returns subgraph of nodes whose attribute
        names or values contain the query (case-insensitive).

        Args:
            query: Search text

        Returns:
            New Graph with matching nodes and edges between them

        Raises:
            ValueError: If query is empty
        """
        query = query.strip()
        if not query:
            raise ValueError("Search query cannot be empty")

        query_lower = query.lower()
        matching_ids = []

        for node_id, node in self._nodes.items():
            for attr_name, attr in node.attributes.items():
                if query_lower in attr_name.lower():
                    matching_ids.append(node_id)
                    break
                if query_lower in str(attr.value).lower():
                    matching_ids.append(node_id)
                    break

        return self.create_subgraph(matching_ids)

    def _parse_filter_value(self, value_str: str, expected_type: AttributeValue) -> Any:
        """Parse value string to expected type. Raises ValueError on failure."""
        if expected_type == AttributeValue.INTEGER:
            return int(value_str)
        if expected_type == AttributeValue.FLOAT:
            return float(value_str)
        if expected_type == AttributeValue.STRING:
            return value_str
        if expected_type == AttributeValue.DATE:
            return date.fromisoformat(value_str)
        raise ValueError(f"Unknown type: {expected_type}")

    def _compare(self, attr_value: Any, op: str, filter_value: Any) -> bool:
        """Compare attribute value with filter value using the given operator."""
        if op == "==":
            return attr_value == filter_value
        if op == "!=":
            return attr_value != filter_value
        if op == ">":
            return attr_value > filter_value
        if op == ">=":
            return attr_value >= filter_value
        if op == "<":
            return attr_value < filter_value
        if op == "<=":
            return attr_value <= filter_value
        return False
