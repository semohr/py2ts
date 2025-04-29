from typing import TypedDict
from py2ts.builder import TSBuilder


def test_basic_builder():
    class StringDict(TypedDict):
        s: str

    ts_builder = TSBuilder()
    ts_builder.add(StringDict)

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
