"""Node (vertex) in the graph."""

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
class Node:
    """
    Represents a node (vertex) in the graph.

    Attributes:
        id: Unique identifier for the node
        attributes: Dictionary of attribute name -> Attribute objects (key, value, type)
    """
    id: str
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
            'attributes': serialize_attributes(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        node = cls(id=data['id'])
        node.attributes = deserialize_attributes(data.get('attributes', {}))
        return node

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id
