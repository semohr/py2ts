import pytest
from py2ts import generate_ts
from py2ts.data import TSInterface


def test_simple_inheritance():
    class Bar:
        bar: str

    class Foo(Bar):
        foo: str

    ts = generate_ts(Foo)
    print(ts)
    assert isinstance(ts, TSInterface)
    assert ts.inheritance is not None

    assert str(ts) == "export interface Foo extends Bar {\n\tfoo: string;\n}"


def test_multiple_inheritance():
    class Bar:
        bar: str

    class Baz:
        baz: str

    class Foo(Bar, Baz):
        foo: str

    with pytest.raises(NotImplementedError):
        generate_ts(Foo)


def test_dataclass_inheritance():
    from dataclasses import dataclass

    @dataclass
    class Bar:
        bar: str

    @dataclass
    class Foo(Bar):
        foo: str

    ts = generate_ts(Foo)
    print(ts)
    assert isinstance(ts, TSInterface)
    assert ts.inheritance is not None

    assert str(ts) == "export interface Foo extends Bar {\n\tfoo: string;\n}"


def test_typeddict_inheritance():
    from typing import TypedDict

    class Bar(TypedDict):
        bar: str

    class Foo(Bar):
        foo: str

    ts = generate_ts(Foo)
    print(ts)
    assert isinstance(ts, TSInterface)
    # Inheritance is not supported for TypedDicts
    assert ts.inheritance is None
    assert str(ts) == "export interface Foo {\n\tbar: string;\n\tfoo: string;\n}"


def test_full_str():
    from dataclasses import dataclass

    @dataclass
    class Bar:
        bar: str

    @dataclass
    class Foo(Bar):
        foo: str

    ts = generate_ts(Foo)
    assert isinstance(ts, TSInterface)
    assert "interface Bar" in ts.full_str()
    assert "interface Foo" in ts.full_str()


def test_inheritance_empty():
    from dataclasses import dataclass

    @dataclass
    class Bar:
        bar: str

    @dataclass
    class Foo(Bar):
        pass

    ts = generate_ts(Foo)
    print(ts)
    assert isinstance(ts, TSInterface)
    assert ts.inheritance is not None
    assert str(ts) == "export type Foo = Bar;\n"


def test_inheritance_cached_base():
    """A base referenced by a field first resolves through the recursion cache."""
    from dataclasses import dataclass

    @dataclass
    class Bar:
        bar: str

    @dataclass
    class Foo(Bar):
        other: Bar

    ts = generate_ts(Foo)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export interface Foo extends Bar {\n\tother: Bar;\n}"


def test_generic_inheritance():
    """A subclass of a parametrized generic carries the type arguments."""
    from typing import Generic, TypeVar

    T = TypeVar("T")
    S = TypeVar("S")

    class Resource(Generic[T, S]):
        type: S
        attributes: T

    class AlbumResource(Resource[str, str]):
        pass

    ts = generate_ts(AlbumResource)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export type AlbumResource = Resource<string, string>;\n"

    # The same result when the generic definition was converted before the
    # subclass (the recursion cache returns a reference to the definition).
    class AlbumResource2(Resource[str, str]):
        pass

    ts = generate_ts(AlbumResource2)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export type AlbumResource2 = Resource<string, string>;\n"


def test_transitive_generic_base_removed():
    """Only the most derived base is emitted, not its generic base too."""
    from typing import Generic, TypeVar

    T = TypeVar("T")

    class Resource(Generic[T]):
        type: T

    class Base(Resource[str]):
        pass

    class Derived(Base):
        pass

    ts = generate_ts(Derived)
    assert isinstance(ts, TSInterface)
    assert str(ts) == "export type Derived = Base;\n"
