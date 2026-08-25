"""Tests for generic pydantic models.

Pydantic materializes parametrized generic models as real classes (e.g.
``AlbumResource(Resource[AlbumAttributes])``) and collapses self-references to
the identity class (e.g. ``Resource[T]`` inside a generic model). The
converter must resolve both back to parametrized references.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

from py2ts import generate_ts
from py2ts.data import TSInterface

T = TypeVar("T")


class Resource(BaseModel, Generic[T]):
    id: str
    data: T


class Wrapper(BaseModel, Generic[T]):
    resource: Resource[T]


T_I = TypeVar("T_I")


class Node(BaseModel, Generic[T_I]):
    value: T_I
    next: "Node[T_I] | None" = None  # noqa: UP037 (self-reference)


def test_bare_generic_model():
    ts = generate_ts(Resource)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface Resource<T> {\n\tid: string;\n\tdata: T;\n}"


def test_materialized_generic_model():
    class AlbumAttributes(BaseModel):
        title: str

    class AlbumResource(Resource[AlbumAttributes]):
        pass

    ts = generate_ts(AlbumResource)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export type AlbumResource = Resource<AlbumAttributes>;\n"
    assert "interface AlbumAttributes" in ts.full_str()
    assert "interface Resource<T>" in ts.full_str()


def test_identity_class_collapsed():
    """Resource[T] collapses to the identity class; arguments are recovered."""
    ts = generate_ts(Wrapper)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface Wrapper<T> {\n\tresource: Resource<T>;\n}"
    assert "interface Resource<T>" in ts.full_str()


def test_recursive_generic_model():
    """Recursive references terminate and resolve to the definition."""

    class StringNode(Node[str]):
        pass

    ts = generate_ts(StringNode)
    assert isinstance(ts, TSInterface)
    assert "export type StringNode = Node<string>;\n" in ts.full_str()
    assert "export interface Node<T_I>" in ts.full_str()


def test_bounded_generic_model():
    """A bounded type parameter renders with its bound and definition."""

    class Content(BaseModel):
        text: str

    C = TypeVar("C", bound=Content)

    class Response(BaseModel, Generic[C]):
        content: C

    ts = generate_ts(Response)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface Response<C extends Content> {\n\tcontent: C;\n}"
    assert "export interface Content" in ts.full_str()

    # Materialized instantiations keep the type arguments
    class JsonResponse(Response[Content]):
        pass

    ts = generate_ts(JsonResponse)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export type JsonResponse = Response<Content>;\n"
