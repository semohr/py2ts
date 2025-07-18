from __future__ import annotations
from typing import TypedDict
from typing_extensions import NotRequired

from py2ts.data import TSComplex, TSInterface
from py2ts.generate import generate_ts


class StringDict(TypedDict):
    s: str
    i: int
    f: float
    b: bool
    n: None


def test_base_types():
    ts = generate_ts(StringDict)

    assert "interface StringDict" in str(ts)
    assert "s: string" in str(ts)
    assert "i: number" in str(ts)
    assert "f: number" in str(ts)
    assert "b: boolean" in str(ts)
    assert "n: null" in str(ts)


def test_exclude():
    ts = generate_ts(StringDict)

    assert isinstance(ts, TSComplex)
    ts = ts.exclude({"s", "i"})

    assert "interface StringDict" in str(ts)
    assert "s: string" not in str(ts)
    assert "i: number" not in str(ts)


class NotRequiredDict(TypedDict):
    s: NotRequired[str]
    i: NotRequired[int]
    f: NotRequired[float]
    b: NotRequired[bool]
    n: NotRequired[None]


def test_not_required():
    ts = generate_ts(NotRequiredDict)

    assert "interface NotRequiredDict" in str(ts)
    assert "s?: string" in str(ts)
    assert "i?: number" in str(ts)
    assert "f?: number" in str(ts)
    assert "b?: boolean" in str(ts)
    assert "n?: null" in str(ts)


class InnerDict(TypedDict):
    s: str


class DeepDict(TypedDict):
    deep: InnerDict | None


class OuterDict(TypedDict):
    nested: InnerDict
    deep: DeepDict | None


def test_nested():
    ts = generate_ts(OuterDict)
    print(ts, flush=True)

    # Converting the outer dict to str should only return the
    # outer dict!
    assert "interface OuterDict" in str(ts)
    assert "nested: InnerDict" in str(ts)
    assert "deep: DeepDict | null" in str(ts) or "deep: null | DeepDict" in str(ts)

    # The full str should contain all the types needed
    # to represent the nested structure
    assert isinstance(ts, TSInterface)
    full_ts = ts.full_str()
    print(full_ts, flush=True)
    assert "interface OuterDict" in full_ts
    assert "interface InnerDict" in full_ts
    assert "interface DeepDict" in full_ts


class RecursiveDict(TypedDict):
    s: str
    r: RecursiveDict


def test_recursive():
    ts = generate_ts(RecursiveDict)
    print(ts, flush=True)

    assert "interface RecursiveDict" in str(ts)
    assert "r: RecursiveDict" in str(ts)
    assert "s: string" in str(ts)

    assert isinstance(ts, TSInterface)
    full_ts = ts.full_str()
    print(full_ts, flush=True)
    assert "interface RecursiveDict" in full_ts
    assert "r: RecursiveDict" in full_ts
    assert "s: string" in full_ts
    # should only have 4 lines
    assert len(full_ts.split("\n")) == 4


class DeeperRecursiveDict(TypedDict):
    s: str
    r: DeepRecursiveDict


class DeepRecursiveDict(TypedDict):
    s: str
    r: DeeperRecursiveDict


def test_deeper_recursive():
    ts = generate_ts(DeeperRecursiveDict)
    print(ts, flush=True)

    assert "interface DeeperRecursiveDict" in str(ts)
    assert "r: DeepRecursiveDict" in str(ts)
    assert "s: string" in str(ts)

    assert isinstance(ts, TSInterface)
    full_ts = ts.full_str()
    print(full_ts, flush=True)
    assert "interface DeeperRecursiveDict" in full_ts
    assert "r: DeepRecursiveDict" in full_ts
    assert "s: string" in full_ts
    assert "interface DeepRecursiveDict" in full_ts
    assert "r: DeeperRecursiveDict" in full_ts
    assert "s: string" in full_ts
