"""
Attribute types and helpers for the graph data model.

Attribute values can be: int, str, float, date (not stored as strings).
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional, Union


class AttributeValue(Enum):
    """ Supported attribute types """
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"


def _resolve_attr_type(attr_type: Union[AttributeValue, str, None]) -> Optional[AttributeValue]:
    """Resolve attr_type to AttributeValue. Accepts enum or string ('integer', 'string', 'float', 'date')."""
    if attr_type is None:
        return None
    if isinstance(attr_type, AttributeValue):
        return attr_type
    if isinstance(attr_type, str):
        try:
            return AttributeValue(attr_type.lower())
        except ValueError:
            raise ValueError(f"Unknown attribute type: {attr_type!r}. Use 'integer', 'string', 'float', or 'date'.")
    return None


def detect_attr_type(value: Any) -> Optional[AttributeValue]:
    """Detect the AttributeValue type for a Python value."""
    if isinstance(value, int):
        return AttributeValue.INTEGER
    elif isinstance(value, float):
        return AttributeValue.FLOAT
    elif isinstance(value, str):
        return AttributeValue.STRING
    elif isinstance(value, date):
        return AttributeValue.DATE
    else:
        return None


@dataclass
class Attribute:
    """ Single attribute with type information """
    key: str
    value: Any
    type: AttributeValue

    def __post_init__(self):
        if self.type == AttributeValue.INTEGER and not isinstance(self.value, int):
            raise TypeError(f"Attribute '{self.key}' expects int, got {type(self.value).__name__}")
        if self.type == AttributeValue.FLOAT and not isinstance(self.value, float):
            raise TypeError(f"Attribute '{self.key}' expects float, got {type(self.value).__name__}")
        if self.type == AttributeValue.STRING and not isinstance(self.value, str):
            raise TypeError(f"Attribute '{self.key}' expects str, got {type(self.value).__name__}")
        if self.type == AttributeValue.DATE and not isinstance(self.value, date):
            raise TypeError(f"Attribute '{self.key}' expects date, got {type(self.value).__name__}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value.isoformat() if isinstance(self.value, date) else self.value,
            'type': self.type.value,
        }

    @classmethod
    def from_dict(cls, key: str, data: Dict[str, Any]) -> 'Attribute':
        attr_type = AttributeValue(data['type'])
        value = data['value']
        if attr_type == AttributeValue.DATE:
            value = date.fromisoformat(value)
        return cls(key=key, value=value, type=attr_type)


def serialize_attributes(attributes: Dict[str, Attribute]) -> Dict[str, Any]:
    """Serialize a dict of Attributes to a JSON-compatible dict."""
    return {k: v.to_dict() for k, v in attributes.items()}


def deserialize_attributes(data: Dict[str, Any]) -> Dict[str, Attribute]:
    """Deserialize a dict of attribute data to Attribute objects."""
    return {key: Attribute.from_dict(key, attr_data) for key, attr_data in data.items()}
