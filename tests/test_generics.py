"""Tests for generic types (TypeVars) in type conversion.

Generic classes emit TypeScript generics: type parameters are resolved
(``interface Resource<A, T extends string>``) and instantiations keep
their type arguments (``export type AlbumResource = Resource<string, string>``).
"""

from typing import Generic, TypeVar

from py2ts import generate_ts
from py2ts.data import TSInterface


def test_basic_generic():
    T = TypeVar("T")

    class Box(Generic[T]):
        content: T

    ts = generate_ts(Box)
    assert str(ts) == "export interface Box<T> {\n\tcontent: T;\n}"


def test_bound_generic():
    A = TypeVar("A")
    T = TypeVar("T", bound=str)

    class Resource(Generic[A, T]):
        type: T
        attributes: A

    ts_resource = generate_ts(Resource)

    assert (
        str(ts_resource) == "export interface Resource<A, T extends string> {\n"
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
    print(ts)
    assert isinstance(ts, TSInterface)
    assert "export interface Content<T>" in ts.full_str()
    assert "export interface Box<C extends Content>" in ts.full_str()


def test_unresolved_typevar_falls_back_to_any():
    """A TypeVar that is not a type parameter of the class maps to unknown."""
    T = TypeVar("T")

    class NotGeneric:
        value: T

    ts = generate_ts(NotGeneric)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface NotGeneric {\n\tvalue: unknown;\n}"
