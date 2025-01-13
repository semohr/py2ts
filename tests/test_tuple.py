from typing import Tuple
import pytest

from py2ts.config import CONFIG
from py2ts.generate import generate_ts
from py2ts.data import TSTupleType, TSPrimitiveType, TypescriptPrimitive


@pytest.mark.parametrize(
    "py_types, expected_ts_type, expected_ts_str",
    [
        (
            (str, int),
            TSTupleType(
                {
                    TSPrimitiveType(TypescriptPrimitive.STRING),
                    TSPrimitiveType(TypescriptPrimitive.NUMBER),
                }
            ),
            {"string", "number"},
        ),
        (
            (float, bool),
            TSTupleType(
                {
                    TSPrimitiveType(TypescriptPrimitive.NUMBER),
                    TSPrimitiveType(TypescriptPrimitive.BOOLEAN),
                }
            ),
            {"number", "boolean"},
        ),
        (
            (bool, type(None)),
            TSTupleType(
                {
                    TSPrimitiveType(TypescriptPrimitive.BOOLEAN),
                    TSPrimitiveType(TypescriptPrimitive.NULL),
                }
            ),
            {"boolean", "null"},
        ),
    ],
)
def test_basic_tuple(py_types, expected_ts_type, expected_ts_str):
    """Test conversion of basic Python tuples to TypeScript."""

    # Test Tuple
    CONFIG.none_as_null = True
    t = generate_ts(Tuple[py_types])

    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    for ts_str in expected_ts_str:
        assert ts_str in str(t)
    assert isinstance(t, TSTupleType)
    assert len(t) == len(expected_ts_str)

    # Test tuple (Python 3.9+ syntax)
    t = generate_ts(tuple[py_types])

    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    for ts_str in expected_ts_str:
        assert ts_str in str(t)
    assert isinstance(t, TSTupleType)
    assert len(t) == len(expected_ts_str)
