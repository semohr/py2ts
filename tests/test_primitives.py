from typing import Any
import pytest
from py2ts.generate import generate_ts
from py2ts.data import TypescriptPrimitive, TSPrimitiveType


@pytest.mark.parametrize(
    "py_type, expected_ts_type, expected_ts_str",
    [
        (str, TSPrimitiveType(TypescriptPrimitive.STRING), "string"),
        (int, TSPrimitiveType(TypescriptPrimitive.NUMBER), "number"),
        (float, TSPrimitiveType(TypescriptPrimitive.NUMBER), "number"),
        (bool, TSPrimitiveType(TypescriptPrimitive.BOOLEAN), "boolean"),
        (type(None), TSPrimitiveType(TypescriptPrimitive.NULL), "null"),
        (Any, TSPrimitiveType(TypescriptPrimitive.ANY), "any"),
    ],
)
def test_primitive_types(py_type, expected_ts_type, expected_ts_str):
    """Test conversion of basic Python types to TypeScript."""
    t = generate_ts(py_type)
    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    assert str(t) == expected_ts_str, f"Expected {expected_ts_str}, but got {str(t)}"


def test_hashes():
    """Test hash values of primitive types."""
    t = []
    for e in TypescriptPrimitive:
        t.append(TSPrimitiveType(e))
    s = set(t)
    assert len(t) == len(s)
