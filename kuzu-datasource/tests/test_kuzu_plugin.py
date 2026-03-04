"""
Unit tests for Kuzu Data Source plugin.

Run with: pytest tests/ -v
"""

import pytest
from datetime import date


class TestKuzuDataSourceLoad:
    """Test loading Kuzu databases into graphs."""

    def test_acyclic_tree_loads(self, plugin, acyclic_db):
        """Acyclic tree (Doe family) produces correct nodes and edges."""
        graph = plugin.load(database_path=acyclic_db)

        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2

        n1 = graph.get_node("id1")
        assert n1 is not None
        assert n1.get_attribute_value("first") == "John"
        assert n1.get_attribute_value("last") == "Doe"
        assert n1.get_attribute_value("years") == 53

    def test_cyclic_loads(self, plugin, cyclic_db):
        """Cyclic graph produces correct nodes and edges."""
        graph = plugin.load(database_path=cyclic_db)

        assert len(graph.nodes) == 3
        assert len(graph.edges) == 4

    def test_large_demo_meets_minimum_nodes(self, plugin, large_db):
        """Large demo has minimum 200 nodes per specification."""
        graph = plugin.load(database_path=large_db)

        assert len(graph.nodes) >= 200


class TestKuzuDataSourceValidation:
    """Test parameter validation and error handling."""

    def test_missing_database_path_raises(self, plugin):
        with pytest.raises(ValueError, match="database_path parameter is required"):
            plugin.load()

    def test_database_not_found_raises(self, plugin):
        with pytest.raises(ValueError, match="Database not found"):
            plugin.load(database_path="/nonexistent/kuzu/db")

    def test_invalid_query_raises(self, plugin, acyclic_db):
        with pytest.raises(ValueError, match="Invalid Cypher query"):
            plugin.load(database_path=acyclic_db, query="NOT A VALID QUERY !!!")


class TestKuzuDataSourceTypes:
    """Test type mapping from Kuzu types to Tangled attribute types."""

    def test_integer_preserved(self, plugin, types_db):
        """Kuzu INT64 is preserved as int."""
        graph = plugin.load(database_path=types_db, node_id_property="id")
        n = graph.get_node("t1")
        assert n is not None
        assert n.get_attribute_value("int_val") == 42
        assert isinstance(n.get_attribute_value("int_val"), int)

    def test_float_preserved(self, plugin, types_db):
        """Kuzu DOUBLE is preserved as float."""
        graph = plugin.load(database_path=types_db, node_id_property="id")
        n = graph.get_node("t1")
        assert n is not None
        assert n.get_attribute_value("float_val") == pytest.approx(3.14)

    def test_string_preserved(self, plugin, types_db):
        """Kuzu STRING is preserved as str."""
        graph = plugin.load(database_path=types_db, node_id_property="id")
        n = graph.get_node("t1")
        assert n is not None
        assert n.get_attribute_value("str_val") == "hello"

    def test_date_preserved(self, plugin, types_db):
        """Kuzu DATE is preserved as date."""
        graph = plugin.load(database_path=types_db, node_id_property="id")
        n = graph.get_node("t1")
        assert n is not None
        val = n.get_attribute_value("date_val")
        assert isinstance(val, date)
        assert val == date(2024, 1, 15)


class TestKuzuDataSourceCyclic:
    """Test cyclic graph detection."""

    def test_graph_has_cycle(self, plugin, cyclic_db):
        """Cyclic database produces a graph with cycles."""
        graph = plugin.load(database_path=cyclic_db)
        assert graph.has_cycle() is True

    def test_parent_appears_as_source_and_target(self, plugin, cyclic_db):
        """Parent node appears as both edge source and edge target."""
        graph = plugin.load(database_path=cyclic_db)

        source_ids = {e.source_id for e in graph.edges.values()}
        target_ids = {e.target_id for e in graph.edges.values()}
        assert "p1" in source_ids
        assert "p1" in target_ids


class TestKuzuDataSourceCustomQuery:
    """Test custom Cypher queries."""

    def test_custom_query_filters_nodes(self, plugin, acyclic_db):
        """Custom query returns a subset of nodes."""
        graph = plugin.load(
            database_path=acyclic_db,
            query='MATCH (n:Person) WHERE n.years > 26 RETURN n',
        )
        # John (53) and Lucy (27) match; Mike (25) does not
        assert len(graph.nodes) == 2
        assert graph.get_node("id1") is not None  # John
        assert graph.get_node("id3") is not None  # Lucy

    def test_node_only_query(self, plugin, acyclic_db):
        """Query returning only nodes produces a graph with no edges."""
        graph = plugin.load(
            database_path=acyclic_db,
            query="MATCH (n:Person) RETURN n",
        )
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 0


class TestKuzuDataSourcePluginInterface:
    """Test plugin interface (name, description, parameters)."""

    def test_plugin_has_name_and_description(self, plugin):
        assert plugin.name == "Kuzu Data Source"
        assert "Kuzu" in plugin.description

    def test_plugin_parameters(self, plugin):
        param_names = [p.name for p in plugin.parameters]
        assert "database_path" in param_names
        assert "query" in param_names
        assert "node_id_property" in param_names

        db_param = next(p for p in plugin.parameters if p.name == "database_path")
        assert db_param.required is True

        query_param = next(p for p in plugin.parameters if p.name == "query")
        assert query_param.required is False
        assert query_param.default is not None
