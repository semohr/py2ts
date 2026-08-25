from dataclasses import dataclass
from typing import Generic, TypedDict, TypeVar

from py2ts import generate_ts
from py2ts.builder import TSBuilder

T = TypeVar("T")


@dataclass
class Node(Generic[T]):
    value: T
    next: "Node[T] | None" = None  # noqa: UP037 (self-reference)


@dataclass
class Wrapper(Generic[T]):
    node: Node[T]


def test_basic_builder():
    class StringDict(TypedDict):
        s: str
        e: int

    ts_builder = TSBuilder()
    ts_builder.add(StringDict, exclude={"e"})

    assert len(ts_builder._elements) == 1

    assert ts_builder.to_str() == "export interface StringDict {\n\ts: string;\n}\n\n"


def test_builder_nested():
    class InnerDict(TypedDict):
        s: str

    class DeepDict(TypedDict):
        deep: InnerDict | None

    ts_builder = TSBuilder()
    ts_builder.add(DeepDict)
    ts_builder.add(InnerDict)

    assert len(ts_builder._elements) == 2

    assert (
        ts_builder.to_str()
        == "export interface DeepDict {\n\tdeep: InnerDict | null;\n}\n\n"
        "export interface InnerDict {\n\ts: string;\n}\n\n"
    )


def test_builder_ts_elements():
    class InnerDict(TypedDict):
        s: str

    class DeepDict(TypedDict):
        deep: InnerDict | None

    ts_builder = TSBuilder()
    ts_builder.add(DeepDict)
    ts_builder.add(InnerDict)

    ts_elements = ts_builder.ts_elements

    assert len(ts_elements) == 2
    assert len(ts_builder._elements) == len(ts_elements)

    assert (
        ts_builder.to_str()
        == "export interface DeepDict {\n\tdeep: InnerDict | null;\n}\n\n"
        "export interface InnerDict {\n\ts: string;\n}\n\n"
    )


def test_resolve_recursive_generic_refs():
    """References resolve their generic definitions and type arguments."""
    from py2ts.builder import _resolve_recursive
    from py2ts.data import (
        TSComplex,
        TSInterface,
        TSInterfaceRef,
        TSPrimitiveType,
        TSTypeParameterRef,
        TypescriptPrimitive,
    )

    definition = TSInterface(
        "Resource",
        {"type": TSTypeParameterRef("T")},
        type_params=("T",),
    )
    attributes = TSInterface(
        "AlbumAttributes",
        {"title": TSPrimitiveType(TypescriptPrimitive.STRING)},
    )
    ref = TSInterfaceRef(
        "Resource",
        type_args=(TSInterfaceRef("AlbumAttributes", definition=attributes),),
        definition=definition,
    )

    elements: set = set()
    _resolve_recursive(ref, elements)

    # Both the references and their definitions are collected
    assert {e.name for e in elements if isinstance(e, TSComplex)} == {
        "AlbumAttributes",
        "Resource",
    }
    definitions = [e for e in elements if isinstance(e, TSInterface)]
    assert sorted(e.name for e in definitions) == ["AlbumAttributes", "Resource"]


def test_resolve_recursive_cycle_terminates():
    """Cyclic references terminate and each type is added only once."""
    from py2ts.builder import _resolve_recursive
    from py2ts.data import TSInterface, TSInterfaceRef, TSTypeParameterRef

    definition = TSInterface(
        "Node",
        {
            "value": TSTypeParameterRef("T"),
            "next": TSInterfaceRef("Node", type_args=(TSTypeParameterRef("T"),)),
        },
        type_params=("T",),
    )
    # Real cycle: the element ref points back at the same definition
    definition.elements["next"].definition = definition

    elements: set = set()
    _resolve_recursive(definition, elements)

    # definition + its own element ref + the type parameter ref
    assert len(elements) == 3


def test_builder_exclude_recursive_generic():
    """Excluding fields from a recursive generic keeps the fields out.

    Regression test: the definition attached to the recursive reference must
    not leak the excluded fields back into the output.
    """
    builder = TSBuilder()
    builder.add(Node, exclude={"value"})
    out = builder.to_str()

    assert "value:" not in out
    assert "next:" in out
    assert out.count("interface Node<T>") == 1

    # The same must hold when the generic definition is also referenced
    # from another added type.
    builder = TSBuilder()
    builder.add(Node, exclude={"value"}).add(Wrapper)
    out = builder.to_str()
    assert "value:" not in out
    assert out.count("interface Node<T>") == 1


def test_exclude_recursive_generic_full_str():
    """full_str of an excluded recursive generic does not leak fields."""
    excluded = generate_ts(Node).exclude({"value"})
    full = excluded.full_str()
    assert "value:" not in full
    assert full.count("interface Node<T>") == 1
