# py2ts

Generates TypeScript type definitions from Python type hints using the `py2ts` library.

## Features

<!-- start features -->
- **Type Conversion**: Automatically convert Python type hints to TypeScript type definitions using the functions provided in the py2ts.generate module.
- **Complex Types Support**: Handle complex types such as enums and nested typed dictionaries.
- **Comprehensive Documentation**: Access detailed documentation, including a Quickstart Guide and API Reference, to help you get started and understand the library's capabilities.
<!-- end features -->

## Installation

You can install Py2Ts from git directly using pip:

```bash
pip install git+https://github.com/semohr/py2ts.git
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

Please refer to the [Quickstart Guide](https://py2ts.readthedocs.io/en/latest/quickstart.html) for more examples and detailed instructions.

