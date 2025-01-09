import enum
from collections.abc import Sequence as ABCSequence
from dataclasses import is_dataclass
from types import UnionType
from typing import (
    List,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

from typing_extensions import NotRequired

from .data import (
    TSArrayType,
    TSEnumType,
    TSInterface,
    TSPrimitiveType,
    TSTupleType,
    TSUnionType,
    TypescriptPrimitive,
    TypescriptType,
)


def generate_ts(py_type: Type | UnionType) -> TypescriptType:
    """
    Convert a Python type to a TypeScript type.

    This function is the main entry point for converting Python types to TypeScript types.
    It will recursively convert the type and its arguments to TypeScript types.

    Parameters
    ----------
    py_type : Type | UnionType
        The Python type to convert to a TypeScript type.

    Returns
    -------
    TypescriptType
        The TypeScript type that corresponds to the provided Python type.
    """
    is_enum = False
    try:
        is_enum = issubclass(py_type, enum.Enum)  # type: ignore
    except:
        pass

    if is_dataclass(py_type) or is_typeddict(py_type):
        return _dictlike_to_ts(cast(Type, py_type))
    elif is_enum:
        return _enum_to_ts(cast(Type, py_type))
    else:
        return _basic_to_ts(py_type)


def _dictlike_to_ts(py_type: Type):
    hints = get_type_hints(py_type, include_extras=True)
    if hasattr(py_type, "__name__"):
        name = py_type.__name__  # type: ignore
    else:
        name = "Anonymous"
    elements = {}
    for n, v in hints.items():
        elements[n] = generate_ts(v)
    return TSInterface(name, elements)


def _enum_to_ts(py_type: Type[enum.Enum]):
    name = py_type.__name__

    elements = {}
    for e in py_type:
        elements[e.name] = e.value

    return TSEnumType(name, elements)


def _basic_to_ts(py_type: Type | UnionType) -> TypescriptType:
    """Convert a basic Python type to a TypeScript type.

    This shouldn't be called directly. And is a helper function for convert_to_ts.
    It processes the basic types that do not need to be inspected further.

    See convert_to_ts for more information.
    """
    origin = get_origin(py_type)

    # Not Required
    if origin is NotRequired:
        arg = get_args(py_type)[0]  # Only has one argument
        type = generate_ts(arg)
        type.not_required = True
        return type

    # Union Type
    if origin is Union or origin is UnionType:
        args = get_args(py_type)
        return TSUnionType({generate_ts(arg) for arg in args})

    # List/Sequence
    elif origin in [List, ABCSequence, list, Sequence]:
        arg = get_args(py_type)[0]  # Only has one argument
        return TSArrayType(generate_ts(arg))

    # Tuple
    elif origin in [tuple, Tuple]:
        args = get_args(py_type)
        return TSTupleType({generate_ts(arg) for arg in args})

    primitive = TypescriptPrimitive.from_python_type(py_type)
    if primitive:
        return TSPrimitiveType(primitive)
    else:
        raise NotImplementedError(
            f"Conversion of type {py_type} is not yet implemented"
        )
