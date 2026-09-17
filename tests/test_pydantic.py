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
    assert (
        str(ts)
        == "export interface Resource<T = unknown> {\n\tid: string;\n\tdata: T;\n}"
    )


def test_materialized_generic_model():
    class AlbumAttributes(BaseModel):
        title: str

    class AlbumResource(Resource[AlbumAttributes]):
        pass

    ts = generate_ts(AlbumResource)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export type AlbumResource = Resource<AlbumAttributes>;\n"
    assert "interface AlbumAttributes" in ts.full_str()
    assert "interface Resource<T = unknown>" in ts.full_str()


def test_identity_class_collapsed():
    """Resource[T] collapses to the identity class; arguments are recovered."""
    ts = generate_ts(Wrapper)
    assert isinstance(ts, TSInterface)
    assert (
        str(ts)
        == "export interface Wrapper<T = unknown> {\n\tresource: Resource<T>;\n}"
    )
    assert "interface Resource<T = unknown>" in ts.full_str()


def test_typevar_name_collision_keeps_actual_args():
    """A materialized reference keeps its actual type arguments.

    Pydantic materializes ``ResourceIdentifier[T_I]`` with args preserved.
    If the origin's own type parameter happens to share a name with a
    parameter of the enclosing generic class (``T``), the origin must not
    be treated as a self-instantiation of the enclosing class - the
    reference has to be rebuilt from the preserved args.
    """

    class Resource(BaseModel, Generic[T]):
        type: T
        id: str

    class ResourceIdentifier(BaseModel, Generic[T]):
        type: T
        id: str

    T_I = TypeVar("T_I")

    class RelResource(Resource[T], Generic[T, T_I]):
        relationships: list[ResourceIdentifier[T_I]]

    ts = generate_ts(RelResource)
    assert isinstance(ts, TSInterface)
    assert "interface ResourceIdentifier<T = unknown>" in ts.full_str()
    assert "relationships: Array<ResourceIdentifier<T_I>>;" in ts.full_str()
    assert "Array<ResourceIdentifier<T>>;" not in ts.full_str()


def test_recursive_generic_model():
    """Recursive references terminate and resolve to the definition."""

    class StringNode(Node[str]):
        pass

    ts = generate_ts(StringNode)
    assert isinstance(ts, TSInterface)
    assert "export type StringNode = Node<string>;\n" in ts.full_str()
    assert "export interface Node<T_I = unknown>" in ts.full_str()


def test_bounded_generic_model():
    """A bounded type parameter renders with its bound and definition."""

    class Content(BaseModel):
        text: str

    C = TypeVar("C", bound=Content)

    class Response(BaseModel, Generic[C]):
        content: C

    ts = generate_ts(Response)
    assert isinstance(ts, TSInterface)
    assert (
        str(ts)
        == "export interface Response<C extends Content = Content> {\n\tcontent: C;\n}"
    )
    assert "export interface Content" in ts.full_str()

    # Materialized instantiations keep the type arguments
    class JsonResponse(Response[Content]):
        pass

    ts = generate_ts(JsonResponse)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export type JsonResponse = Response<Content>;\n"


def test_typevar_bound_to_generic_model():
    """A TypeVar bound to a generic model keeps the bound's parameters generic.

    A bare generic bound (e.g. ``Resource`` for ``Resource[A, T]``) must not
    render as bare ``Resource`` (TS2314: requires type arguments) or as
    ``Resource<A, T>`` using the definition's out-of-scope type parameter
    names (TS2304). The bound is rendered as bare ``Resource`` instead;
    the type parameter defaults provide the concrete arguments.
    """
    A = TypeVar("A")
    T = TypeVar("T", bound=str)

    class Resource(BaseModel, Generic[A, T]):
        type: T
        attributes: A

    R = TypeVar("R", bound=Resource)

    class Document(BaseModel, Generic[R]):
        data: R

    ts = generate_ts(Document)
    assert isinstance(ts, TSInterface)
    assert str(ts) == (
        "export interface Document<R extends Resource = Resource> {\n\tdata: R;\n}"
    )
    assert (
        "export interface Resource<A = unknown, T extends string = string>"
        in ts.full_str()
    )

    R_I = TypeVar("R_I", bound=Resource)

    class DocumentWithIncluded(Document[R], Generic[R, R_I]):
        included: list[R_I] | None = None

    ts = generate_ts(DocumentWithIncluded)
    assert isinstance(ts, TSInterface)
    assert str(ts) == (
        "export interface DocumentWithIncluded<"
        "R extends Resource = Resource, "
        "R_I extends Resource = Resource> extends Document<R> {\n"
        "\tincluded: Array<R_I> | null;\n"
        "}"
    )


def test_reference_to_typevar_bound_model_is_complete():
    """References to a model bounded by a generic model keep the full arity.

    A bare reference (``Document``) and a materialized reference
    (``Document[ItemResource]``) must both stay valid without leaking
    the bound's out-of-scope parameters.
    """
    A = TypeVar("A")
    T = TypeVar("T", bound=str)

    class Resource(BaseModel, Generic[A, T]):
        type: T
        attributes: A

    class ItemResource(Resource[str, str]):
        id: str

    R = TypeVar("R", bound=Resource)

    class Document(BaseModel, Generic[R]):
        data: R

    class Holder(BaseModel):
        first: Document[ItemResource]
        second: Document

    ts = generate_ts(Holder)
    assert isinstance(ts, TSInterface)
    assert str(ts) == (
        "export interface Holder {\n"
        "\tfirst: Document<ItemResource>;\n"
        "\tsecond: Document;\n"
        "}"
    )
    full = ts.full_str()
    assert "export interface ItemResource extends Resource<string, string>" in full
    assert "export interface Document<R extends Resource = Resource>" in full
