"""Edge connecting two nodes in the graph."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

from tangled_api.model.attribute import (
    Attribute,
    AttributeValue,
    _resolve_attr_type,
    detect_attr_type,
    deserialize_attributes,
    serialize_attributes,
)


@dataclass
class Edge:
    """
    Represents an edge connecting two nodes in the graph.

    Attributes:
        id: Unique identifier for the edge
        source_id: ID of the source node
        target_id: ID of the target node
        attributes: Dictionary of attribute name -> value pairs
    """
    id: str
    source_id: str
    target_id: str
    attributes: Dict[str, Attribute] = field(default_factory=dict)

    def get_attribute(self, key: str) -> Optional[Attribute]:
        return self.attributes.get(key)

    def get_attribute_value(self, key: str) -> Optional[Any]:
        attr = self.attributes.get(key)
        return attr.value if attr else None

    def set_attribute(self, key: str, value: Any, attr_type: Optional[Union[AttributeValue, str]] = None):
        resolved = _resolve_attr_type(attr_type)
        if resolved is None:
            resolved = detect_attr_type(value)
        if resolved is None:
            raise ValueError("Unsupported attribute type")
        self.attributes[key] = Attribute(key, value, resolved)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'attributes': serialize_attributes(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        edge = cls(
            id=data['id'],
            source_id=data['source_id'],
            target_id=data['target_id'],
        )
        edge.attributes = deserialize_attributes(data.get('attributes', {}))
        return edge

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return self.id == other.id
