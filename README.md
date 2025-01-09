# py2ts

Py2Ts is a Python package that generates TypeScript type definitions from Python type hints.

## Features

<!-- start features -->

<!-- end features -->



## Quickstart

<!-- start quickstart -->


<!-- end quickstart -->

For more information, visit [documentation][quickstart-docs].


### Supported Types

Py2Ts should support most types, feel free to open an issue if you encounter any problems!


| Python Type       | TypeScript Primitive           |
|-------------------|--------------------------------|
| `str`             | `string`                       |
| `int`             | `number`                       |
| `float`           | `number`                       |
| `bool`            | `boolean`                      |
| `None`            | `null` or `undefined`          |
| `Any`             | `any`                          |
| `Literal["foo"]`  | `"foo"`                        |

| Python Type       | TypeScript Derived             |
|-------------------|--------------------------------|
| `List[T]`         | `Array<T>`                     |
| `list[T]`         | `Array<T>`                     |
| `Sequence[T]`     | `Array<T>`                     |
| `ABCSequence[T]`  | `Array<T>`                     |
| `Tuple[T1, T2]`   | `[T1, T2]`                     |
| `tuple[T1, T2]`   | `[T1, T2]`                     |
| `Union[T1, T2]`   | `T1 \| T2`                     |
| `T1 \| T2`        | `T1 \| T2`                     |
| `Optional[T]`     | `T \| null` or `T \| undefined`|

| Python Type          | TypeScript Complex             |
|----------------------|--------------------------------|
| `Enum`               | `enum`                         |
| `TypedDict`          | `interface`                    |
| `DataClass`          | `interface`                    |
| `N: NotRequired[T]`  | `N?: T`                        |


The `None` type is converted to `null` or `undefined` based on the `none_to_null` option. By default, `None` is converted to `null` change the behavior by setting the `none_to_null` option to `false`.

```python
# Global configuration
from py2ts.config import Config
Config["none_to_null"] = False
```
```python
# Pass configuration to the `generate` function
from py2ts import generate
generate_ts(str, config={"none_to_null": False})
```


