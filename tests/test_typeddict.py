from typing import TypedDict
from typing_extensions import NotRequired

from py2ts.data import TSInterface
from py2ts.generate import generate_ts


def test_base_types():
    class StringDict(TypedDict):
        s: str
        i: int
        f: float
        b: bool
        n: None

    ts = generate_ts(StringDict)

    assert "interface StringDict" in str(ts)
    assert "s: string" in str(ts)
    assert "i: number" in str(ts)
    assert "f: number" in str(ts)
    assert "b: boolean" in str(ts)
    assert "n: null" in str(ts)


def test_not_required():
    class NotRequiredDict(TypedDict):
        s: NotRequired[str]
        i: NotRequired[int]
        f: NotRequired[float]
        b: NotRequired[bool]
        n: NotRequired[None]

    ts = generate_ts(NotRequiredDict)

    assert "interface NotRequiredDict" in str(ts)
    assert "s?: string" in str(ts)
    assert "i?: number" in str(ts)
    assert "f?: number" in str(ts)
    assert "b?: boolean" in str(ts)
    assert "n?: null" in str(ts)


def test_nested():
    class InnerDict(TypedDict):
        s: str

    class DeepDict(TypedDict):
        deep: InnerDict | None

    class OuterDict(TypedDict):
        nested: InnerDict
        deep: DeepDict | None

    ts = generate_ts(OuterDict)

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
