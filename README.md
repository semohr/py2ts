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

