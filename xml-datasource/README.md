# Tangled XML Data Source Plugin

Data source plugin that parses XML files and constructs graphs.

## Features

- Parses arbitrary XML documents
- Elements with children become nodes
- Element attributes become node attributes  
- Leaf elements (no children) become parent node attributes
- Supports cyclic references via XPath-like `reference` attributes

## Installation

```bash
pip install -e /path/to/xml-datasource
```

## Usage

The plugin is automatically discovered by the platform.

```python
from tangled_platform import Platform

platform = Platform()
workspace = platform.create_workspace()

# Load XML data
workspace.load_data(
    platform.get_data_source("xml"),
    file_path="path/to/data.xml"
)
```

## Cyclic Graph Support

Use `reference` attribute with XPath-like paths:

```xml
<Persons>
    <Person>
        <name>Alice</name>
        <friend>
            <Person reference="../../Person[2]"/>
        </friend>
    </Person>
    <Person>
        <name>Bob</name>
    </Person>
</Persons>
```
