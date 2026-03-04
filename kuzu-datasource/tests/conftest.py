"""
Pytest fixtures for Kuzu Data Source plugin tests.

Creates temporary Kuzu databases programmatically since Kuzu databases
are binary/platform-specific and cannot be committed as test fixtures.
"""

from datetime import date, timedelta

import kuzu
import pytest

from tangled_kuzu_datasource import KuzuDataSource


@pytest.fixture
def plugin():
    return KuzuDataSource()


@pytest.fixture
def acyclic_db(tmp_path):
    """3 Person nodes (John/Mike/Lucy Doe), 2 CHILD_OF edges. No cycles."""
    db_path = str(tmp_path / "acyclic_db")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    conn.execute(
        "CREATE NODE TABLE Person("
        "id STRING, first STRING, last STRING, years INT64, "
        "PRIMARY KEY(id))"
    )
    conn.execute("CREATE REL TABLE CHILD_OF(FROM Person TO Person)")
    conn.execute(
        'CREATE (:Person {id: "id1", first: "John", last: "Doe", years: 53})'
    )
    conn.execute(
        'CREATE (:Person {id: "id2", first: "Mike", last: "Doe", years: 25})'
    )
    conn.execute(
        'CREATE (:Person {id: "id3", first: "Lucy", last: "Doe", years: 27})'
    )
    conn.execute(
        'MATCH (a:Person {id: "id2"}), (b:Person {id: "id1"}) '
        "CREATE (a)-[:CHILD_OF]->(b)"
    )
    conn.execute(
        'MATCH (a:Person {id: "id3"}), (b:Person {id: "id1"}) '
        "CREATE (a)-[:CHILD_OF]->(b)"
    )
    del conn
    del db
    return db_path


@pytest.fixture
def cyclic_db(tmp_path):
    """3 Person nodes, 2 HAS_CHILD + 2 HAS_PARENT edges creating cycles."""
    db_path = str(tmp_path / "cyclic_db")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    conn.execute(
        "CREATE NODE TABLE Person("
        "id STRING, first STRING, last STRING, "
        "PRIMARY KEY(id))"
    )
    conn.execute("CREATE REL TABLE HAS_CHILD(FROM Person TO Person)")
    conn.execute("CREATE REL TABLE HAS_PARENT(FROM Person TO Person)")
    conn.execute('CREATE (:Person {id: "p1", first: "John", last: "Doe"})')
    conn.execute('CREATE (:Person {id: "p2", first: "Mike", last: "Doe"})')
    conn.execute('CREATE (:Person {id: "p3", first: "Lucy", last: "Doe"})')
    # John -> Mike, John -> Lucy (HAS_CHILD)
    conn.execute(
        'MATCH (a:Person {id: "p1"}), (b:Person {id: "p2"}) '
        "CREATE (a)-[:HAS_CHILD]->(b)"
    )
    conn.execute(
        'MATCH (a:Person {id: "p1"}), (b:Person {id: "p3"}) '
        "CREATE (a)-[:HAS_CHILD]->(b)"
    )
    # Mike -> John, Lucy -> John (HAS_PARENT) — creates cycles
    conn.execute(
        'MATCH (a:Person {id: "p2"}), (b:Person {id: "p1"}) '
        "CREATE (a)-[:HAS_PARENT]->(b)"
    )
    conn.execute(
        'MATCH (a:Person {id: "p3"}), (b:Person {id: "p1"}) '
        "CREATE (a)-[:HAS_PARENT]->(b)"
    )
    del conn
    del db
    return db_path


@pytest.fixture
def large_db(tmp_path):
    """210 Employee nodes with hierarchical REPORTS_TO edges and varied types."""
    db_path = str(tmp_path / "large_db")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    conn.execute(
        "CREATE NODE TABLE Employee("
        "id STRING, name STRING, level INT64, salary DOUBLE, "
        "start_date DATE, PRIMARY KEY(id))"
    )
    conn.execute("CREATE REL TABLE REPORTS_TO(FROM Employee TO Employee)")

    base_date = date(2020, 1, 1)
    for i in range(210):
        eid = f"emp{i}"
        name = f"Employee_{i}"
        level = i % 5
        salary = 50000.0 + i * 100
        d = (base_date + timedelta(days=i)).isoformat()
        conn.execute(
            f"CREATE (:Employee {{id: \"{eid}\", name: \"{name}\", "
            f"level: {level}, salary: {salary}, "
            f"start_date: date('{d}')}})"
        )

    # Hierarchy: employee i reports to employee i//10 (for i > 0)
    for i in range(1, 210):
        manager = i // 10
        conn.execute(
            f'MATCH (a:Employee {{id: "emp{i}"}}), '
            f'(b:Employee {{id: "emp{manager}"}}) '
            f"CREATE (a)-[:REPORTS_TO]->(b)"
        )

    del conn
    del db
    return db_path


@pytest.fixture
def types_db(tmp_path):
    """1 node with INT64, DOUBLE, STRING, DATE, BOOLEAN columns for type tests."""
    db_path = str(tmp_path / "types_db")
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    conn.execute(
        "CREATE NODE TABLE TypeTest("
        "id STRING, int_val INT64, float_val DOUBLE, str_val STRING, "
        "date_val DATE, bool_val BOOLEAN, PRIMARY KEY(id))"
    )
    conn.execute(
        "CREATE (:TypeTest {id: \"t1\", int_val: 42, float_val: 3.14, "
        "str_val: \"hello\", date_val: date('2024-01-15'), bool_val: true})"
    )
    del conn
    del db
    return db_path
