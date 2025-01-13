from enum import Enum, auto
from py2ts import generate_ts
from py2ts.data import TSEnumType


def test_basic_enum():
    class Colors(Enum):
        Green = 1
        Red = 2

    ts = generate_ts(Colors)
    print(ts)

    assert isinstance(ts, TSEnumType)
    assert str(ts) == "export enum Colors {\n\tGreen = 1,\n\tRed = 2,\n}"


def test_with_stringValue():
    class Colors(Enum):
        Green = "green"
        Red = "red"

    ts = generate_ts(Colors)
    print(ts)

    assert isinstance(ts, TSEnumType)
    assert str(ts) == "export enum Colors {\n\tGreen = 'green',\n\tRed = 'red',\n}"


def test_with_auto():
    class Colors(Enum):
        Green = auto()
        Red = auto()

    ts = generate_ts(Colors)
    print(ts)

    assert isinstance(ts, TSEnumType)
    assert str(ts) == "export enum Colors {\n\tGreen = 1,\n\tRed = 2,\n}"
