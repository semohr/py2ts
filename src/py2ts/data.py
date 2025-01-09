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
from typing import Annotated, Dict, Iterator, List, Optional, Sequence, Set

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
#                                  Primitive types                             #
# ---------------------------------------------------------------------------- #


def _elements_to_names(
    elements: Sequence[TypescriptType] | Set[TypescriptType],
) -> List[str]:
    strs: List[str] = []
    for t in elements:
        if isinstance(t, TSComplex):
            strs.append(t.name)
        else:
            strs.append(str(t))
    return strs


@dataclass(kw_only=True)
class TypescriptType(ABC):
    """Represents a TypeScript type."""

    not_required: bool = False
    comment: Optional[str] = None

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


# ---------------------------------------------------------------------------- #
#                                 Derived Types                                #
# ---------------------------------------------------------------------------- #


@dataclass
class DerivedType(TypescriptType, ABC):
    """Represents a TypeScript derived type.

    This is an abstract class that is used as a base class for more complex types
    such as arrays, tuples, and unions.
    """

    elements: Set[TypescriptType] | TypescriptType

    def __hash__(self) -> int:
        """Return a hash value for the derived type."""
        return hash(self.elements)

    def __iter__(self) -> Iterator[TypescriptType]:
        """Return an iterator over the elements of the derived type."""
        if isinstance(self.elements, Set):
            yield from self.elements
        else:
            yield self.elements

    def __len__(self) -> int:
        """Return the number of elements in the derived type."""
        if isinstance(self.elements, Set):
            return len(self.elements)
        return 1


@dataclass
class TSUnionType(DerivedType):
    """Represents a TypeScript union type.

    Example:
    string | number
    string | number | boolean
    """

    def __str__(self) -> str:
        """Return a string representation of the union type for use in the generated code."""
        strs = []
        for t in self:
            if isinstance(t, TSInterface):
                strs.append(t.name)
            else:
                strs.append(str(t))

        return " | ".join(strs)


@dataclass
class TSArrayType(DerivedType):
    """Represents a TypeScript array type.

    Example:
    Array<string>
    Array<number|string>
    """

    def __str__(self) -> str:
        """Return a string representation of the array type for use in the generated code."""
        if isinstance(self.elements, Set):
            raise NotImplementedError("Array of multiple types is not supported!")

        return f"Array<{_elements_to_names([self.elements])[0]}>"


@dataclass
class TSTupleType(DerivedType):
    """Represents a TypeScript tuple type.

    Example:
    [string, number, boolean]
    """

    def __str__(self) -> str:
        """Return a string representation of the tuple type for use in the generated code."""
        if isinstance(self.elements, Set):
            e_names = _elements_to_names(self.elements)
        else:
            e_names = [str(self.elements)]

        return f"[{', '.join(e_names)}]"


@dataclass
class TypescriptLiteralType(DerivedType):
    """Represents a TypeScript literal type.

    Example:
    "foo"
    """

    def __str__(self) -> str:
        """Return a string representation of the literal type for use in the generated code."""
        if isinstance(self.elements, Set):
            raise NotImplementedError("Literal of multiple types is not supported!")

        return f'"{self.elements}"'


@dataclass
class TypescriptIntersectionType(DerivedType):
    """Represents a TypeScript intersection type.

    Note:
    Not really used in the code generation process. But in theory, it could be used to
    represent the intersection of two types, similar to the union type.

    Example:
    {"foo":number} & {"bar":string}
    """

    def __str__(self) -> str:
        """Return a string representation of the intersection type for use in the generated code."""
        if isinstance(self.elements, Set):
            e_names = _elements_to_names(self.elements)
        else:
            e_names = [str(self.elements)]

        return " & ".join(e_names)


# ---------------------------------------------------------------------------- #
#                                 complex types                                #
# ---------------------------------------------------------------------------- #


class TSComplex(TypescriptType, ABC):
    """Represents a TypeScript complex type.

    This is an abstract class that is used as a base class for more complex types
    such as interfaces and enums.

    We assume the name is unique for each complex type therefore we use it as the hash.
    """

    name: str

    def __str__(self) -> str:
        """Return the name of the complex type."""
        return self.name

    def __hash__(self) -> int:
        """Return a hash value for the complex type."""
        return hash(self.name)


@dataclass
class TypescriptEnumType(TSComplex):
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

    keys: List[str]
    values: Optional[List[str | int]]

    def __str__(self) -> str:
        """Return a string representation of the enum for use in the generated code.

        This method is used to generate the full enum definition.
        """
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
class TSInterface(TSComplex):
    """Represents a TypeScript interface.

    Example:
    interface Person {
        name: string;
        age: number;
        isStudent?: boolean;
    }
    """

    name: str
    elements: Dict[str, TypescriptType | TSInterface | TypescriptEnumType]

    def __str__(self) -> str:
        """Return a string representation of the interface.

        This does not include nested interfaces or enums, you may need to add them manually.
        """
        interface_str = f"interface {self.name} {{\n"

        for key, value in self.elements.items():
            a = key
            if value.not_required:
                a += "?"
            b = _elements_to_names([value])[0]

            # add the type to the interface
            interface_str += f"\t{a}: {b};\n"

        interface_str += "}"

        return interface_str

    def full_str(self) -> str:
        """Return a string representation of the interface including nested interfaces and enums."""
        this_interface_str = str(self)

        for key, value in self.elements.items():
            if isinstance(value, TSInterface):
                this_interface_str = f"{value.full_str()}\n\n{this_interface_str}"
            elif isinstance(value, DerivedType):
                # TODO
                raise NotImplementedError("Nested enums are not yet supported")
        return this_interface_str

    def __hash__(self) -> int:
        """Return a hash value for the complex type."""
        return super().__hash__()
