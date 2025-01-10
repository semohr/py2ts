# Contribution Guide

Thank you for your interest in contributing to our project! Please follow these guidelines to ensure a smooth contribution process.

## Prerequisites

- Python 3.10 or higher
- Git

## Setting Up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/semohr/py2ts.git
   cd py2ts
   ```
2. **Install the dependencies:**
    We recommend using a virtual environment to manage the dependencies.
   ```bash
   pip install -e .[dev]
   ```

## Install pre-commit hooks
We automatically check for code style and formatting issues using pre-commit hooks. To install the hooks, run the following command:

```bash
pip install pre-commit
pre-commit install
```

## Before Submitting a Pull Request

Verify that your code follows the project's coding standards and conventions. Run [Ruff](https://docs.astral.sh/ruff/) manually or use the pre-commit hooks to check for any issues. Additionally, run the tests to ensure that your changes do not break any existing functionality.

```bash
# Run Ruff manually
ruff check
# Run the tests
pytest
```
