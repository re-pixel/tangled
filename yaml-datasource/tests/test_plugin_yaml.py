"""
Unit tests for YAML Data Source plugin.

Run with: pytest tests/ -v
"""

import pytest
from datetime import date
from pathlib import Path

from tangled_yaml_datasource import YamlDataSource

EXAMPLES_DIR = Path(__file__).parent / "examples"


class TestYamlDataSourceLoad:
    """Test loading YAML files into graphs."""

    def test_acyclic_tree_loads(self):
        """Acyclic tree from spec (Doe family) produces correct nodes and edges."""
        plugin = YamlDataSource()
        graph = plugin.load(
            file_path="acyclic_tree.yaml",
            base_path=str(EXAMPLES_DIR),
            id_attribute="id",
        )
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2

        n1 = graph.get_node("id1")
        assert n1 is not None
        assert n1.get_attribute_value("first") == "John"
        assert n1.get_attribute_value("last") == "Doe"
        assert n1.get_attribute_value("years") == 53

    def test_large_demo_meets_minimum_nodes(self):
        """Large demo has minimum 200 nodes per specification."""
        plugin = YamlDataSource()
        graph = plugin.load(
            file_path="large_demo.yaml",
            base_path=str(EXAMPLES_DIR),
            id_attribute="id",
        )
        assert len(graph.nodes) >= 200

    def test_cyclic_loads_with_references(self):
        """Cyclic graph from spec (parent/children with @id and parent refs)."""
        plugin = YamlDataSource()
        graph = plugin.load(
            file_path="cyclic.yaml",
            base_path=str(EXAMPLES_DIR),
            id_attribute="@id",
        )
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 4

        source_ids = {e.source_id for e in graph.edges.values()}
        target_ids = {e.target_id for e in graph.edges.values()}
        assert "28dddab1-4aa7-6e2b-b0b2-7ed9096aa9bc" in source_ids
        assert "28dddab1-4aa7-6e2b-b0b2-7ed9096aa9bc" in target_ids


class TestYamlDataSourceValidation:
    """Test parameter validation and error handling."""

    def test_missing_file_path_raises(self):
        plugin = YamlDataSource()
        with pytest.raises(ValueError, match="file_path parameter is required"):
            plugin.load()

    def test_file_not_found_raises(self):
        plugin = YamlDataSource()
        with pytest.raises(ValueError, match="File not found"):
            plugin.load(file_path="nonexistent.yaml", base_path=str(EXAMPLES_DIR))

    def test_invalid_yaml_raises(self):
        plugin = YamlDataSource()
        invalid_path = EXAMPLES_DIR / "invalid.yaml"
        invalid_path.write_text(":\n  - :\n    - : {{{")
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                plugin.load(
                    file_path="invalid.yaml",
                    base_path=str(EXAMPLES_DIR),
                )
        finally:
            invalid_path.unlink(missing_ok=True)


class TestYamlDataSourceTypes:
    """Test type parsing (int, float, str, date)."""

    def test_integer_preserved(self):
        """YAML integers are preserved as int type."""
        plugin = YamlDataSource()
        data_path = EXAMPLES_DIR / "types_test.yaml"
        data_path.write_text("id: p1\nname: Test\nage: 30\n")
        try:
            graph = plugin.load(
                file_path="types_test.yaml",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            n = graph.get_node("p1")
            assert n is not None
            assert n.get_attribute_value("age") == 30
            assert isinstance(n.get_attribute_value("age"), int)
        finally:
            data_path.unlink(missing_ok=True)

    def test_float_preserved(self):
        """YAML floats are preserved as float type."""
        plugin = YamlDataSource()
        data_path = EXAMPLES_DIR / "types_test.yaml"
        data_path.write_text("id: p1\nname: Test\nheight: 5.8\n")
        try:
            graph = plugin.load(
                file_path="types_test.yaml",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            n = graph.get_node("p1")
            assert n is not None
            assert n.get_attribute_value("height") == 5.8
        finally:
            data_path.unlink(missing_ok=True)

    def test_date_parsing_iso(self):
        """ISO date strings are parsed as date type."""
        plugin = YamlDataSource()
        data_path = EXAMPLES_DIR / "types_test.yaml"
        # Quote the date so YAML doesn't auto-parse it, testing our string->date logic
        data_path.write_text('id: p1\nbirthdate: "1990-05-15"\nname: Test\n')
        try:
            graph = plugin.load(
                file_path="types_test.yaml",
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

    def test_yaml_native_date(self):
        """YAML natively parsed dates are preserved."""
        plugin = YamlDataSource()
        data_path = EXAMPLES_DIR / "types_test.yaml"
        # Unquoted date: YAML safe_load parses this as datetime.date
        data_path.write_text("id: p1\nbirthdate: 1990-05-15\nname: Test\n")
        try:
            graph = plugin.load(
                file_path="types_test.yaml",
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

    def test_sequence_of_primitives_as_comma_separated(self):
        """Sequences of primitives become comma-separated string attribute."""
        plugin = YamlDataSource()
        data_path = EXAMPLES_DIR / "types_test.yaml"
        data_path.write_text("id: p1\ntags:\n  - a\n  - b\n  - c\nscores:\n  - 1\n  - 2\n  - 3\n")
        try:
            graph = plugin.load(
                file_path="types_test.yaml",
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
        plugin = YamlDataSource()
        data_path = EXAMPLES_DIR / "types_test.yaml"
        data_path.write_text("id: p1\nname: Test\nempty: null\n")
        try:
            graph = plugin.load(
                file_path="types_test.yaml",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            n = graph.get_node("p1")
            assert n is not None
            assert n.get_attribute_value("empty") is None
            assert "empty" not in n.attributes
        finally:
            data_path.unlink(missing_ok=True)


class TestYamlDataSourceRootSequence:
    """Test root sequence handling."""

    def test_root_sequence_each_element_top_level_node(self):
        """Root sequence: each element is a separate top-level node."""
        plugin = YamlDataSource()
        data_path = EXAMPLES_DIR / "root_seq_test.yaml"
        data_path.write_text("- id: a\n  name: A\n- id: b\n  name: B\n")
        try:
            graph = plugin.load(
                file_path="root_seq_test.yaml",
                base_path=str(EXAMPLES_DIR),
                id_attribute="id",
            )
            assert len(graph.nodes) == 2
            assert graph.get_node("a") is not None
            assert graph.get_node("b") is not None
            assert len(graph.edges) == 0
        finally:
            data_path.unlink(missing_ok=True)


class TestYamlDataSourcePluginInterface:
    """Test plugin interface (name, description, parameters)."""

    def test_plugin_has_name_and_description(self):
        plugin = YamlDataSource()
        assert plugin.name == "YAML Data Source"
        assert "YAML" in plugin.description

    def test_plugin_parameters_include_file_path_and_base_path(self):
        plugin = YamlDataSource()
        param_names = [p.name for p in plugin.parameters]
        assert "file_path" in param_names
        assert "base_path" in param_names
        assert "id_attribute" in param_names
