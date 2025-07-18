import enum
import importlib.util
import inspect
import logging
from abc import ABC
from collections.abc import Sequence as ABCSequence
from dataclasses import is_dataclass
from types import UnionType
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
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

from py2ts.config import MinimalConfig

from .config import CONFIG
from .data import (
    TSArrayType,
    TSEnumType,
    TSInterface,
    TSInterfaceRef,
    TSLiteralType,
    TSPrimitiveType,
    TSRecordType,
    TSTupleType,
    TSUnionType,
    TypescriptPrimitive,
    TypescriptType,
)

log = logging.getLogger("py2ts")


def generate_ts(
    py_type: Type | UnionType, config: Optional[MinimalConfig] = None
) -> TypescriptType:
    """
    Convert a Python type to a TypeScript type.

    This function is the main entry point for converting Python types to TypeScript types.
    It will recursively convert the type and its arguments to TypeScript types. The returned
    TypeScript type will be a tree of TypeScript types that represent the provided Python type.

    Parameters
    ----------
    py_type : Type | UnionType
        The Python type to convert to a TypeScript type.
    config : MinimalConfig, optional
        A dictionary with configuration options. If given, will reset all defaults!

    Returns
    -------
    TypescriptType
        The TypeScript type that corresponds to the provided Python type.
    """
    # Reset config
    if config:
        CONFIG.__init__()
        CONFIG.override(config)

    # Reset recursion tracking
    global interfaces
    interfaces.clear()

    return _generate_ts(py_type)


# Used to keep track of interfaces that have already been generated
# to prevent infinite recursion in generating ts types.
interfaces = set()


def _generate_ts(py_type: Type | UnionType) -> TypescriptType:
    """Help function to generate_ts.

    This does not reset visited nodes which resolve
    the recursion. There might be a better way to solve
    this than recursion but it works for now.
    """
    global interfaces

    is_enum = False
    try:
        is_enum = issubclass(py_type, enum.Enum)  # type: ignore
    except:
        pass

    if is_dataclass(py_type) or is_typeddict(py_type):
        if py_type in interfaces:
            return TSInterfaceRef(py_type.__name__)  # type: ignore
        interfaces.add(py_type)
        ts_interface = _classlike_to_ts(cast(Type, py_type))
        return ts_interface
    elif is_enum:
        return _enum_to_ts(cast(Type, py_type))
    elif _is_dict(py_type):
        return _dict_to_ts(cast(Type[dict], py_type))
    else:
        return _basic_to_ts(py_type)


def _dict_to_ts(py_type: Type[dict]):
    args = get_args(py_type)
    if len(args) != 2:
        # Fill with any until 2 values
        args = list(args)
        while len(args) < 2:
            args.append(Any)

    key_type, value_type = args

    return TSRecordType(_generate_ts(key_type), _generate_ts(value_type))


def _classlike_to_ts(py_type: Type):
    hints = _get_type_hints_no_inheritance(py_type)
    if hasattr(py_type, "__name__"):
        name = py_type.__name__  # type: ignore
    else:
        name = "Anonymous"
    elements = {}

    for n, v in hints.items():
        elements[n] = _generate_ts(v)

    # Check inheritance
    inheritance: TSInterface | TSInterfaceRef | None = None
    bases = set(inspect.getmro(py_type))
    bases.discard(py_type)  # need to remove the class itself
    bases.discard(object)  # need to remove the object class
    bases.discard(dict)  # need to remove the tuple class
    bases.discard(ABC)  # need to remove the tuple class

    valid_bases = []

    for base in bases:
        i = _generate_ts(base)
        assert isinstance(
            i, (TSInterface, TSInterfaceRef)
        ), "Base class is not an interface but a primitive type."
        if isinstance(i, TSInterface) and len(i.elements) == 0:
            # Skip empty interfaces
            continue
        valid_bases.append(i)

    if len(valid_bases) == 1:
        inheritance = valid_bases[0]
    elif len(valid_bases) > 1:
        raise NotImplementedError(
            "Multiple inheritance is not supported by typescript. "
            f"Got {len(valid_bases)} instead: {', '.join([b.name for b in valid_bases])}"
        )

    return TSInterface(name, elements, inheritance)


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

    if origin in _wrapper_types():
        # If the type is just a wrapper type (e.g. sqlalchemy Mapped)
        return _generate_ts(get_args(py_type)[0])

    # Not Required
    if origin is NotRequired:
        arg = get_args(py_type)[0]  # Only has one argument
        type = _generate_ts(arg)
        type.not_required = True
        return type

    # Union Type
    if origin is Union or origin is UnionType:
        args = get_args(py_type)
        return TSUnionType({_generate_ts(arg) for arg in args})

    # List/Sequence
    elif origin in [List, ABCSequence, list, Sequence]:
        arg = get_args(py_type)[0]  # Only has one argument
        return TSArrayType(_generate_ts(arg))

    # Tuple
    elif origin in [tuple, Tuple]:
        args = get_args(py_type)
        return TSTupleType({_generate_ts(arg) for arg in args})

    # Literal
    elif origin is Literal:
        args = get_args(py_type)
        if len(args) == 1:
            return TSLiteralType(args[0])
        else:
            return TSUnionType({TSLiteralType(arg) for arg in args})

    # Primitive types
    primitive = TypescriptPrimitive.from_python_type(py_type)
    if primitive:
        return TSPrimitiveType(primitive)

    # Generic classes
    if inspect.isclass(py_type):
        log.info(
            "Generic classes might not be converted correctly. Please use dataclasses or TypedDicts instead!"
        )
        return _classlike_to_ts(py_type)

    else:
        raise NotImplementedError(
            f"Conversion of type {py_type} is not yet implemented"
        )


def _wrapper_types() -> List[Type]:
    # Unpack nested types (e.g. sqlalchemy Mapping)
    types: list[Type] = []
    if importlib.util.find_spec("sqlalchemy") is not None:
        from sqlalchemy.orm import Mapped

        types.append(Mapped)

    return types


def _is_dict(py_type: Type | UnionType) -> bool:
    origin = get_origin(py_type)
    if origin is dict or py_type is dict or origin is Dict:
        return True
    return False


def _get_type_hints_no_inheritance(cls: Type) -> Dict[str, Any]:
    """Get type hints for a class excluding annotations inherited from parent classes."""
    # Get type hints for the current class (including inherited ones)
    all_hints = get_type_hints(cls, include_extras=True)

    # Get annotations defined directly in this class (not inherited)
    cls_annotations = cls.__dict__.get("__annotations__", {})

    # Filter to keep only annotations defined in this class
    return {k: v for k, v in all_hints.items() if k in cls_annotations}
