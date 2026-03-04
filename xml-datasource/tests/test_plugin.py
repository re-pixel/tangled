"""
Unit tests for XML Data Source plugin.

Run with: pytest xml-datasource/tests/ -v
"""

import pytest
from datetime import date
from pathlib import Path

from tangled_xml_datasource import XmlDataSource

EXAMPLES_DIR = Path(__file__).parent / "examples"


class TestXmlDataSourceLoad:
    """Test loading XML files into graphs."""

    def test_acyclic_tree_loads(self):
        """Acyclic company structure produces correct nodes and edges."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="acyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        assert len(graph.nodes) == 6
        assert len(graph.edges) == 5
        assert not graph.has_cycle()

    def test_acyclic_node_attributes(self):
        """Leaf elements become typed attributes on parent node."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="acyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        dept = graph.get_node("Department_1")
        assert dept is not None
        assert dept.get_attribute_value("name") == "Engineering"
        assert dept.get_attribute_value("location") == "Building A"

        emp = graph.get_node("Employee_1")
        assert emp is not None
        assert emp.get_attribute_value("name") == "Alice"
        assert emp.get_attribute_value("role") == "Manager"
        assert emp.get_attribute_value("salary") == 95000
        assert isinstance(emp.get_attribute_value("salary"), int)

    def test_acyclic_edges_structure(self):
        """Structural edges connect parent nodes to child nodes."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="acyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        edges = graph.edges
        company_to_dept = [
            e for e in edges.values()
            if e.source_id == "Company_1"
        ]
        assert len(company_to_dept) == 2

        dept1_to_emp = [
            e for e in edges.values()
            if e.source_id == "Department_1"
        ]
        assert len(dept1_to_emp) == 2

    def test_cyclic_loads_with_references(self):
        """Cyclic graph from spec (XPath references between Person elements)."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="cyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        assert len(graph.nodes) == 7
        assert len(graph.edges) == 8
        assert graph.has_cycle()

    def test_cyclic_reference_edges_exist(self):
        """Reference attributes create edges to the correct target nodes."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="cyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        edges = graph.edges

        owner1_to_person2 = [
            e for e in edges.values()
            if e.source_id == "owner_1" and e.target_id == "Person_2"
        ]
        assert len(owner1_to_person2) == 1

        owner2_to_person1 = [
            e for e in edges.values()
            if e.source_id == "owner_2" and e.target_id == "Person_1"
        ]
        assert len(owner2_to_person1) == 1

    def test_cyclic_node_attributes(self):
        """Person nodes have correct name attributes from leaf children."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="cyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        p1 = graph.get_node("Person_1")
        assert p1 is not None
        assert p1.get_attribute_value("name") == "Alice"

        p2 = graph.get_node("Person_2")
        assert p2 is not None
        assert p2.get_attribute_value("name") == "Peter"

    def test_large_demo_meets_minimum_nodes(self):
        """Large demo has minimum 200 nodes per specification."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="large_demo.xml",
            base_path=str(EXAMPLES_DIR),
        )
        assert len(graph.nodes) >= 200


class TestXmlDataSourceValidation:
    """Test parameter validation and error handling."""

    def test_missing_file_path_raises(self):
        plugin = XmlDataSource()
        with pytest.raises(ValueError, match="file_path parameter is required"):
            plugin.load()

    def test_file_not_found_raises(self):
        plugin = XmlDataSource()
        with pytest.raises(ValueError, match="File not found"):
            plugin.load(file_path="nonexistent.xml", base_path=str(EXAMPLES_DIR))

    def test_invalid_xml_raises(self):
        plugin = XmlDataSource()
        invalid_path = EXAMPLES_DIR / "invalid.xml"
        invalid_path.write_text("<broken><unclosed>")
        try:
            with pytest.raises(ValueError, match="Invalid XML"):
                plugin.load(
                    file_path="invalid.xml",
                    base_path=str(EXAMPLES_DIR),
                )
        finally:
            invalid_path.unlink(missing_ok=True)


class TestXmlDataSourceTypes:
    """Test type parsing (int, float, str, date)."""

    def test_integer_parsing(self):
        """Integer text content is parsed as int."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="acyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        emp = graph.get_node("Employee_1")
        assert emp is not None
        salary = emp.get_attribute_value("salary")
        assert salary == 95000
        assert isinstance(salary, int)

    def test_float_parsing(self):
        """Float text content is parsed as float."""
        plugin = XmlDataSource()
        tmp = EXAMPLES_DIR / "float_test.xml"
        tmp.write_text(
            "<Root><Item><price>19.99</price><name>Widget</name></Item></Root>"
        )
        try:
            graph = plugin.load(file_path="float_test.xml", base_path=str(EXAMPLES_DIR))
            item = graph.get_node("Item_1")
            assert item is not None
            assert item.get_attribute_value("price") == 19.99
            assert isinstance(item.get_attribute_value("price"), float)
        finally:
            tmp.unlink(missing_ok=True)

    def test_date_parsing(self):
        """Date text content is parsed as date when key hints or ISO format."""
        plugin = XmlDataSource()
        tmp = EXAMPLES_DIR / "date_test.xml"
        tmp.write_text(
            "<Root><Event><title>Meeting</title>"
            "<date>2024-03-15</date></Event></Root>"
        )
        try:
            graph = plugin.load(file_path="date_test.xml", base_path=str(EXAMPLES_DIR))
            event = graph.get_node("Event_1")
            assert event is not None
            d = event.get_attribute_value("date")
            assert isinstance(d, date)
            assert d == date(2024, 3, 15)
        finally:
            tmp.unlink(missing_ok=True)

    def test_string_preserved(self):
        """Non-numeric, non-date text stays as string."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="acyclic.xml",
            base_path=str(EXAMPLES_DIR),
        )
        dept = graph.get_node("Department_1")
        assert dept is not None
        loc = dept.get_attribute_value("location")
        assert loc == "Building A"
        assert isinstance(loc, str)


class TestXmlDataSourceXmlAttributes:
    """Test that XML element attributes become node attributes."""

    def test_xml_attributes_on_node(self):
        """XML attributes (key=val in opening tag) become node attributes."""
        plugin = XmlDataSource()
        tmp = EXAMPLES_DIR / "xml_attr_test.xml"
        tmp.write_text(
            '<Root><Person status="active" priority="3">'
            "<name>Alice</name></Person></Root>"
        )
        try:
            graph = plugin.load(
                file_path="xml_attr_test.xml", base_path=str(EXAMPLES_DIR)
            )
            person = graph.get_node("Person_1")
            assert person is not None
            assert person.get_attribute_value("status") == "active"
            assert person.get_attribute_value("priority") == 3
        finally:
            tmp.unlink(missing_ok=True)

    def test_id_attribute_used_as_node_id(self):
        """Elements with id XML attribute use that as their node ID."""
        plugin = XmlDataSource()
        tmp = EXAMPLES_DIR / "id_test.xml"
        tmp.write_text(
            '<Root><Item id="custom_id"><label>Test</label></Item></Root>'
        )
        try:
            graph = plugin.load(
                file_path="id_test.xml", base_path=str(EXAMPLES_DIR)
            )
            item = graph.get_node("custom_id")
            assert item is not None
            assert item.get_attribute_value("label") == "Test"
        finally:
            tmp.unlink(missing_ok=True)


class TestXmlDataSourceEdgeCases:
    """Test edge cases and special scenarios."""

    def test_single_element_no_children(self):
        """Root element with no children produces one node."""
        plugin = XmlDataSource()
        tmp = EXAMPLES_DIR / "single.xml"
        tmp.write_text('<Root attr="value"/>')
        try:
            graph = plugin.load(file_path="single.xml", base_path=str(EXAMPLES_DIR))
            assert len(graph.nodes) == 1
            assert len(graph.edges) == 0
        finally:
            tmp.unlink(missing_ok=True)

    def test_deeply_nested_structure(self):
        """Deeply nested elements all become nodes with correct edges."""
        plugin = XmlDataSource()
        tmp = EXAMPLES_DIR / "deep.xml"
        tmp.write_text(
            "<A><B><C><D><val>deep</val></D></C></B></A>"
        )
        try:
            graph = plugin.load(file_path="deep.xml", base_path=str(EXAMPLES_DIR))
            assert len(graph.nodes) == 4
            assert len(graph.edges) == 3
            d_node = graph.get_node("D_1")
            assert d_node is not None
            assert d_node.get_attribute_value("val") == "deep"
        finally:
            tmp.unlink(missing_ok=True)

    def test_custom_reference_attribute(self):
        """Custom reference_attribute name is respected."""
        plugin = XmlDataSource()
        tmp = EXAMPLES_DIR / "custom_ref.xml"
        tmp.write_text(
            "<Root>"
            '<Item id="item1"><name>First</name></Item>'
            '<Item id="item2"><name>Second</name>'
            '<link><Item ref="../../../Item[1]"/></link>'
            "</Item>"
            "</Root>"
        )
        try:
            graph = plugin.load(
                file_path="custom_ref.xml",
                base_path=str(EXAMPLES_DIR),
                reference_attribute="ref",
            )
            edges = graph.edges
            ref_edges = [
                e for e in edges.values()
                if e.target_id == "item1"
            ]
            assert len(ref_edges) >= 1
        finally:
            tmp.unlink(missing_ok=True)

    def test_large_demo_has_typed_attributes(self):
        """Large demo employees have int age, int salary, and date start_date."""
        plugin = XmlDataSource()
        graph = plugin.load(
            file_path="large_demo.xml",
            base_path=str(EXAMPLES_DIR),
        )
        emp_nodes = [n for nid, n in graph.nodes.items() if nid.startswith("Employee")]
        assert len(emp_nodes) > 0
        emp = emp_nodes[0]
        assert isinstance(emp.get_attribute_value("age"), int)
        assert isinstance(emp.get_attribute_value("salary"), int)
        assert isinstance(emp.get_attribute_value("start_date"), date)


class TestXmlDataSourcePluginInterface:
    """Test plugin interface (name, description, parameters)."""

    def test_plugin_has_name_and_description(self):
        plugin = XmlDataSource()
        assert plugin.name == "XML Data Source"
        assert "XML" in plugin.description

    def test_plugin_parameters_include_required(self):
        plugin = XmlDataSource()
        param_names = [p.name for p in plugin.parameters]
        assert "file_path" in param_names
        assert "base_path" in param_names
        assert "reference_attribute" in param_names

    def test_file_path_is_required(self):
        plugin = XmlDataSource()
        fp = next(p for p in plugin.parameters if p.name == "file_path")
        assert fp.required is True

    def test_optional_params_have_defaults(self):
        plugin = XmlDataSource()
        bp = next(p for p in plugin.parameters if p.name == "base_path")
        assert bp.required is False
        assert bp.default == "."
        ra = next(p for p in plugin.parameters if p.name == "reference_attribute")
        assert ra.required is False
        assert ra.default == "reference"
