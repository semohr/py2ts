# Supported Types

Py2Ts should support most types out of the box, feel free to open an issue if you encounter any problems!

Internally we categorize python and typescript types into three categories depending on their complexity.

Generally the python `None` type is convertible to `null` or `undefined` in typescript, depending on preference. By default `None` is converted to `null`
but this behavior may be changed with the `none_to_null` option. 

```python
# Global configuration
from py2ts.config import Config
Config["none_to_null"] = False
```

```python
# Pass configuration to the `generate` function
from py2ts import generate_ts
generate_ts(type(None), config={"none_to_null": False}) # -> undefined
```

## Primitive types

TODO: paragraph

| Python Type       | TypeScript                     |
|-------------------|--------------------------------|
| `str`             | `string`                       |
| `int`             | `number`                       |
| `float`           | `number`                       |
| `bool`            | `boolean`                      |
| `None`            | `null` or `undefined`          |
| `Any`             | `any`                          |
| `Literal["foo"]`  | `"foo"`                        |


## Derived 

All of these types are derived types contain one or multiple subtypes and inherit from the abstract {TODO:ref} class. 

| Python Type       | TypeScript                     |
|-------------------|--------------------------------|
| `list[T]`         | `Array<T>`                     |
| `tuple[T1, T2]`   | `[T1, T2]`                     |
| `Sequence[T]`     | `Array<T>`                     |
| `Union[T1, T2]`   | `T1 \| T2`                     |
| `T1 \| T2`        | `T1 \| T2`                     |
| `Optional[T]`     | `T \| null` or `T \| undefined`|


## Complex 

TODO: paragraph

| Python Type          | TypeScript Complex             |
|----------------------|--------------------------------|
| `Enum`               | `enum`                         |
| `TypedDict`          | `interface`                    |
| `DataClass`          | `interface`                    |
| `N: NotRequired[T]`  | `N?: T`                        |


