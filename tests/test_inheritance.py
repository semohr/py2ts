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
