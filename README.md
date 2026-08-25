<p align="center">
    <h1 align="center">py2ts</h1>
</p>
<p align="center">
    <em>TypeScript type definitions from Python type hints</em>
</p>


<p align="center">
    <a href="https://github.com/semohr/py2ts/actions">
        <img alt="build status" src="https://img.shields.io/github/actions/workflow/status/semohr/py2ts/workflow.yml?style=flat-square" />
    </a>
    <a href="https://py2ts.readthedocs.io/en/latest/">
        <img alt="docs" src="https://img.shields.io/readthedocs/py2ts?style=flat-square" />
    </a>
    <a href="https://github.com/semohr/py2ts/blob/main/LICENSE">
        <img alt="License: GPL v3" src="https://img.shields.io/badge/License-GPL%20v3-blue.svg?style=flat-square" />
    </a>
</p>


## Features

<!-- start features -->
- **Complex Types Support**: Handle complex types such as enums and nested typed dictionaries.
- **Generic Types Support**: Convert Python generics (`TypeVar`s, bounded parameters, parametrized references) to TypeScript generics, including recursive and pydantic models.
- **Comprehensive Documentation**: Access detailed documentation, including a Quickstart Guide and API Reference, to help you get started and understand the library's capabilities.
<!-- end features -->

## Installation

You can install Py2Ts from pypi directly using pip:

```bash
pip install python2ts
```

## Quickstart

To generate TypeScript type definitions from Python type hints, use the `generate_ts` function from the `py2ts.generate` module. Here's an example:

```python
from py2ts import generate_ts

class Person:
    name: str
    age: int

print(generate_ts(Person))
```
This will output the following TypeScript type definition:
```typescript
export interface Person {
    name: string;
    age: number;
}
```

Please refer to the [Quickstart Guide](https://py2ts.readthedocs.io/en/latest/quickstart.html) for more examples and detailed instructions.



## Complex Types Support

Py2Ts supports complex types such as enums and nested typed dictionaries. Here's an example:

```python
from __future__ import annotations
from enum import Enum
from typing_extensions import NotRequired
from typing import TypedDict
from py2ts import generate_ts

class Color(Enum):
    RED = 1
    GREEN = "green"
    BLUE = "blue"   

class Polygon(TypedDict):
    color: Color
    edges: NotRequired[int]
    children: list[Polygon] | None

ts = generate_ts(Polygon)

print(ts.full_str())
```
This will output the following TypeScript type definition:
```typescript
export enum Color {
	RED = 1,
	GREEN = 'green',
	BLUE = 'blue',
}

export interface Polygon {
	color: Color;
	edges?: number;
	children: Array<Polygon> | null;
}
```


## Generic Types Support

Py2Ts converts Python generic classes to TypeScript generics. Type parameters, bounds,
parametrized references and recursive generics are supported:

```python
from typing import Generic, TypeVar
from dataclasses import dataclass
from py2ts import generate_ts

T = TypeVar("T")

@dataclass
class Node(Generic[T]):
    value: T
    next: "Node[T] | None" = None

print(generate_ts(Node).full_str())
```

```typescript
export interface Node<T> {
	value: T;
	next: Node<T> | null;
}
```

Bounded type parameters render as `T extends ...` (e.g. `TypeVar("T", bound=str)` becomes
`T extends string`), and instantiations keep their type arguments (e.g. `Node[str]` becomes
`Node<string>`). Pydantic generic models are supported as well. See the
[Supported Types](https://py2ts.readthedocs.io/en/latest/supported.html) page for details.


