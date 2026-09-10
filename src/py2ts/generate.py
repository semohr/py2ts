from __future__ import annotations

import ast
import enum
import importlib.util
import inspect
import logging
import sys
from abc import ABC
from collections.abc import Sequence
from dataclasses import is_dataclass
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

from typing_extensions import NotRequired

from .config import CONFIG
from .data import (
    TSArrayType,
    TSComplex,
    TSEnumType,
    TSInterface,
    TSInterfaceRef,
    TSLiteralType,
    TSPrimitiveType,
    TSRecordType,
    TSTupleType,
    TSTypeParameterRef,
    TSUnionType,
    TypescriptPrimitive,
    TypescriptType,
)

if TYPE_CHECKING:
    from py2ts.config import MinimalConfig

log = logging.getLogger("py2ts")


def generate_ts(
    py_type: type | UnionType, config: MinimalConfig | None = None
) -> TypescriptType:
    """
    Convert a Python type to a TypeScript type.

    This function is the main entry point for converting Python types to
    TypeScript types.
    It will recursively convert the type and its arguments to TypeScript types.
    The returned
    TypeScript type will be a tree of TypeScript types that represent the provided
    Python type.

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
        CONFIG.reset()
        CONFIG.override(config)

    # Reset recursion tracking
    global interfaces
    interfaces.clear()

    return _generate_ts(py_type)


# Maps a converted class to its TSInterface. Used to prevent infinite
# recursion when generating recursive types and to resolve recursive
# references to the same (generic) definition.
interfaces: dict[type, TSInterface] = {}


def _generate_ts(
    py_type: type | UnionType, context: frozenset[str] = frozenset()
) -> TypescriptType:
    """Help function to generate_ts.

    ``context`` holds the names of the type parameters in scope (i.e. the
    type parameters of the generic class currently being converted). TypeVars
    matching a name in the context are converted to references to the type
    parameter (``T``) instead of falling back to ``Any``.

    This does not reset visited nodes which resolve
    the recursion. There might be a better way to solve
    this than recursion but it works for now.
    """
    global interfaces

    # Pydantic materializes parametrized generic models as real classes
    # (e.g. ResourceIdentifier[T_I]). Convert them to a reference to their
    # origin class carrying the type arguments (e.g. ResourceIdentifier<T_I>).
    pydantic_metadata = getattr(py_type, "__pydantic_generic_metadata__", None)
    if pydantic_metadata is not None and pydantic_metadata["origin"] is not None:
        origin = pydantic_metadata["origin"]
        args = pydantic_metadata.get("args") or ()
        if args:
            target = interfaces.get(origin)
            if target is None:
                converted = _generate_ts(origin, context)
                if isinstance(converted, TSInterfaceRef):
                    # The origin resolved to a self-instantiation (its type
                    # parameters happen to be in scope). The materialized
                    # class carries the real type arguments in ``args``, so
                    # reuse only the definition and rebuild the reference
                    # from ``args`` below.
                    assert converted.definition is not None
                    target = converted.definition
                else:
                    assert isinstance(converted, TSInterface)
                    target = converted
            return TSInterfaceRef(
                target.name,
                type_args=tuple(_generate_ts(a, context) for a in args),
                definition=target,
            )
        py_type = origin

    # Pydantic collapses instantiations with the model's own type parameters
    # to the identity class (e.g. ResourceIdentifier[T_I] == ResourceIdentifier
    # in pydantic >= 2.12), losing the arguments. Recover them when all
    # parameters are type parameters of the enclosing generic class.
    if pydantic_metadata is not None and pydantic_metadata["origin"] is None:
        params = pydantic_metadata.get("parameters") or ()
        param_names = tuple(getattr(p, "__name__", str(p)) for p in params)
        if param_names and all(n in context for n in param_names):
            definition = interfaces.get(cast("type", py_type))
            if definition is None:
                definition = _classlike_to_ts(cast("type", py_type))
            return TSInterfaceRef(
                definition.name,
                type_args=tuple(TSTypeParameterRef(n) for n in param_names),
                definition=definition,
            )

    is_enum = False
    try:
        is_enum = issubclass(py_type, enum.Enum)  # type: ignore
    except Exception:
        pass

    if is_dataclass(py_type) or is_typeddict(py_type):
        if py_type in interfaces:
            return _interface_ref(cast("type", py_type))
        return _classlike_to_ts(cast("type", py_type))
    elif is_enum:
        return _enum_to_ts(cast("type", py_type))
    elif _is_dict(py_type):
        return _dict_to_ts(cast("type[dict]", py_type), context)
    else:
        return _basic_to_ts(py_type, context)


def _dict_to_ts(py_type: type[dict], context: frozenset[str] = frozenset()):
    args = list(get_args(py_type))
    if len(args) != 2:
        # Bare dict has no type arguments
        while len(args) < 2:
            args.append(Any)

    key_type, value_type = args

    return TSRecordType(
        _generate_ts(key_type, context), _generate_ts(value_type, context)
    )


def _type_parameters(py_type: type) -> tuple[tuple[str, type | None], ...]:
    """Type parameters of a generic class as ``(name, bound)`` pairs.

    Uses the pydantic generic metadata if available (it keeps the original
    TypeVars), otherwise the typing ``__parameters__``. The bound is ``None``
    for unbounded parameters.
    """
    metadata = getattr(py_type, "__pydantic_generic_metadata__", None)
    if metadata is not None and metadata.get("parameters"):
        params = metadata["parameters"]
    else:
        params = getattr(py_type, "__parameters__", ()) or ()
    return tuple(
        (getattr(p, "__name__", str(p)), getattr(p, "__bound__", None)) for p in params
    )


def _interface_ref(py_type: type) -> TSInterfaceRef:
    """Build a reference to an already converted interface.

    Carries the type parameters of the generic definition as type arguments
    (e.g. ``Node<T>``) and points back at the definition.
    """
    ts = interfaces[py_type]
    return TSInterfaceRef(
        ts.name,
        type_args=tuple(TSTypeParameterRef(p) for p in ts.type_params),
        definition=ts,
    )


def _generic_args(py_type: type, base: type) -> tuple | None:
    """Type arguments used to instantiate ``base`` in ``py_type``, if any.

    Returns ``None`` if the base is not parametrized. Handles plain typing
    aliases (``Resource[str, str]`` in ``__orig_bases__``) as well as pydantic
    materialized classes (which carry their arguments in
    ``__pydantic_generic_metadata__``).

    Pydantic materializes a base parametrized with the subclass's own type
    parameters (e.g. ``Resource[A, T]`` inside ``RelResource[A, T, T_I]``) as
    the identity class, losing the arguments. In that case the arguments are
    the subclass's leading parameters.
    """
    metadata = getattr(base, "__pydantic_generic_metadata__", None)
    if metadata is not None and metadata.get("args"):
        return tuple(metadata["args"])

    for orig in getattr(py_type, "__orig_bases__", ()):
        if get_origin(orig) is base:
            args = get_args(orig)
            return tuple(args) if args else None

    if metadata is not None and metadata.get("parameters"):
        base_params = metadata["parameters"]
        sub_params = getattr(py_type, "__parameters__", ()) or ()
        base_names = tuple(getattr(p, "__name__", str(p)) for p in base_params)
        sub_names = tuple(getattr(p, "__name__", str(p)) for p in sub_params)
        if base_names and len(sub_params) >= len(base_params):
            if sub_names[: len(base_params)] == base_names:
                return tuple(sub_params[: len(base_params)])
    return None


def _classlike_to_ts(py_type: type) -> TSInterface:
    hints = _get_type_hints_no_inheritance(py_type)
    if hasattr(py_type, "__name__"):
        name = py_type.__name__  # type: ignore
    else:
        name = "Anonymous"

    params = _type_parameters(py_type)
    type_params = tuple(name for name, _ in params)
    context = frozenset(type_params)
    bounds = {
        name: _generate_ts(bound, context)
        for name, bound in params
        if bound is not None
    }

    elements: dict[str, TypescriptType] = {}
    ts = TSInterface(name, elements, None, type_params, bounds)
    # Register the interface before converting the fields so that recursive
    # references (e.g. Node[T]) resolve to this definition.
    interfaces[py_type] = ts

    for n, v in hints.items():
        elements[n] = _generate_ts(v, context)

    # Check inheritance
    bases = set(inspect.getmro(py_type))
    bases.discard(py_type)  # need to remove the class itself
    bases.discard(object)  # need to remove the object class
    bases.discard(dict)  # need to remove the dict class
    bases.discard(ABC)  # need to remove the abstract base class

    valid_bases = []

    def _is_empty(i: TSInterface | TSInterfaceRef) -> bool:
        """Whether a base is an empty marker interface to be skipped.

        Handles both the interface itself and the definition behind a
        reference (the recursion cache returns references). An empty
        interface with an inheritance is a type alias, not a marker.
        """
        if isinstance(i, TSInterface):
            return len(i.elements) == 0 and i.inheritance is None
        definition = i.definition
        return (
            isinstance(definition, TSInterface)
            and len(definition.elements) == 0
            and definition.inheritance is None
        )

    for base in bases:
        i = _generate_ts(base, context)
        assert isinstance(i, (TSInterface, TSInterfaceRef)), (
            "Base class is not an interface but a primitive type."
        )
        if _is_empty(i):
            # Skip empty interfaces (e.g. Generic, typing.TypedDict markers)
            continue
        valid_bases.append((base, i))

    # Remove bases that are already inherited transitively through a more
    # derived base (e.g. a generic base class and the class it inherits from)
    valid_bases = [
        (base, i)
        for base, i in valid_bases
        if not any(
            issubclass(other, base) for other, _ in valid_bases if other is not base
        )
    ]

    if len(valid_bases) == 1:
        base, i = valid_bases[0]
        ts.inheritance = _inheritance_ref(py_type, base, i, context)
    elif len(valid_bases) > 1:
        raise NotImplementedError(
            "Multiple inheritance is not supported by typescript. "
            f"Got {len(valid_bases)} instead: "
            f"{', '.join([b[1].name for b in valid_bases])}"
        )

    return ts


def _inheritance_ref(
    py_type: type, base: type, i: TSInterface | TSInterfaceRef, context: frozenset[str]
) -> TSInterfaceRef:
    """Build a reference to a base class.

    Carries type arguments if the base is parametrized.
    """
    args = _generic_args(py_type, base)
    if args is not None:
        definition = i.definition if isinstance(i, TSInterfaceRef) else i
        return TSInterfaceRef(
            i.name,
            type_args=tuple(_generate_ts(a, context) for a in args),
            definition=definition,
        )
    if isinstance(i, TSInterface):
        return TSInterfaceRef(i.name, definition=i)
    return i


def _enum_to_ts(py_type: type[enum.Enum]):
    name = py_type.__name__

    elements = {}
    for e in py_type:
        elements[e.name] = e.value

    return TSEnumType(name, elements)


def _basic_to_ts(
    py_type: type | UnionType, context: frozenset[str] = frozenset()
) -> TypescriptType:
    """Convert a basic Python type to a TypeScript type.

    This shouldn't be called directly. And is a helper function for convert_to_ts.
    It processes the basic types that do not need to be inspected further.

    See convert_to_ts for more information.
    """
    origin = get_origin(py_type)

    if origin in _wrapper_types():
        # If the type is just a wrapper type (e.g. sqlalchemy Mapped)
        return _generate_ts(get_args(py_type)[0], context)

    # Not Required
    if origin is NotRequired:
        arg = get_args(py_type)[0]  # Only has one argument
        type = _generate_ts(arg, context)
        type.not_required = True
        return type

    # Union Type
    if origin is Union or origin is UnionType:
        args = get_args(py_type)
        return TSUnionType({_generate_ts(arg, context) for arg in args})

    # List/Sequence
    elif origin in (list, Sequence):
        arg = get_args(py_type)[0]  # Only has one argument
        return TSArrayType(_generate_ts(arg, context))

    # Tuple
    elif origin is tuple:
        args = get_args(py_type)
        return TSTupleType({_generate_ts(arg, context) for arg in args})

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

    # Generic type parameters (TypeVar) resolve to the type parameter of the
    # enclosing generic class, if any. Unresolved TypeVars fall back to Any
    # (unknown by default)
    if isinstance(py_type, TypeVar):
        if py_type.__name__ in context:
            return TSTypeParameterRef(py_type.__name__)
        return _generate_ts(Any)

    # Parametrized generic class (e.g. Resource[str, str] or Node[T])
    # Note: a plain class like Generic itself has no args and must not be
    # treated as a parametrized reference.
    if inspect.isclass(origin) and get_args(py_type):
        target: TSComplex | None = interfaces.get(origin)
        if target is None:
            converted = _generate_ts(origin, context)
            if (
                isinstance(converted, TSInterfaceRef)
                and converted.definition is not None
            ):
                target = converted.definition
            elif isinstance(converted, TSInterface):
                target = converted
            else:
                raise NotImplementedError(
                    f"Conversion of type {py_type} is not yet implemented"
                )
        if isinstance(target, TSInterface):
            return TSInterfaceRef(
                target.name,
                type_args=tuple(_generate_ts(a, context) for a in get_args(py_type)),
                definition=target,
            )
        raise NotImplementedError(
            f"Conversion of type {py_type} is not yet implemented"
        )

    # Generic classes
    if inspect.isclass(py_type):
        if py_type in interfaces:
            return _interface_ref(py_type)
        log.info(
            "Generic classes might not be converted correctly. Please use "
            "dataclasses or TypedDicts instead!"
        )
        return _classlike_to_ts(py_type)

    else:
        raise NotImplementedError(
            f"Conversion of type {py_type} is not yet implemented"
        )


def _wrapper_types() -> list[Any]:
    # Unpack nested types (e.g. sqlalchemy Mapping, typing.Annotated)
    types: list[Any] = [Annotated]
    if importlib.util.find_spec("sqlalchemy") is not None:
        from sqlalchemy.orm import Mapped

        types.append(Mapped)

    return types


def _is_dict(py_type: type | UnionType) -> bool:
    origin = get_origin(py_type)
    if origin is dict or py_type is dict or origin is dict:
        return True
    return False


def _is_type_checking(node: ast.expr) -> bool:
    """Whether an ``if`` condition checks ``TYPE_CHECKING``."""
    if isinstance(node, ast.Name):
        return node.id == "TYPE_CHECKING"
    return isinstance(node, ast.Attribute) and node.attr == "TYPE_CHECKING"


def _type_checking_locals(cls: type) -> dict[str, Any]:
    """Evaluate top-level TYPE_CHECKING blocks from the class MRO's modules.

    Only plain ``if TYPE_CHECKING:`` or ``if typing.TYPE_CHECKING:`` tests are
    evaluated. Their code may have arbitrary side effects, including importing
    modules and defining names. Evaluation is best effort: failures are logged
    and ignored.
    """
    namespace: dict[str, Any] = {}
    module_names = dict.fromkeys(base.__module__ for base in cls.__mro__)
    for module_name in module_names:
        module = sys.modules.get(module_name)
        if module is None:
            continue
        try:
            source = inspect.getsource(module)
            # Cheap pre-filter: a module without the pattern cannot contain
            # a TYPE_CHECKING block, so skip parsing it.
            if "TYPE_CHECKING" not in source:
                continue
            tree = ast.parse(
                source,
                filename=getattr(module, "__file__", None) or module_name,
            )
        except (OSError, TypeError, SyntaxError):
            # Built-in, interactively defined, generated, or invalid source.
            continue
        for node in tree.body:
            if not (isinstance(node, ast.If) and _is_type_checking(node.test)):
                continue
            code = compile(
                ast.Module(body=node.body, type_ignores=[]),
                filename=getattr(module, "__file__", None) or "<type_checking>",
                mode="exec",
            )
            try:
                exec(code, module.__dict__, namespace)
            except Exception as exc:
                log.debug(
                    "Could not evaluate TYPE_CHECKING block in %s: %s",
                    module_name,
                    exc,
                    exc_info=True,
                )
    return namespace


def _get_type_hints_no_inheritance(cls: type) -> dict[str, Any]:
    """Get type hints for a class excluding inherited annotations.

    Excludes annotations inherited from parent classes.
    """
    try:
        # Get type hints for the current class (including inherited ones)
        all_hints = get_type_hints(cls, include_extras=True)
    except NameError:
        # Retry with names that are only imported for type checkers, e.g.
        # inside `if TYPE_CHECKING:` blocks.
        all_hints = get_type_hints(
            cls, include_extras=True, localns=_type_checking_locals(cls)
        )

    # Get annotations defined directly in this class (not inherited)
    cls_annotations = inspect.get_annotations(cls) or {}

    # Filter to keep only annotations defined in this class
    return {k: v for k, v in all_hints.items() if k in cls_annotations}
