"""Data structures used in the code generation process.

This module defines the data structures used to represent TypeScript types and
interfaces, as well as the graph of interfaces that are generated from the Python
dataclasses.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import Annotated, Dict, List, Optional, Set

from py2ts.config import CONFIG

# Helper annotation for type names
TypeName = Annotated[str, "TypeName"]


class TypescriptPrimitive(Enum):
    """Represents a TypeScript primitive type."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"
    UNDEFINED = "undefined"
    UNKNOWN = "unknown"
    NEVER = "never"
    VOID = "void"
    ANY = "any"

    @classmethod
    def from_python_type(cls, py_type: type | UnionType) -> TypescriptPrimitive | None:
        """Convert a Python type to a corresponding TypeScript primitive type.

        Parameters
        ----------
        py_type : type
            The Python type to be converted.

        Returns
        -------
        TypescriptPrimitive | None
            The corresponding TypeScript primitive type, or `None` if no mapping exists.

        Notes
        -----
        The mapping between Python types and TypeScript primitives is as follows:
        - `str` -> `TypescriptPrimitive.STRING`
        - `int` -> `TypescriptPrimitive.NUMBER`
        - `float` -> `TypescriptPrimitive.NUMBER`
        - `bool` -> `TypescriptPrimitive.BOOLEAN`
        - `None` -> `TypescriptPrimitive.NULL` if `CONFIG["none_as_null"]` is `True`,
          otherwise `TypescriptPrimitive.UNDEFINED`.

        If the provided `py_type` does not match any of the above, the method returns `None`.
        """
        TYPE_MAP: dict = {
            str: TypescriptPrimitive.STRING,
            int: TypescriptPrimitive.NUMBER,
            float: TypescriptPrimitive.NUMBER,
            bool: TypescriptPrimitive.BOOLEAN,
        }

        if CONFIG["none_as_null"]:
            TYPE_MAP[type(None)] = TypescriptPrimitive.NULL
        else:
            TYPE_MAP[type(None)] = TypescriptPrimitive.UNDEFINED

        return TYPE_MAP.get(py_type)


# ---------------------------------------------------------------------------- #
#                                  Basic types                                 #
# ---------------------------------------------------------------------------- #


class TypescriptType(ABC):
    """Represents a TypeScript type."""

    not_required: bool
    comment: Optional[str]

    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the type for use in the generated code."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Return a hash value for the type."""
        pass


@dataclass
class TSPrimitiveType(TypescriptType):
    """Represents a TypeScript primitive type.

    Example:
    string
    number
    boolean
    """

    type: TypescriptPrimitive

    def __str__(self) -> str:
        """Return a string representation of the primitive type for use in the generated code."""
        return self.type.value

    def __hash__(self) -> int:
        """Return a hash value for the primitive type."""
        return hash(self.type)


@dataclass
class TSUnionType(TypescriptType):
    """Represents a TypeScript union type.

    Example:
    string | number
    string | number | boolean
    """

    types: Set[TypescriptType]

    def __str__(self) -> str:
        """Return a string representation of the union type for use in the generated code."""
        return " | ".join(str(t) for t in self.types)

    def __hash__(self) -> int:
        """Return a hash value for the union type."""
        return hash(self.types)


@dataclass
class TSArrayType(TypescriptType):
    """Represents a TypeScript array type.

    Example:
    Array<string>
    Array<number|string>
    """

    element: TypescriptType

    def __str__(self) -> str:
        """Return a string representation of the array type for use in the generated code."""
        return f"Array<{str(self.element)}>"


@dataclass
class TSTupleType(TypescriptType):
    """Represents a TypeScript tuple type.

    Example:
    [string, number, boolean]
    """

    elements: Set[TypescriptType]

    def __str__(self) -> str:
        """Return a string representation of the tuple type for use in the generated code."""
        return f"[{', '.join(str(t) for t in self.elements)}]"


@dataclass
class TypescriptLiteralType(TypescriptType):
    """Represents a TypeScript literal type.

    Example:
    "foo"
    """

    element: str

    def __str__(self) -> str:
        """Return a string representation of the literal type for use in the generated code."""
        return f'"{self.element}"'


@dataclass
class TypescriptIntersectionType(TypescriptType):
    """Represents a TypeScript intersection type.

    Note:
    Not really used in the code generation process. But in theory, it could be used to
    represent the intersection of two types, similar to the union type.

    Example:
    {"foo":number} & {"bar":string}
    """

    types: Set[TypescriptType]

    def __str__(self) -> str:
        """Return a string representation of the intersection type for use in the generated code."""
        return " & ".join(str(t) for t in self.types)


# ---------------------------------------------------------------------------- #
#                                 complex types                                #
# ---------------------------------------------------------------------------- #


@dataclass
class TypescriptEnumType(TypescriptType):
    """Represents a TypeScript enum type.

    Example:
    enum Color {
        Red,
        Green,
        Blue
    }

    enum Direction {
        Up = "UP",
        Down = "DOWN",
        Left = "LEFT",
        Right = "RIGHT"
    }
    """

    name: str
    keys: List[str]
    values: Optional[List[str | int]]

    def __str__(self) -> str:
        """Return a string representation of the enum type for use in the generated code."""
        enum_str = f"enum {self.name}{{\n"
        if self.values is None:
            enum_str += ",\n\t".join(self.keys)
        else:
            for key, value in zip(self.keys, self.values):
                enum_str += f"\t{key} = "
                if isinstance(value, str):
                    enum_str += f'"{value}",\n'
                else:
                    enum_str += f"{value},\n"
            # remove last comma
            enum_str = enum_str[:-2]
        enum_str += "\n}"
        return enum_str


@dataclass
class TypescriptInterface(TypescriptType):
    """Represents a TypeScript interface.

    Example:
    interface Person {
        name: string;
        age: number;
        isStudent?: boolean;
    }
    """

    name: str
    elements: Dict[str, TypescriptType | TypescriptInterface | TypescriptEnumType]

    def __str__(self) -> str:
        """Return a string representation of the interface for use in the generated code."""
        interface_str = f"interface {self.name} {{\n"
        for key, value in self.elements.items():
            if isinstance(value, (TypescriptInterface, TypescriptEnumType)):
                interface_str += f"\t{key}: {value.name};\n"
            else:
                interface_str += f"\t{key}: {value};\n"
        interface_str += "}"
        return interface_str

    def str_recursive(self) -> str:
        """Return a string representation of the interface for use in the generated code.

        This method is used to generate the full interface definition, including nested
        interfaces and enums.
        """
        visited = set()
        interface_str = f"interface {self.name} {{\n"

        def add_interface(value: TypescriptInterface):
            nonlocal interface_str
            if value.name not in visited:
                visited.add(value.name)
                interface_str = f"{value.str_recursive()}\n\n{interface_str}"

        def add_enum(value: TypescriptEnumType):
            nonlocal interface_str
            if value.name not in visited:
                visited.add(value.name)
                interface_str = f"{value}\n\n{interface_str}"

        for key, value in self.elements.items():
            a = key
            if value.not_required:
                a += "?"

            if isinstance(value, TypescriptInterface):
                # add interface or enum to the top of the file
                add_interface(value)
                b = value.name
            elif isinstance(value, TypescriptEnumType):
                add_enum(value)
                b = value.name
            else:
                b = value

            # add the type to the interface
            interface_str += f"\t{a}: {b};\n"

        interface_str += "}"

        return interface_str
