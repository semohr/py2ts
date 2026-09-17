"""Tests for generic types (TypeVars) in type conversion.

Generic classes emit TypeScript generics: type parameters are resolved
(``interface Resource<A = unknown, T extends string = string>``) and
instantiations keep their type arguments (``export type AlbumResource =
Resource<string, string>``).
"""

from typing import Generic, TypeVar

from py2ts import generate_ts
from py2ts.data import TSInterface


def test_basic_generic():
    T = TypeVar("T")

    class Box(Generic[T]):
        content: T

    ts = generate_ts(Box)
    assert str(ts) == "export interface Box<T = unknown> {\n\tcontent: T;\n}"


def test_bound_generic():
    A = TypeVar("A")
    T = TypeVar("T", bound=str)

    class Resource(Generic[A, T]):
        type: T
        attributes: A

    ts_resource = generate_ts(Resource)

    assert (
        str(ts_resource)
        == "export interface Resource<A = unknown, T extends string = string> {\n"
        "\ttype: T;\n\tattributes: A;\n}"
    )


def test_nested_generic():
    T = TypeVar("T")

    class Content(Generic[T]):
        data: str
        other: T

    C = TypeVar("C", bound=Content)

    class Box(Generic[C]):
        content: C

    ts = generate_ts(Box)
    assert isinstance(ts, TSInterface)
    assert "export interface Content<T = unknown>" in ts.full_str()
    assert "export interface Box<C extends Content = Content>" in ts.full_str()


def test_bare_generic_reference_uses_defaults():
    """Referencing a generic class bare relies on its type parameter defaults."""
    T = TypeVar("T")

    class Content(Generic[T]):
        other: T

    class Reader:
        content: Content  # first reference, definition not cached yet
        cached: Content[str]

    ts = generate_ts(Reader)
    assert isinstance(ts, TSInterface)
    assert str(ts) == (
        "export interface Reader {\n\tcontent: Content;\n\tcached: Content<string>;\n}"
    )
    assert "export interface Content<T = unknown>" in ts.full_str()


def test_bound_to_generic_out_of_scope_uses_default():
    """A bound to a generic class keeps the bound without fallback arguments."""
    T = TypeVar("T", bound=str)

    class Content(Generic[T]):
        other: T

    C = TypeVar("C", bound=Content)

    class Box(Generic[C]):
        content: C

    class Holder:
        box: Box

    ts = generate_ts(Holder)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface Holder {\n\tbox: Box;\n}"
    full = ts.full_str()
    assert "export interface Content<T extends string = string>" in full
    assert "export interface Box<C extends Content = Content>" in full


def test_bound_to_sibling_parameter_uses_default():
    """A constraint referencing another parameter stays valid out of scope."""
    K = TypeVar("K")
    V = TypeVar("V", bound=K)

    class Pair(Generic[K, V]):
        key: K
        value: V

    class Holder:
        first: Pair[str, str]
        second: Pair

    ts = generate_ts(Holder)
    assert isinstance(ts, TSInterface)
    assert str(ts) == (
        "export interface Holder {\n\tfirst: Pair<string, string>;\n\tsecond: Pair;\n}"
    )
    assert "export interface Pair<K = unknown, V extends K = K>" in ts.full_str()


def test_typevar_scope_matches_by_name():
    """A same-named TypeVar maps to the class parameter.

    On some Python 3.12 versions ``get_type_hints`` resolves PEP 695
    annotation strings to same-named module-level TypeVars; the annotation
    must still resolve to the type parameter of the class being converted.
    """
    T_param = TypeVar("T")
    T_other = TypeVar("T")  # same name, different object

    class Box(Generic[T_param]):
        content: T_other

    ts = generate_ts(Box)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface Box<T = unknown> {\n\tcontent: T;\n}"


def test_unresolved_typevar_falls_back_to_any():
    """A TypeVar that is not a type parameter of the class maps to unknown."""
    T = TypeVar("T")

    class NotGeneric:
        value: T

    ts = generate_ts(NotGeneric)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface NotGeneric {\n\tvalue: unknown;\n}"
