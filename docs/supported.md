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


## Primitive types

Primitive types are the most basic data types available within any programming language. These types serve as the building blocks for data manipulation. In Python and TypeScript, primitive types include simple types like strings, numbers, and booleans. They partially overlap, but there are some differences between the two languages.

| Python Type       | TypeScript                     |
|-------------------|--------------------------------|
| `str`             | `string`                       |
| `int`             | `number`                       |
| `float`           | `number`                       |
| `bool`            | `boolean`                      |
| `bytes`           | `Uint8Array`                   |
| `None`            | `null` or `undefined`          |
| `Any`             | `any`                          |
| `Literal["foo"]`  | `"foo"`                        |

## Derived 

Derived types are more complex types that are built from primitive types. They often involve collections or combinations of other types. These types include lists, tuples, sequences, and unions, which can contain multiple subtypes.

| Python Type       | TypeScript                     |
|-------------------|--------------------------------|
| `list[T]`         | `Array<T>`                     |
| `tuple[T1, T2]`   | `[T1, T2]`                     |
| `Sequence[T]`     | `Array<T>`                     |
| `Union[T1, T2]`   | `T1 \| T2`                     |
| `T1 \| T2`        | `T1 \| T2`                     |
| `Optional[T]`     | `T \| null` or `T \| undefined`|



## Complex 

Complex types are advanced types that often involve custom structures or classes. These types include enums, typed dictionaries, and data classes, which can represent more sophisticated data models.

| Python Type          | TypeScript Complex             |
|----------------------|--------------------------------|
| `Enum`               | `enum`                         |
| `TypedDict`          | `interface`                    |
| `DataClass`          | `interface`                    |
| `N: NotRequired[T]`  | `N?: T`                        |

