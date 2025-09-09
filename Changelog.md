# 📦 Changelog

All notable changes to this project will be documented in this file.

## [0.6.0]

- Added configuration options for indentation style (tabs vs spaces) and size. Use `CONFIG.indent_with_tabs` and `CONFIG.indent_size` to customize the output format of the generated TypeScript code.

## [0.5.0]

- Add any_as_unknown config option to use `unknown` instead of `any` for the `Any` type from Python. This is now the default behavior [#2](https://github.com/semohr/py2ts/issues/2).

## [0.4.1]

### Fixed

- Support for edge cases in TypeScript interface generation, specifically when an interface has no elements but inherits from another type. This ensures that the generated TypeScript code is valid and does not produce empty interfaces.

## [0.4.0] 

### Added

- Support for excluding fields from TypeScript types using the `exclude` method. This only works for `TSComplex` types, such as `TSInterface`, `TSRecordType`, and `TSEnum`. The builder also now supports excluding fields when adding types.
- Added changelog :)

## [0.3.1] 

### Fixed

- Resolved a small issue with wrapped `dict` types.
- Fixed import error.

## [0.3.0] 

### Added

- Support for wrapper types, specifically `Mapped` from sqlalchemy.

## [0.2.1] 

### Added

- Support for ABCs in inheritance.

### Fixed

- Minor issue with builder logic when using inherited types.

## [0.2.0] 

### Added

- Support for class inheritance in type generation.

## [0.1.9] 

### Added

- `datetime` type support.

## [0.1.6] 

### Added

- Ordering support for TypeScript generic types.

### Fixed

- Incorrect ordering logic for record types.

## [0.1.4] 

### Changed

- TypeScript types are now consistently ordered by name.

## [0.1.3] 

### Changed

- `fullstr()` now ensures parent is always listed last.

## [0.1.2] 

### Added

- Example for Flask/Quart response typing.

## [0.1.0] 

### Added

- Initial support for `Record` types.

## [Unreleased - Pre 0.1.0]

### Added

- Full support for recursive types.
- Enum support, including nested dicts.
- Basic conversion of Python primitives to TypeScript.
- `__hash__` methods for `Record` and `Sequence` types.
- TypeScript `export` keyword support for cross-file usage.
- Py.typed marker for PEP 561 compliance.
- Small builder class to simplify TypeScript generation.
- Badges, docs, and contribution guides.
- GitHub workflows, ReadTheDocs integration, and pre-commit hooks.

### Changed

- Refactored base types into 3 categories.
- Renamed `convert` to `generate`.

### Fixed

- Compatibility fixes for Python 3.10.
- Hashing issue due to non-inherited methods.
- Inconsistent ordering behavior across Python versions.
- CI workflow issues with matrix and string casting.

Let me know if you'd like:

- This output as a `CHANGELOG.md` file
- GitHub diff links for each version
- A GitHub Action to generate this automatically with every tag push
