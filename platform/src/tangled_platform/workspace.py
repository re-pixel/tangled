"""
Workspace management.

A workspace contains:
- A loaded graph from a data source
- Active filters and searches (forming a subgraph chain)
- Current visualization state
"""

from typing import Any, Dict, List, Optional
from tangled_api.model import Graph, Node, Edge
from tangled_api.plugins import DataSourcePlugin, VisualizerPlugin


class Workspace:
    """
    Represents a single workspace with a graph and applied operations.
    
    Supports successive filter/search operations:
    G1 -> filter -> G2 -> search -> G3 -> filter -> G4 ...
    """
    
    def __init__(self, workspace_id: str):
        self.id = workspace_id
        self._original_graph: Optional[Graph] = None
        self._current_graph: Optional[Graph] = None
        self._operation_history: List[Dict[str, Any]] = []
        self._data_source_name: Optional[str] = None

        # g = Graph(directed=True)
        # nodes = [
        #     Node(id="n1", attributes={"name": "Alice", "age": 30, "city": "Sarajevo"}),
        #     Node(id="n2", attributes={"name": "Bob",   "age": 25, "city": "Beograd"}),
        #     Node(id="n3", attributes={"name": "Carol", "age": 35, "city": "Zagreb"}),
        #     Node(id="n4", attributes={"name": "David", "age": 28, "city": "Sarajevo"}),
        #     Node(id="n5", attributes={"name": "Eva",   "age": 22, "city": "Beograd"}),
        # ]
        # for node in nodes:
        #     g._nodes[node.id] = node
        # edges = [
        #     Edge(id="e1", source_id="n1", target_id="n2", attributes={"relation": "knows", "since": 2020}),
        #     Edge(id="e2", source_id="n2", target_id="n3", attributes={"relation": "knows", "since": 2019}),
        #     Edge(id="e3", source_id="n3", target_id="n4", attributes={"relation": "knows", "since": 2021}),
        #     Edge(id="e4", source_id="n4", target_id="n5", attributes={"relation": "knows", "since": 2022}),
        #     Edge(id="e5", source_id="n1", target_id="n5", attributes={"relation": "knows", "since": 2018}),
        #     Edge(id="e6", source_id="n5", target_id="n2", attributes={"relation": "knows", "since": 2023}),
        # ]
        # for edge in edges:
        #     g._edges[edge.id] = edge

        # self._original_graph = g
        # self._current_graph = g

    @property
    def graph(self) -> Optional[Graph]:
        """The current graph (after all applied operations)."""
        return self._current_graph
    
    @property
    def original_graph(self) -> Optional[Graph]:
        """The original graph before any operations."""
        return self._original_graph
    
    def load_data(self, plugin: DataSourcePlugin, **params: Any) -> None:
        """
        Load graph data using a data source plugin.
        
        Args:
            plugin: The data source plugin instance
            **params: Parameters for the plugin
        """
        self._original_graph = plugin.load(**params)
        self._current_graph = self._original_graph
        self._operation_history = []
        self._data_source_name = plugin.name
    
    def filter(self, query: str) -> None:
        """
        Apply a filter operation to the current graph.
        
        Format: <attribute> <comparator> <value>
        Comparators: ==, !=, >, >=, <, <=
        
        Args:
            query: Filter query string
            
        Raises:
            ValueError: If no graph loaded, invalid format, or value has wrong type
        """
        if self._current_graph is None:
            raise ValueError("No graph loaded")
        self._current_graph = self._current_graph.filter_by_query(query)
    
    def search(self, query: str) -> None:
        """
        Apply a search operation to the current graph.
        
        Finds nodes where attribute names or values contain the query.
        
        Args:
            query: Search text
        """
        # TODO: Implement search logic
        # - Check all attributes
        # - Generate subgraph of matching nodes
        # - Update _current_graph
        # - Record in _operation_history
        pass
    
    def reset(self) -> None:
        """Reset to the original graph, clearing all operations."""
        self._current_graph = self._original_graph
        self._operation_history = []
    
    def render(self, plugin: VisualizerPlugin) -> str:
        """
        Render the current graph using a visualizer plugin.
        
        Args:
            plugin: The visualizer plugin instance
            
        Returns:
            HTML string representation of the graph
        """
        
        if self._current_graph is None:
            return ""
        return plugin.render(self._current_graph)
            
