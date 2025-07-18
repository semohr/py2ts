from typing import TypedDict
from py2ts.builder import TSBuilder


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
        == "export interface DeepDict {\n\tdeep: InnerDict | null;\n}\n\nexport interface InnerDict {\n\ts: string;\n}\n\n"
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
        == "export interface DeepDict {\n\tdeep: InnerDict | null;\n}\n\nexport interface InnerDict {\n\ts: string;\n}\n\n"
    )
