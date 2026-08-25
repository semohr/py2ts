# Supported Types

Py2Ts should support most types out of the box, feel free to open an issue if you encounter any problems!

Internally we categorize python and typescript types into three categories depending on their complexity.

Generally the python `None` type is convertible to `null` or `undefined` in typescript, depending on preference. By default `None` is converted to `null`
but this behavior may be changed with the `none_to_null` option.

```python
from py2ts import generate_ts
generate_ts(type(None)) # => "null"

# Global configuration
from py2ts.config import Config
CONFIG.none_as_null = False
generate_ts(type(None)) # => "undefined"
```

The `Any` type is convertible to `unknown` by default, if you want to use `any` instead, you can change this behavior with the `any_as_unknown` option.

```python
from py2ts import generate_ts
from typing import Any
generate_ts(Any) # => "unknown"

from py2ts.config import Config
CONFIG.any_as_unknown = False
generate_ts(Any) # => "any"
```

## Primitive types

Primitive types are the most basic data types available within any programming language. These types serve as the building blocks for data manipulation. In Python and TypeScript, primitive types include simple types like strings, numbers, and booleans. They partially overlap, but there are some differences between the two languages.

| Python Type      | TypeScript            |
| ---------------- | --------------------- |
| `str`            | `string`              |
| `int`            | `number`              |
| `float`          | `number`              |
| `bool`           | `boolean`             |
| `bytes`          | `Uint8Array`          |
| `datetime`       | `Date`                |
| `None`           | `null` or `undefined` |
| `Any`            | `unknown` or `any`    |
| `Literal["foo"]` | `"foo"`               |

## Derived

Derived types are more complex types that are built from primitive types. They often involve collections or combinations of other types. These types include lists, tuples, sequences, and unions, which can contain multiple subtypes.

| Python Type     | TypeScript                      |
| --------------- | ------------------------------- |
| `list[T]`       | `Array<T>`                      |
| `tuple[T1, T2]` | `[T1, T2]`                      |
| `Sequence[T]`   | `Array<T>`                      |
| `dict[K, V]`    | `Record<K, V>`                  |
| `Union[T1, T2]` | `T1 \| T2`                      |
| `T1 \| T2`      | `T1 \| T2`                      |
| `Optional[T]`   | `T \| null` or `T \| undefined` |

## Complex

Complex types are advanced types that often involve custom structures or classes. These types include enums, typed dictionaries, and data classes, which can represent more sophisticated data models.

| Python Type         | TypeScript Complex |
| ------------------- | ------------------ |
| `Enum`              | `enum`             |
| `TypedDict`         | `interface`        |
| `DataClass`         | `interface`        |
| `N: NotRequired[T]` | `N?: T`            |

## Generics

Generic classes (classes with `TypeVar` parameters) are converted to TypeScript generics. Type
parameters render as `<T>`, bounded parameters as `T extends ...`, and references and
instantiations keep their type arguments.

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

| Python Type                 | TypeScript                 |
| --------------------------- | -------------------------- |
| `class Box(Generic[T])`     | `interface Box<T>`         |
| `TypeVar("T", bound=str)`   | `T extends string`         |
| `Node[T]` (field reference) | `Node<T>`                  |
| `Resource[str, str]`        | `Resource<string, string>` |
| Unresolved `TypeVar`        | `unknown`                  |

Bounded type parameters render with their bound:

```python
A = TypeVar("A")
T = TypeVar("T", bound=str)

class Resource(Generic[A, T]):
    type: T
    attributes: A
```

```typescript
export interface Resource<A, T extends string> {
  type: T;
  attributes: A;
}
```

Pydantic generic models are supported as well. Pydantic materializes parametrized models as
real classes (e.g. `AlbumResource(Resource[AlbumAttributes])`) and collapses self-references
to the identity class (e.g. `Resource[T]` inside a generic model); both are resolved back to
parametrized references (`Resource<AlbumAttributes>` and `Resource<T>`).

## Inheritance

Inheritance should mostly work out of the box, it seems like TypeDicts implement inheritance different from normal classes, so this is not supported yet.

## Indent Style

By default, py2ts uses tabs for indentation in the generated TypeScript code. If you prefer to use spaces instead, you can configure this behavior using the `indent_with_tabs` and `indent_size` options in the configuration.

```python
from py2ts.config import CONFIG
from py2ts import generate_ts

CONFIG.indent_with_tabs = False  # Use spaces for indentation
CONFIG.indent_size = 2           # Set the number of spaces per indentation level

generate_ts(your_python_type)  # The generated TypeScript code will use spaces for indentation
```
