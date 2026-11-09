from enum import Enum, auto
from py2ts import generate_ts
from py2ts.data import TSEnumType, TSInterface


def test_basic_enum():
    class Colors(Enum):
        Green = 1
        Red = 2

    ts = generate_ts(Colors)
    print(ts)

    assert isinstance(ts, TSEnumType)
    assert str(ts) == "export enum Colors {\n\tGreen = 1,\n\tRed = 2,\n}"


def test_with_string_value():
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


def test_with_boolean_and_float_value():
    """Booleans/floats in mixed-type enums (issue #3)."""

    class AutoTag(Enum):
        Auto = "auto"
        Small = 0.5
        On = True
        Off = False

    ts = generate_ts(AutoTag)

    assert isinstance(ts, TSEnumType)
    assert str(ts) == (
        "export enum AutoTag {\n"
        "\tAuto = 'auto',\n"
        "\tSmall = 0.5,\n"
        "\tOn = true,\n"
        "\tOff = false,\n"
        "}"
    )


def test_enum_aliases_are_kept():
    class Toggle(Enum):
        Off = False
        Zero = 0  # alias of Off in Python

    assert str(generate_ts(Toggle)) == (
        "export enum Toggle {\n\tOff = false,\n\tZero = false,\n}"
    )


def test_enum_in_dict():
    class Colors(Enum):
        Green = 1
        Red = "red"

    class Test:
        color: Colors

    ts = generate_ts(Test)

    assert isinstance(ts, TSInterface)
    print(ts.full_str())

    fs = ts.full_str()
    assert "color: Colors" in fs
    assert "export enum Colors" in fs
    assert "Green = 1" in fs
    assert "Red = 'red'" in fs
    assert "export interface Test" in fs
