"""
Graph data model supporting directed/undirected and cyclic/acyclic graphs.

Attribute values can be: int, str, float, date (not stored as strings).
"""

import copy
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Union
from enum import Enum

# Supported attribute value types per specification
class AttributeValue(Enum):
    """ Supported attribute types """
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"


def _resolve_attr_type(attr_type: Union[AttributeValue, str, None]) -> Optional[AttributeValue]:
    """Resolve attr_type to AttributeValue. Accepts enum or string ('integer', 'string', 'float', 'date')."""
    if attr_type is None:
        return None
    if isinstance(attr_type, AttributeValue):
        return attr_type
    if isinstance(attr_type, str):
        try:
            return AttributeValue(attr_type.lower())
        except ValueError:
            raise ValueError(f"Unknown attribute type: {attr_type!r}. Use 'integer', 'string', 'float', or 'date'.")
    return None

@dataclass
class Attribute:
    """ Single attribute with type information """
    key: str
    value: Any
    type: AttributeValue

    def __post_init__(self):
        if self.type == AttributeValue.INTEGER and not isinstance(self.value, int):
            raise TypeError(f"Attribute '{self.key}' expects int, got {type(self.value).__name__}")
        if self.type == AttributeValue.FLOAT and not isinstance(self.value, float):
            raise TypeError(f"Attribute '{self.key}' expects float, got {type(self.value).__name__}")
        if self.type == AttributeValue.STRING and not isinstance(self.value, str):
            raise TypeError(f"Attribute '{self.key}' expects str, got {type(self.value).__name__}")
        if self.type == AttributeValue.DATE and not isinstance(self.value, date):
            raise TypeError(f"Attribute '{self.key}' expects date, got {type(self.value).__name__}")

@dataclass
class Node:
    """
    Represents a node (vertex) in the graph.
    
    Attributes:
        id: Unique identifier for the node
        attributes: Dictionary of attribute name -> Attribute objects (key, value, type)
    """
    id: str
    attributes: Dict[str, Attribute] = field(default_factory=dict)

    def get_attribute(self, key: str) -> Optional[Attribute]:
        return self.attributes.get(key)
    
    def get_attribute_value(self, key: str) -> Optional[Any]:
        attr = self.attributes.get(key)
        return attr.value if attr else None

    def set_attribute(self, key: str, value: Any, attr_type: Optional[Union[AttributeValue, str]] = None):
        resolved = _resolve_attr_type(attr_type)
        if resolved is None:
            resolved = self._detect_type(value)
        if resolved is None:
            raise ValueError("Unsupported attribute type")
        attr_type = resolved

        if attr_type == AttributeValue.INTEGER and not isinstance(value, int):
            raise TypeError("Value must be int")
        if attr_type == AttributeValue.FLOAT and not isinstance(value, float):
            raise TypeError("Value must be float")
        if attr_type == AttributeValue.STRING and not isinstance(value, str):
            raise TypeError("Value must be str")
        if attr_type == AttributeValue.DATE and not isinstance(value, date):
            raise TypeError("Value must be date")

        self.attributes[key] = Attribute(key, value, attr_type)


    @staticmethod
    def _detect_type(value: Any) -> Optional[AttributeValue]:
        if isinstance(value, int):
            return AttributeValue.INTEGER
        elif isinstance(value, float):
            return AttributeValue.FLOAT
        elif isinstance(value, str):
            return AttributeValue.STRING
        elif isinstance(value, date):
            return AttributeValue.DATE
        else:
            return None

        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'attributes': {
                k: {'value': 
                        v.value.isoformat() 
                        if isinstance(v.value, date) 
                        else v.value, 
                    'type': v.type.value} 
                for k, v in self.attributes.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        node = cls(id=data['id'])
        
        for key, attr_data in data.get('attributes', {}).items():
            attr_type = AttributeValue(attr_data['type'])

            value = attr_data['value']
            if attr_type == AttributeValue.DATE:
                value = date.fromisoformat(value)

            node.attributes[key] = Attribute(
                key=key,
                value=value,
                type=attr_type
            )
        
        return node
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id


@dataclass  
class Edge:
    """
    Represents an edge connecting two nodes in the graph.
    
    Attributes:
        id: Unique identifier for the edge
        source_id: ID of the source node
        target_id: ID of the target node
        attributes: Dictionary of attribute name -> value pairs
    """
    id: str
    source_id: str
    target_id: str
    attributes: Dict[str, Attribute] = field(default_factory=dict)

    def get_attribute(self, key: str) -> Optional[Attribute]:
        return self.attributes.get(key)
    
    def get_attribute_value(self, key: str) -> Optional[Any]:
        attr = self.attributes.get(key)
        return attr.value if attr else None
    
    def set_attribute(self, key: str, value: Any, attr_type: Optional[Union[AttributeValue, str]] = None):
        """ Set edge attribute with type detection """
        resolved = _resolve_attr_type(attr_type)
        if resolved is None:
            resolved = Node._detect_type(value)
        if resolved is None:
            raise ValueError("Unsupported attribute type")
        attr_type = resolved
        
        if attr_type == AttributeValue.INTEGER and not isinstance(value, int):
            raise TypeError("Value must be int")
        if attr_type == AttributeValue.FLOAT and not isinstance(value, float):
            raise TypeError("Value must be float")
        if attr_type == AttributeValue.STRING and not isinstance(value, str):
            raise TypeError("Value must be str")
        if attr_type == AttributeValue.DATE and not isinstance(value, date):
            raise TypeError("Value must be date")
        
        self.attributes[key] = Attribute(key, value, attr_type)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'attributes': {
                k: {'value': 
                        v.value.isoformat() 
                        if isinstance(v.value, date) 
                        else v.value, 
                    'type': v.type.value}
                for k, v in self.attributes.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        edge = cls(
            id=data['id'],
            source_id=data['source_id'],
            target_id=data['target_id']
        )
        
        for key, attr_data in data.get('attributes', {}).items():
            attr_type = AttributeValue(attr_data['type'])

            value = attr_data['value']
            if attr_type == AttributeValue.DATE:
                value = date.fromisoformat(value)

            edge.attributes[key] = Attribute(
                key=key,
                value=value,
                type=attr_type
            )
        
        return edge
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return self.id == other.id


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
            
            for neighbor in self.get_neighbors(node_id):
                if neighbor.id not in visited:
                    if dfs(neighbor.id, node_id):
                        return True
                elif neighbor.id != parent_id:
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
        
        for node_id in dict.fromkeys(node_ids):
            if node_id in self._nodes:
                node = self._nodes[node_id]
                new_node = Node(id=node.id)
                new_node.attributes = copy.deepcopy(node.attributes)
                subgraph.add_node(new_node)
        
        for edge in self._edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
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
        Filter graph by attribute query. Returns subgraph of nodes matching the filter.
        
        Format: <attribute> <comparator> <value>
        Comparators: ==, !=, >, >=, <, <=
        
        Raises ValueError if query format is invalid or value has wrong type for the attribute.
        """
        query = query.strip()
        if not query:
            raise ValueError("Filter query cannot be empty")
        
        match = re.match(r'(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+)', query)
        if not match:
            raise ValueError(
                "Invalid filter format. Use: <attribute> <op> <value> "
                "(e.g. age > 25). Operators: ==, !=, >, >=, <, <="
            )
        
        attr_name, op, value_str = match.groups()
        attr_name = attr_name.strip()
        value_str = value_str.strip()
        
        # Find expected type from first node that has this attribute
        expected_type = None
        for node in self._nodes.values():
            attr = node.get_attribute(attr_name)
            if attr is not None:
                expected_type = attr.type
                break
        
        if expected_type is None:
            raise ValueError(f"Attribute '{attr_name}' not found in graph")
        
        # Convert value string to expected type
        try:
            converted = self._parse_filter_value(value_str, expected_type)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Value {value_str!r} is not a valid {expected_type.value} for attribute '{attr_name}'"
            ) from e
        
        # Collect matching node IDs
        matching_ids = []
        for node_id, node in self._nodes.items():
            attr = node.get_attribute(attr_name)
            if attr is None:
                continue
            if self._compare(attr.value, op, converted):
                matching_ids.append(node_id)
        
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