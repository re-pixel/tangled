"""
Unit tests for Graph data model.

Run with: pytest api/tests/ -v
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

    def test_set_attribute_explicit_type_via_string(self):
        """Test that set_attribute accepts type as string (public API, no AttributeValue import)."""
        node = Node(id="n1")
        node.set_attribute("score", 100, "integer")
        data = node.to_dict()
        assert data["attributes"]["score"]["type"] == "integer"
        assert data["attributes"]["score"]["value"] == 100

    def test_set_attribute_invalid_string_type_raises(self):
        node = Node(id="n1")
        with pytest.raises(ValueError, match="Unknown attribute type"):
            node.set_attribute("x", 1, "invalid_type")

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

    def test_remove_node_accepts_int_id(self):
        """Node IDs are stored as str; int should be normalized for lookup."""
        graph = Graph()
        graph.add_node(Node("1"))
        graph.remove_node(1)
        assert graph.get_node("1") is None

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

    def test_create_subgraph_deep_copy(self):
        """Mutating subgraph node attributes does not affect original graph."""
        graph = Graph()
        n1 = Node("n1")
        n1.set_attribute("value", 100)
        n2 = Node("n2")
        n2.set_attribute("value", 200)
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge(Edge("e1", "n1", "n2"))

        subgraph = graph.create_subgraph(["n1", "n2"])
        subgraph.get_node("n1").set_attribute("value", 999)

        assert graph.get_node("n1").get_attribute_value("value") == 100
        assert subgraph.get_node("n1").get_attribute_value("value") == 999

    def test_create_subgraph_handles_duplicate_ids(self):
        """Duplicate node IDs in the list should not raise."""
        graph = Graph()
        graph.add_node(Node("n1"))
        graph.add_node(Node("n2"))
        graph.add_edge(Edge("e1", "n1", "n2"))
        subgraph = graph.create_subgraph(["n1", "n1", "n2"])
        assert len(subgraph) == 2
        assert len(subgraph.edges) == 1

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


class TestGraphFilter:
    """Test filter_by_query method."""

    def test_filter_by_query_basic(self):
        graph = Graph()
        for i, age in enumerate([20, 25, 30, 35]):
            n = Node(id=f"n{i}")
            n.set_attribute("age", age)
            n.set_attribute("name", f"Person{i}")
            graph.add_node(n)
        graph.add_edge(Edge("e1", "n0", "n1"))
        graph.add_edge(Edge("e2", "n1", "n2"))
        graph.add_edge(Edge("e3", "n2", "n3"))

        filtered = graph.filter_by_query("age > 25")
        assert len(filtered) == 2
        assert "n2" in filtered.get_node_ids()
        assert "n3" in filtered.get_node_ids()
        assert "n0" not in filtered.get_node_ids()
        assert "n1" not in filtered.get_node_ids()
        assert len(filtered.edges) == 1

    def test_filter_by_query_wrong_type_raises(self):
        graph = Graph()
        n = Node("n1")
        n.set_attribute("age", 25)
        graph.add_node(n)

        with pytest.raises(ValueError, match="not a valid integer"):
            graph.filter_by_query("age > abc")

    def test_filter_by_query_invalid_format_raises(self):
        graph = Graph()
        n = Node("n1")
        n.set_attribute("age", 25)
        graph.add_node(n)

        with pytest.raises(ValueError, match="Invalid filter format"):
            graph.filter_by_query("invalid query without operator")

    def test_filter_by_query_unknown_attribute_raises(self):
        graph = Graph()
        n = Node("n1")
        n.set_attribute("age", 25)
        graph.add_node(n)

        with pytest.raises(ValueError, match="not found in graph"):
            graph.filter_by_query("nonexistent > 5")


class TestCompoundFilter:
    """Test compound filter expressions with &&, ||, !, ()."""

    @pytest.fixture()
    def graph(self):
        """4 nodes: n0(age=20,salary=80), n1(age=25,salary=120), n2(age=30,salary=60), n3(age=35,salary=150)"""
        g = Graph()
        for nid, age, salary in [("n0", 20, 80), ("n1", 25, 120), ("n2", 30, 60), ("n3", 35, 150)]:
            n = Node(nid)
            n.set_attribute("age", age)
            n.set_attribute("salary", salary)
            g.add_node(n)
        g.add_edge(Edge("e01", "n0", "n1"))
        g.add_edge(Edge("e12", "n1", "n2"))
        g.add_edge(Edge("e23", "n2", "n3"))
        return g

    def test_filter_compound_and(self, graph):
        result = graph.filter_by_query("age > 25 && salary >= 100")
        assert set(result.get_node_ids()) == {"n3"}

    def test_filter_compound_or(self, graph):
        result = graph.filter_by_query("age > 30 || salary < 70")
        # age>30: {n3}; salary<70: {n2}; union: {n2, n3}
        assert set(result.get_node_ids()) == {"n2", "n3"}

    def test_filter_compound_not(self, graph):
        result = graph.filter_by_query("!(age > 25)")
        assert set(result.get_node_ids()) == {"n0", "n1"}

    def test_filter_compound_precedence(self, graph):
        # && binds tighter than ||: age > 25 || (salary > 100 && age < 30)
        result = graph.filter_by_query("age > 25 || salary > 100 && age < 30")
        assert set(result.get_node_ids()) == {"n1", "n2", "n3"}

    def test_filter_compound_parens_override(self, graph):
        result = graph.filter_by_query("(age > 25 || salary > 100) && age < 35")
        assert set(result.get_node_ids()) == {"n1", "n2"}

    def test_filter_compound_nested_not(self, graph):
        result = graph.filter_by_query("age > 20 && !(salary >= 100)")
        assert set(result.get_node_ids()) == {"n2"}

    def test_filter_compound_double_and(self, graph):
        result = graph.filter_by_query("age >= 25 && age <= 30 && salary > 50")
        assert set(result.get_node_ids()) == {"n1", "n2"}

    def test_filter_single_predicate_unchanged(self, graph):
        result = graph.filter_by_query("age > 25")
        assert set(result.get_node_ids()) == {"n2", "n3"}

    def test_filter_compound_unbalanced_parens_raises(self, graph):
        with pytest.raises(ValueError):
            graph.filter_by_query("(age > 25")

    def test_filter_compound_empty_predicate_raises(self, graph):
        with pytest.raises(ValueError):
            graph.filter_by_query("age > 25 &&")

    def test_filter_compound_no_spaces(self, graph):
        result = graph.filter_by_query("age>30&&salary>=150")
        assert set(result.get_node_ids()) == {"n3"}


class TestGraphSearch:
    """Test search method."""

    def test_search_by_value_substring(self):
        graph = Graph()
        n1 = Node("n1")
        n1.set_attribute("name", "Alice")
        n1.set_attribute("age", 25)
        n2 = Node("n2")
        n2.set_attribute("name", "Bob")
        n2.set_attribute("age", 30)
        n3 = Node("n3")
        n3.set_attribute("name", "Alice")
        n3.set_attribute("age", 35)
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        graph.add_edge(Edge("e1", "n1", "n2"))
        graph.add_edge(Edge("e2", "n2", "n3"))

        result = graph.search("Alice")
        assert len(result) == 2
        assert "n1" in result.get_node_ids()
        assert "n3" in result.get_node_ids()
        assert "n2" not in result.get_node_ids()
        # n1-n2 and n2-n3 edges; n2 excluded, so no edges between n1 and n3
        assert len(result.edges) == 0

    def test_search_by_attribute_name_substring(self):
        graph = Graph()
        n1 = Node("n1")
        n1.set_attribute("full_name", "John")
        n2 = Node("n2")
        n2.set_attribute("age", 30)
        graph.add_node(n1)
        graph.add_node(n2)

        result = graph.search("name")
        assert len(result) == 1
        assert "n1" in result.get_node_ids()

    def test_search_empty_query_raises(self):
        graph = Graph()
        n = Node("n1")
        n.set_attribute("name", "Alice")
        graph.add_node(n)

        with pytest.raises(ValueError, match="Search query cannot be empty"):
            graph.search("")
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            graph.search("   ")

    def test_search_no_match_returns_empty_subgraph(self):
        graph = Graph()
        n = Node("n1")
        n.set_attribute("name", "Alice")
        n.set_attribute("age", 25)
        graph.add_node(n)

        result = graph.search("xyz")
        assert len(result) == 0
        assert result.get_node_ids() == []

    def test_search_edges_between_matching_nodes_preserved(self):
        graph = Graph()
        n1 = Node("n1")
        n1.set_attribute("name", "Alice")
        n2 = Node("n2")
        n2.set_attribute("name", "Alice")
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge(Edge("e1", "n1", "n2"))

        result = graph.search("Alice")
        assert len(result) == 2
        assert len(result.edges) == 1
        assert "e1" in result.get_edge_ids()

    def test_search_case_insensitive(self):
        graph = Graph()
        n = Node("n1")
        n.set_attribute("name", "Alice")
        graph.add_node(n)

        result = graph.search("alice")
        assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
