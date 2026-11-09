from dataclasses import dataclass
from typing import Literal

import pytest
from py2ts.data import TSInterface, TSLiteralType
from py2ts.generate import generate_ts


@pytest.mark.parametrize(
    "py_type, expected_ts_type, expected_ts_str",
    [
        (Literal["foo"], TSLiteralType("foo"), '"foo"'),
        (Literal['say "hi"'], TSLiteralType('say "hi"'), '"say \\"hi\\""'),
        (Literal[True], TSLiteralType(True), "true"),
        (Literal[False], TSLiteralType(False), "false"),
        (Literal[1], TSLiteralType(1), "1"),
        (Literal[None], TSLiteralType(None), "null"),
    ],
)
def test_literal(py_type, expected_ts_type, expected_ts_str):
    ts = generate_ts(py_type)

    assert ts == expected_ts_type, f"Expected {expected_ts_type}, but got {ts}"
    assert str(ts) == expected_ts_str, f"Expected {expected_ts_str}, but got {ts!s}"


@pytest.mark.parametrize(
    "py_type, expected_ts_str",
    [
        (Literal["foo", "bar"], '"bar" | "foo"'),
        # True == 1 in Python, but "true" and "1" are distinct TS literals
        (Literal[True, 1], "1 | true"),
        (
            Literal["auto", "preview", "bootleg", "off", False],
            '"auto" | "bootleg" | "off" | "preview" | false',
        ),
    ],
)
def test_literal_union(py_type, expected_ts_str):
    assert str(generate_ts(py_type)) == expected_ts_str


def test_literal_in_interface():
    """Regression test for https://github.com/semohr/py2ts/issues/3."""

    @dataclass
    class InboxFolderSchema:
        autotag: Literal["auto", "preview", "bootleg", "off", False] = "off"

    ts = generate_ts(InboxFolderSchema)

    assert isinstance(ts, TSInterface)
    assert 'autotag: "auto" | "bootleg" | "off" | "preview" | false;' in str(ts)
