"""
Framework-agnostic graph serialization.
"""


def serialize_graph(graph) -> dict:
    """Convert a Graph object to a JSON-serializable dict.

    Returns ``{"nodes": [...], "edges": [...], "directed": bool}``.
    """
    if graph is None:
        return {"nodes": [], "edges": [], "directed": True}

    nodes = []
    for node_id, node in graph.nodes.items():
        attrs = {}
        for k, attr in node.attributes.items():
            value = attr.value
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            attrs[k] = {"value": str(value), "type": attr.type.value}
        nodes.append({"id": node_id, "attributes": attrs})

    edges = []
    for edge_id, edge in graph.edges.items():
        attrs = {}
        for k, attr in edge.attributes.items():
            value = attr.value
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            attrs[k] = {"value": str(value), "type": attr.type.value}
        edges.append({
            "id": edge_id,
            "source": edge.source_id,
            "target": edge.target_id,
            "attributes": attrs,
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "directed": graph.directed,
    }
