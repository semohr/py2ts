from typing import Optional, Union

import pytest
from py2ts.generate import generate_ts
from py2ts.data import TSPrimitiveType, TSUnionType
from py2ts.config import CONFIG


@pytest.mark.parametrize("config_none_as_null", [True, False])
@pytest.mark.parametrize(
    "py_type, expected_ts_str",
    [
        (str | None, "string"),
        (int | None, "number"),
        (Optional[float], "number"),  # noqa: UP045 - also test typing.Optional path
        (Optional[bool], "boolean"),  # noqa: UP045 - also test typing.Optional path
    ],
)
def test_optional_extras(config_none_as_null, py_type, expected_ts_str):
    """Test conversion of basic Python types to TypeScript with optional.

    Should resolve to union of the primitive type and undefined or null depending on
    config.
    """
    CONFIG.none_as_null = config_none_as_null
    t = generate_ts(py_type)

    none_str = "null" if config_none_as_null else "undefined"
    assert expected_ts_str in str(t)
    assert none_str in str(t)

    # Check union has 2 types
    assert isinstance(t, TSUnionType)
    assert len(t) == 2


@pytest.mark.parametrize(
    "py_type, expected_ts_str",
    [
        (Union[str, int], ("string", "number")),  # noqa: UP007 - test typing.Union path
        (float | bool, ("number", "boolean")),
        (Union[bool, str], ("boolean", "string")),  # noqa: UP007 - typing.Union
        (str | bool, ("boolean", "string")),
        (Union[str, float], ("string", "number")),  # noqa: UP007 - typing.Union
        (str | float, ("string", "number")),
    ],
)
def test_basic_union(py_type, expected_ts_str):
    """Test conversion of basic Python types to TypeScript with optional.

    Should resolve to union of the primitive type and undefined or null depending on
    config.
    """
    t = generate_ts(py_type)
    for ts_str in expected_ts_str:
        assert ts_str in str(t)

    assert isinstance(t, TSUnionType)
    assert len(t) == len(expected_ts_str)


@pytest.mark.parametrize(
    "py_type, expected_ts_str",
    [
        (Union[str, str, int], ("string", "number")),  # noqa: UP007 - typing.Union
        (float | int, ("number",)),
        (Union[bool, bool, int], ("boolean", "number")),  # noqa: UP007 - typing.Union
        (Optional[type(None) | int], ("null", "number")),  # noqa: UP045 - typing.Optional
    ],
)
def test_concat_of_same_type(py_type, expected_ts_str):
    """Test conversion of basic Python types to TypeScript with optional.

    Should resolve duplicates
    """
    CONFIG.none_as_null = True
    t = generate_ts(py_type)
    for ts_str in expected_ts_str:
        assert ts_str in str(t)

    assert isinstance(t, TSUnionType)
    assert len(t) == len(expected_ts_str)


@pytest.mark.parametrize(
    "py_type",
    [
        (str | int | float | bool),
        (Union[str | int, float | bool]),  # noqa: UP007 - nested typing.Union
    ],
)
def test_nested_unions(py_type):
    """Test conversion of nested unions.
    Should resolve to a flat union of all types.
    """
    t = generate_ts(py_type)
    assert isinstance(t, TSUnionType)
    assert len(t) == 3

    for i in t:
        assert isinstance(i, TSPrimitiveType)
