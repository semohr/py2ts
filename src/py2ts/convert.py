from collections.abc import Sequence as ABCSequence
from dataclasses import is_dataclass
from types import UnionType
from typing import (
    List,
    Sequence,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    is_typeddict,
)

from .data import (
    TSArrayType,
    TSPrimitiveType,
    TSTupleType,
    TSUnionType,
    TypescriptPrimitive,
    TypescriptType,
)


def convert_to_ts(py_type: Type | UnionType) -> TypescriptType:
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
    if is_dataclass(py_type) or is_typeddict(py_type):
        raise NotImplementedError("TypedDict conversion is not yet implemented")
    else:
        return _basic_cover_to_ts(py_type)


def _basic_cover_to_ts(py_type: Type | UnionType) -> TypescriptType:
    """Convert a basic Python type to a TypeScript type.

    This shouldn't be called directly. And is a helper function for convert_to_ts.
    It processes the basic types that do not need to be inspected further.

    See convert_to_ts for more information.
    """
    origin = get_origin(py_type)

    # Union Type
    if origin is Union:
        args = get_args(py_type)
        return TSUnionType({convert_to_ts(arg) for arg in args})

    # List/Sequence
    elif origin in [List, ABCSequence, list, Sequence]:
        arg = get_args(py_type)[0]  # Only has one argument
        return TSArrayType(convert_to_ts(arg))

    # Tuple
    elif origin in [tuple, Tuple]:
        args = get_args(py_type)
        return TSTupleType({convert_to_ts(arg) for arg in args})

    primitive = TypescriptPrimitive.from_python_type(py_type)
    if primitive:
        return TSPrimitiveType(primitive)
    else:
        raise NotImplementedError(
            f"Conversion of type {py_type} is not yet implemented"
        )
