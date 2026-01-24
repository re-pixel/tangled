"""
Graph data model supporting directed/undirected and cyclic/acyclic graphs.

Attribute values can be: int, str, float, date (not stored as strings).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Union

# Supported attribute value types per specification
AttributeValue = Union[int, str, float, date]


@dataclass
class Node:
    """
    Represents a node (vertex) in the graph.
    
    Attributes:
        id: Unique identifier for the node
        attributes: Dictionary of attribute name -> value pairs
    """
    id: str
    attributes: Dict[str, AttributeValue] = field(default_factory=dict)
    
    # TODO: Implement node


@dataclass  
class Edge:
    """
    Represents an edge connecting two nodes in the graph.
    
    Attributes:
        id: Unique identifier for the edge
        source_id: ID of the source node
        target_id: ID of the target node
        attributes: Dictionary of attribute name -> value pairs
        directed: Whether this edge is directed (default: True)
    """
    id: str
    source_id: str
    target_id: str
    attributes: Dict[str, AttributeValue] = field(default_factory=dict)
    directed: bool = True
    
    # TODO: Implement edge


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
        
        # TODO: Implement graph
    
    @property
    def directed(self) -> bool:
        """Whether this graph is directed."""
        return self._directed
    
    @property
    def nodes(self) -> Dict[str, Node]:
        """All nodes in the graph, keyed by ID."""
        return self._nodes
    
    @property
    def edges(self) -> Dict[str, Edge]:
        """All edges in the graph, keyed by ID."""
        return self._edges
    
    # TODO: Add methods for:
    # - add_node, remove_node
    # - add_edge, remove_edge  
    # - get_neighbors, get_adjacent_edges
    # - subgraph creation (for search/filter results)
    # - cycle detection
    # - serialization/deserialization
