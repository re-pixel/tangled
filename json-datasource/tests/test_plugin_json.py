"""
Unit tests for JSON Data Source plugin.

Run with: pytest tests/ -v
"""

import pytest
from datetime import date
from pathlib import Path

from tangled_json_datasource import JsonDataSource

EXAMPLES_DIR = Path(__file__).parent / "examples"


class TestJsonDataSourceLoad:
    """Test loading JSON files into graphs."""

    def test_acyclic_tree_loads(self):
        """Acyclic tree from spec (Doe family) produces correct nodes and edges."""
        plugin = JsonDataSource()
        graph = plugin.load(
            file_path="acyclic_tree.json",
            base_path=str(EXAMPLES_DIR),
            id_attribute="id",
        )
        assert len(graph.nodes) == 4
        assert len(graph.edges) == 2

        n1 = graph.get_node("id1")
        assert n1 is not None
        assert n1.get_attribute_value("first") == "John"
        assert n1.get_attribute_value("last") == "Doe"
        assert n1.get_attribute_value("years") == 53

    def test_cyclic_loads_with_references(self):
        """Cyclic graph from spec (parent/children with @id and parent refs)."""
        plugin = JsonDataSource()
        graph = plugin.load(
            file_path="cyclic.json",
            base_path=str(EXAMPLES_DIR),
            id_attribute="@id",
        )
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 4

        source_ids = {e.source_id for e in graph.edges.values()}
        target_ids = {e.target_id for e in graph.edges.values()}
        assert "28dddab1-4aa7-6e2b-b0b2-7ed9096aa9bc" in source_ids
        assert "28dddab1-4aa7-6e2b-b0b2-7ed9096aa9bc" in target_ids

    def test_large_demo_meets_minimum_nodes(self):
        """Large demo has minimum 200 nodes per specification."""
        plugin = JsonDataSource()
        graph = plugin.load(
            file_path="large_demo.json",
            base_path=str(EXAMPLES_DIR),
            id_attribute="id",
        )
        assert len(graph.nodes) >= 200


class TestJsonDataSourceValidation:
    """Test parameter validation and error handling."""

    def test_missing_file_path_raises(self):
        plugin = JsonDataSource()
        with pytest.raises(ValueError, match="file_path parameter is required"):
            plugin.load()

    def test_file_not_found_raises(self):
        plugin = JsonDataSource()
        with pytest.raises(ValueError, match="File not found"):
            plugin.load(file_path="nonexistent.json", base_path=str(EXAMPLES_DIR))

    def test_invalid_json_raises(self):
        plugin = JsonDataSource()
        invalid_path = EXAMPLES_DIR / "invalid.json"
        invalid_path.write_text("{ invalid }")
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                plugin.load(
                    file_path="invalid.json",
                    base_path=str(EXAMPLES_DIR),
                )
        finally:
            invalid_path.unlink(missing_ok=True)


class TestJsonDataSourceTypes:
    """Test type parsing (int, float, str, date)."""

    def test_date_parsing_iso(self):
        """ISO date strings are parsed as date type."""
        plugin = JsonDataSource()
        data_path = EXAMPLES_DIR / "types_test.json"
        data_path.write_text(
            '{"directed": true, "nodes": [{"id": "p1", "birthdate": "1990-05-15", "name": "Test"}]}'
        )
        try:
            graph = plugin.load(
                file_path="types_test.json",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            n = graph.get_node("p1")
            assert n is not None
            birth = n.get_attribute_value("birthdate")
            assert isinstance(birth, date)
            assert birth == date(1990, 5, 15)
        finally:
            data_path.unlink(missing_ok=True)

    def test_array_of_primitives_as_comma_separated(self):
        """Arrays of primitives become comma-separated string attribute."""
        plugin = JsonDataSource()
        data_path = EXAMPLES_DIR / "types_test.json"
        data_path.write_text(
            '{"directed": true, "nodes": [{"id": "p1", "tags": ["a", "b", "c"], "scores": [1, 2, 3]}]}'
        )
        try:
            graph = plugin.load(
                file_path="types_test.json",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            n = graph.get_node("p1")
            assert n is not None
            assert n.get_attribute_value("tags") == "a,b,c"
            assert n.get_attribute_value("scores") == "1,2,3"
        finally:
            data_path.unlink(missing_ok=True)

    def test_null_values_skipped(self):
        """Null values are not stored as attributes."""
        plugin = JsonDataSource()
        data_path = EXAMPLES_DIR / "types_test.json"
        data_path.write_text('{"directed": true, "nodes": [{"id": "p1", "name": "Test", "empty": null}]}')
        try:
            graph = plugin.load(
                file_path="types_test.json",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            n = graph.get_node("p1")
            assert n is not None
            assert n.get_attribute_value("empty") is None
            assert "empty" not in n.attributes
        finally:
            data_path.unlink(missing_ok=True)


class TestJsonDataSourceRootArray:
    """Test root array handling."""

    def test_root_array_each_element_top_level_node(self):
        """Root array: each element is a separate top-level node."""
        plugin = JsonDataSource()
        data_path = EXAMPLES_DIR / "root_array_test.json"
        data_path.write_text(
            '[{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]'
        )
        try:
            graph = plugin.load(
                file_path="root_array_test.json",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            assert len(graph.nodes) == 2
            assert graph.get_node("a") is not None
            assert graph.get_node("b") is not None
            assert len(graph.edges) == 0
        finally:
            data_path.unlink(missing_ok=True)


class TestJsonDataSourcePluginInterface:
    """Test plugin interface (name, description, parameters)."""

    def test_plugin_has_name_and_description(self):
        plugin = JsonDataSource()
        assert plugin.name == "JSON Data Source"
        assert "JSON" in plugin.description

    def test_plugin_parameters_include_file_path_and_base_path(self):
        plugin = JsonDataSource()
        param_names = [p.name for p in plugin.parameters]
        assert "file_path" in param_names
        assert "base_path" in param_names
        assert "id_attribute" in param_names