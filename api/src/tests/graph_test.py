"""
Unit tests for Graph data model.

Run with: python -m pytest test_graph.py -v
"""

import pytest
from datetime import date
from tangled_api.model import (
    Graph, Node, Edge, Attribute, AttributeValue
)

class TestAttribute:
    """Test Attribute class"""
    
    def test_type_mismatch_raises_error(self):
        with pytest.raises(TypeError):
            Attribute("age", "thirty", AttributeValue.INTEGER)


class TestNode:
    """Test Node class"""
    
    def test_create_empty_node(self):
        node = Node(id="node1")
        assert node.id == "node1"
        assert len(node.attributes) == 0
    
    def test_set_attribute_auto_detect(self):
        node = Node(id="n1")
        node.set_attribute("name", "Bob")
        node.set_attribute("age", 25)
        node.set_attribute("height", 1.75)
        node.set_attribute("birthdate", date(1990, 5, 15))
        
        assert node.get_attribute_value("name") == "Bob"
        assert node.get_attribute_value("age") == 25
        assert node.get_attribute_value("height") == 1.75
        assert node.get_attribute_value("birthdate") == date(1990, 5, 15)
    
    def test_set_attribute_explicit_type(self):
        node = Node(id="n1")
        node.set_attribute("score", 100, AttributeValue.INTEGER)
        attr = node.get_attribute("score")
        if (attr is not None):
            assert attr.type == AttributeValue.INTEGER
    
    def test_node_serialization(self):
        node = Node(id="n1")
        node.set_attribute("name", "Alice")
        node.set_attribute("age", 30)
        node.set_attribute("birthdate", date(1994, 3, 20))
        
        data = node.to_dict()
        assert data['id'] == "n1"
        assert data['attributes']['name']['value'] == "Alice"
        assert data['attributes']['age']['value'] == 30
        assert data['attributes']['birthdate']['value'] == "1994-03-20"
    
    def test_node_deserialization(self):
        data = {
            'id': "n1",
            'attributes': {
                'name': {'value': 'Alice', 'type': 'string'},
                'age': {'value': 30, 'type': 'integer'},
                'birthdate': {'value': '1994-03-20', 'type': 'date'}
            }
        }
        
        node = Node.from_dict(data)
        assert node.id == "n1"
        assert node.get_attribute_value("name") == "Alice"
        assert node.get_attribute_value("age") == 30
        assert node.get_attribute_value("birthdate") == date(1994, 3, 20)
    
    def test_node_equality(self):
        n1 = Node(id="n1")
        n2 = Node(id="n1")
        n3 = Node(id="n2")
        
        assert n1 == n2
        assert n1 != n3
    
    def test_node_hash(self):
        n1 = Node(id="n1")
        n2 = Node(id="n1")
        
        node_set = {n1, n2}
        assert len(node_set) == 1


class TestEdge:
    """Test Edge class"""
    
    def test_create_edge(self):
        edge = Edge(id="e1", source_id="n1", target_id="n2")
        assert edge.id == "e1"
        assert edge.source_id == "n1"
        assert edge.target_id == "n2"
    
    def test_edge_with_attributes(self):
        edge = Edge(id="e1", source_id="n1", target_id="n2")
        edge.set_attribute("weight", 5.5)
        edge.set_attribute("label", "knows")
        
        val1 = edge.get_attribute_value("weight")
        assert val1 == 5.5

        val2 = edge.get_attribute_value("label")
        assert val2 == "knows"
    
    def test_edge_serialization(self):
        edge = Edge(id="e1", source_id="n1", target_id="n2")
        edge.set_attribute("weight", 3.5)
        
        data = edge.to_dict()
        assert data['id'] == "e1"
        assert data['source_id'] == "n1"
        assert data['target_id'] == "n2"
        assert data['attributes']['weight']['value'] == 3.5


class TestGraph:
    """Test Graph class"""
    
    def test_create_empty_graph(self):
        graph = Graph()
        assert len(graph) == 0
        assert graph.directed is True
    
    def test_create_undirected_graph(self):
        graph = Graph(directed=False)
        assert graph.directed is False
    
    def test_add_nodes(self):
        graph = Graph()
        n1 = Node(id="n1")
        n2 = Node(id="n2")
        
        graph.add_node(n1)
        graph.add_node(n2)
        
        assert len(graph) == 2
        assert graph.get_node("n1") == n1
    
    def test_add_duplicate_node_raises_error(self):
        graph = Graph()
        n1 = Node(id="n1")
        
        graph.add_node(n1)
        
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(n1)
    
    def test_remove_node(self):
        graph = Graph()
        n1 = Node(id="n1")
        graph.add_node(n1)
        
        graph.remove_node("n1")
        
        assert len(graph) == 0
        assert graph.get_node("n1") is None
    
    def test_cannot_remove_node_with_edges(self):
        graph = Graph()
        n1 = Node(id="n1")
        n2 = Node(id="n2")
        graph.add_node(n1)
        graph.add_node(n2)
        
        edge = Edge(id="e1", source_id="n1", target_id="n2")
        graph.add_edge(edge)
        
        with pytest.raises(ValueError, match="has.*connected edges"):
            graph.remove_node("n1")
    
    def test_add_edge(self):
        graph = Graph()
        n1 = Node(id="n1")
        n2 = Node(id="n2")
        graph.add_node(n1)
        graph.add_node(n2)
        
        edge = Edge(id="e1", source_id="n1", target_id="n2")
        graph.add_edge(edge)
        
        assert len(graph.edges) == 1
        assert graph.get_edge("e1") == edge
    
    def test_add_edge_nonexistent_source_raises_error(self):
        graph = Graph()
        n2 = Node(id="n2")
        graph.add_node(n2)
        
        edge = Edge(id="e1", source_id="n1", target_id="n2")
        
        with pytest.raises(ValueError, match="Source node.*not found"):
            graph.add_edge(edge)
    
    def test_remove_edge(self):
        graph = Graph()
        n1 = Node(id="n1")
        n2 = Node(id="n2")
        graph.add_node(n1)
        graph.add_node(n2)
        
        edge = Edge(id="e1", source_id="n1", target_id="n2")
        graph.add_edge(edge)
        graph.remove_edge("e1")
        
        assert len(graph.edges) == 0
    
    def test_get_successors(self):
        graph = Graph(directed=True)
        n1 = Node(id="n1")
        n2 = Node(id="n2")
        n3 = Node(id="n3")
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        graph.add_edge(Edge("e1", "n1", "n2"))
        graph.add_edge(Edge("e2", "n1", "n3"))
        
        successors = graph.get_successors("n1")
        assert len(successors) == 2
        assert n2 in successors
        assert n3 in successors
    
    def test_get_predecessors(self):
        graph = Graph(directed=True)
        n1 = Node(id="n1")
        n2 = Node(id="n2")
        n3 = Node(id="n3")
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        graph.add_edge(Edge("e1", "n1", "n3"))
        graph.add_edge(Edge("e2", "n2", "n3"))
        
        predecessors = graph.get_predecessors("n3")
        assert len(predecessors) == 2
        assert n1 in predecessors
        assert n2 in predecessors
    
    def test_undirected_graph_neighbors(self):
        graph = Graph(directed=False)
        n1 = Node(id="n1")
        n2 = Node(id="n2")
        graph.add_node(n1)
        graph.add_node(n2)
        
        graph.add_edge(Edge("e1", "n1", "n2"))
        
        assert n2 in graph.get_neighbors("n1")
        assert n1 in graph.get_neighbors("n2")
    
    def test_update_node(self):
        graph = Graph()
        n1 = Node(id="n1")
        n1.set_attribute("name", "Alice")
        n1.set_attribute("age", 25)
        graph.add_node(n1)
        
        graph.update_node("n1", {"age": 26, "city": "Belgrade"})
        
        updated = graph.get_node("n1")
        if (updated is not None):
            assert updated.get_attribute_value("age") == 26
            assert updated.get_attribute_value("city") == "Belgrade"
    
    def test_create_subgraph(self):
        graph = Graph()
        
        for i in range(5):
            n = Node(id=f"n{i}")
            n.set_attribute("value", i * 10)
            graph.add_node(n)
        
        graph.add_edge(Edge("e01", "n0", "n1"))
        graph.add_edge(Edge("e12", "n1", "n2"))
        graph.add_edge(Edge("e23", "n2", "n3"))
        graph.add_edge(Edge("e34", "n3", "n4"))
        
        subgraph = graph.create_subgraph(["n1", "n2", "n3"])
        
        assert len(subgraph) == 3
        assert len(subgraph.edges) == 2
        assert "n0" not in subgraph.get_node_ids()
        assert "n1" in subgraph.get_node_ids()
    
    def test_has_cycle_directed_acyclic(self):
        graph = Graph(directed=True)
        
        graph.add_node(Node("n1"))
        graph.add_node(Node("n2"))
        graph.add_node(Node("n3"))
        
        graph.add_edge(Edge("e1", "n1", "n2"))
        graph.add_edge(Edge("e2", "n2", "n3"))
        
        assert graph.has_cycle() is False
    
    def test_has_cycle_directed_cyclic(self):
        graph = Graph(directed=True)
        
        graph.add_node(Node("n1"))
        graph.add_node(Node("n2"))
        graph.add_node(Node("n3"))
        
        graph.add_edge(Edge("e1", "n1", "n2"))
        graph.add_edge(Edge("e2", "n2", "n3"))
        graph.add_edge(Edge("e3", "n3", "n1"))
        
        assert graph.has_cycle() is True
    
    def test_has_cycle_undirected_acyclic(self):
        graph = Graph(directed=False)
        
        graph.add_node(Node("n1"))
        graph.add_node(Node("n2"))
        graph.add_node(Node("n3"))
        
        graph.add_edge(Edge("e1", "n1", "n2"))
        graph.add_edge(Edge("e2", "n2", "n3"))
        
        assert graph.has_cycle() is False
    
    def test_has_cycle_undirected_cyclic(self):
        graph = Graph(directed=False)
        
        graph.add_node(Node("n1"))
        graph.add_node(Node("n2"))
        graph.add_node(Node("n3"))
        
        graph.add_edge(Edge("e1", "n1", "n2"))
        graph.add_edge(Edge("e2", "n2", "n3"))
        graph.add_edge(Edge("e3", "n3", "n1"))
        
        assert graph.has_cycle() is True
    
    def test_graph_serialization(self):
        graph = Graph(directed=True)
        
        n1 = Node("n1")
        n1.set_attribute("name", "Alice")
        n2 = Node("n2")
        n2.set_attribute("name", "Bob")
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge(Edge("e1", "n1", "n2"))
        
        data = graph.to_dict()
        
        assert data['directed'] is True
        assert len(data['nodes']) == 2
        assert len(data['edges']) == 1
    
    def test_graph_deserialization(self):
        data = {
            'directed': True,
            'nodes': [
                {'id': 'n1', 'attributes': {'name': {'value': 'Alice', 'type': 'string'}}},
                {'id': 'n2', 'attributes': {'name': {'value': 'Bob', 'type': 'string'}}}
            ],
            'edges': [
                {'id': 'e1', 'source_id': 'n1', 'target_id': 'n2', 'attributes': {}}
            ]
        }
        
        graph = Graph.from_dict(data)
        
        assert graph.directed is True
        assert len(graph) == 2
        assert len(graph.edges) == 1
    
    def test_graph_clone(self):
        graph = Graph()
        n1 = Node("n1")
        n1.set_attribute("value", 100)
        graph.add_node(n1)
        
        clone = graph.clone()
        
        node = graph.get_node("n1")
        if (node is not None):
            node.set_attribute("value", 200)
        
        cloned = clone.get_node("n1")
        if (cloned is not None):
            assert cloned.get_attribute_value("value") == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])