"""Data structures used in the code generation process.

This module defines the data structures used to represent TypeScript types and
interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from types import UnionType
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set

from .config import CONFIG


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
    UINT8ARRAY = "Uint8Array"
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
        """
        TYPE_MAP: dict = {
            str: TypescriptPrimitive.STRING,
            int: TypescriptPrimitive.NUMBER,
            float: TypescriptPrimitive.NUMBER,
            bool: TypescriptPrimitive.BOOLEAN,
            bytes: TypescriptPrimitive.UINT8ARRAY,
            Any: TypescriptPrimitive.ANY,
        }

        if CONFIG.none_as_null:
            TYPE_MAP[type(None)] = TypescriptPrimitive.NULL
        else:
            TYPE_MAP[type(None)] = TypescriptPrimitive.UNDEFINED

        return TYPE_MAP.get(py_type)


# ---------------------------------------------------------------------------- #
#                                  Primitive types                             #
# ---------------------------------------------------------------------------- #


def _elements_to_names(
    elements: Sequence[TypescriptType] | Set[TypescriptType] | Sequence[str] | Set[str],
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


@dataclass
class TSLiteralType(TypescriptType):
    """Represents a TypeScript literal type.

    Example:
    "foo"
    """

    value: Any

    def __str__(self) -> str:
        """Return a string representation of the literal type for use in the generated code."""
        return f'"{self.value}"'

    def __hash__(self) -> int:
        """Return a hash value for the literal type."""
        return hash(self.value)


# ---------------------------------------------------------------------------- #
#                                 Derived Types                                #
# ---------------------------------------------------------------------------- #


@dataclass
class DerivedType(TypescriptType, ABC):
    """Represents a TypeScript derived type.

    This is an abstract class that is used as a base class for more complex types
    such as arrays, tuples, unions and dicts.
    """

    elements: Set[TypescriptType] | TypescriptType | Sequence[TypescriptType]

    def __hash__(self) -> int:
        """Return a hash value for the derived type."""
        if isinstance(self.elements, Set) or isinstance(self.elements, Sequence):
            return hash(frozenset(self.elements))
        else:
            return hash(self.elements)

    def __iter__(self) -> Iterator[TypescriptType]:
        """Return an iterator over the elements of the derived type."""
        if isinstance(self.elements, Set):
            yield from self.elements
        elif isinstance(self.elements, Sequence):
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

    def __hash__(self) -> int:
        """Return a hash value for the union type."""
        return super().__hash__()


@dataclass
class TSArrayType(DerivedType):
    """Represents a TypeScript array type.

    Example:
    Array<string>
    Array<number|string>
    """

    def __str__(self) -> str:
        """Return a string representation of the array type for use in the generated code."""
        if isinstance(self.elements, Set) or isinstance(self.elements, Sequence):
            raise NotImplementedError("Array of multiple types is not supported!")

        return f"Array<{_elements_to_names([self.elements])[0]}>"

    def __hash__(self) -> int:
        """Return a hash value for the array type."""
        return super().__hash__()


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

    def __hash__(self) -> int:
        """Return a hash value for the array type."""
        return super().__hash__()


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
        if isinstance(self.elements, Set) or isinstance(self.elements, Sequence):
            e_names = _elements_to_names(self.elements)
        else:
            e_names = [str(self.elements)]

        return " & ".join(e_names)

    def __hash__(self) -> int:
        """Return a hash value for the array type."""
        return super().__hash__()


@dataclass
class TSRecordType(DerivedType):
    """Represents a TypeScript record type.

    Example:
    Record<string, number>
    """

    # elements = [key, value]

    def __init__(self, key: TypescriptType, value: TypescriptType) -> None:
        super().__init__(elements=[key, value])

    def __str__(self) -> str:
        """Return a string representation of the record type for use in the generated code."""
        if isinstance(self.elements, Set) or isinstance(self.elements, Sequence):
            e_names = _elements_to_names(self.elements)
        else:
            e_names = [str(self.elements)]

        return f"Record<{', '.join(e_names)}>"

    def __hash__(self) -> int:
        """Return a hash value for the array type."""
        return super().__hash__()


# ---------------------------------------------------------------------------- #
#                                 complex types                                #
# ---------------------------------------------------------------------------- #


@dataclass
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
class TSEnumType(TSComplex):
    """Represents a TypeScript enum type."""

    elements: Dict[str, str | int]

    def __str__(self) -> str:
        """Return a string representation of the enum for use in the generated code.

        This method is used to generate the full enum definition.
        """
        prefix = "export " if CONFIG.export_interfaces else ""
        enum_str = f"{prefix}enum {self.name} {{\n"

        for key, value in self.elements.items():
            if isinstance(value, str):
                enum_str += f"\t{key} = '{value}',\n"
            elif isinstance(value, int):
                enum_str += f"\t{key} = {value},\n"
            else:
                raise ValueError(f"Invalid value for enum: {value}")
        enum_str += "}"

        return enum_str

    def __hash__(self) -> int:
        """Return a hash value for the array type."""
        return super().__hash__()


@dataclass
class TSInterfaceRef(TSComplex):
    """Represents a TypeScript interface reference."""

    def __str__(self) -> str:
        """Return a string representation of the interface reference."""
        return self.name

    def __hash__(self) -> int:
        """Return a hash value for the complex type."""
        return super().__hash__()


@dataclass
class TSInterface(TSComplex):
    """Represents a TypeScript interface."""

    name: str

    # If string the element is a nested interface reference (if recursive)
    elements: Dict[str, TypescriptType | TSInterface | TSEnumType]

    def __str__(self) -> str:
        """Return a string representation of the interface.

        This does not include nested interfaces or enums, you may need to add them manually.
        """
        prefix = "export " if CONFIG.export_interfaces else ""

        interface_str = f"{prefix}interface {self.name} {{\n"

        for key, value in self.elements.items():
            a = key

            if not isinstance(value, str) and value.not_required:
                a += "?"
            b = _elements_to_names([value])[0]

            # add the type to the interface
            interface_str += f"\t{a}: {b};\n"

        interface_str += "}"

        return interface_str

    def full_str(self) -> str:
        """Return a string representation of the interface including nested interfaces and enums."""
        this_interface_str = str(self)

        this_interface_str += _elements_to_full_str(self.elements.values())

        return this_interface_str

    def __hash__(self) -> int:
        """Return a hash value for the array type."""
        return super().__hash__()


def _elements_to_full_str(elements: Iterable[TypescriptType]) -> str:
    """Return a string representation of the interface including nested interfaces and enums."""
    visited = set()
    full_str = ""

    def parse_elements(element: TypescriptType):
        """Recursively get all elements and add them to the string."""
        nonlocal full_str
        nonlocal visited

        # Early exit if already visited
        if element in visited:
            return

        if isinstance(element, TSInterface):
            full_str = f"{element}\n\n{full_str}"
            visited.add(element)

            for key, value in element.elements.items():
                parse_elements(value)

        elif isinstance(element, TSEnumType):
            full_str = f"{element}\n\n{full_str}"
            visited.add(element)

        elif isinstance(element, DerivedType):
            elements = list(element.__iter__())
            for ele in elements:
                if element in visited:
                    continue

                parse_elements(ele)
                visited.add(ele)
        else:
            visited.add(element)

    for element in elements:
        parse_elements(element)

    return full_str
