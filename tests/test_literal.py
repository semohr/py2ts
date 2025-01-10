from typing import Literal
import pytest
from py2ts.generate import generate_ts
from py2ts.data import TSLiteralType, TSUnionType


@pytest.mark.parametrize(
    "py_type, expected_ts_type, expected_ts_str",
    [
        (
            Literal["foo"],
            TSLiteralType("foo"),
            '"foo"',
        ),
        (
            Literal["foo", "bar"],
            TSUnionType({TSLiteralType("foo"), TSLiteralType("bar")}),
            '"bar" | "foo"',
        ),
    ],
)
def test_literal(py_type, expected_ts_type, expected_ts_str):
    ts = generate_ts(py_type)

    assert ts == expected_ts_type, f"Expected {expected_ts_type}, but got {ts}"
    assert str(ts) == expected_ts_str, f"Expected {expected_ts_str}, but got {str(ts)}"
