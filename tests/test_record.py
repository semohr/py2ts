from typing import Dict, TypedDict
import pytest

from py2ts.config import CONFIG
from py2ts.generate import generate_ts
from py2ts.data import TSPrimitiveType, TSRecordType, TypescriptPrimitive


@pytest.mark.parametrize(
    "py_types, expected_ts_type, expected_ts_str",
    [
        (
            dict,
            TSRecordType(
                TSPrimitiveType(TypescriptPrimitive.UNKNOWN),
                TSPrimitiveType(TypescriptPrimitive.UNKNOWN),
            ),
            "Record<unknown, unknown>",
        ),
        (
            dict[str, int],
            TSRecordType(
                TSPrimitiveType(TypescriptPrimitive.STRING),
                TSPrimitiveType(TypescriptPrimitive.NUMBER),
            ),
            "Record<string, number>",
        ),
        (
            dict[str, str],
            TSRecordType(
                TSPrimitiveType(TypescriptPrimitive.STRING),
                TSPrimitiveType(TypescriptPrimitive.STRING),
            ),
            "Record<string, string>",
        ),
        (
            Dict,
            TSRecordType(
                TSPrimitiveType(TypescriptPrimitive.UNKNOWN),
                TSPrimitiveType(TypescriptPrimitive.UNKNOWN),
            ),
            "Record<unknown, unknown>",
        ),
        (
            Dict[str, None],
            TSRecordType(
                TSPrimitiveType(TypescriptPrimitive.STRING),
                TSPrimitiveType(TypescriptPrimitive.NULL),
            ),
            "Record<string, null>",
        ),
        (
            Dict[None, str],
            TSRecordType(
                TSPrimitiveType(TypescriptPrimitive.NULL),
                TSPrimitiveType(TypescriptPrimitive.STRING),
            ),
            "Record<null, string>",
        ),
    ],
)
def test_basic_record(py_types, expected_ts_type, expected_ts_str):
    """Test conversion of basic Python tuples to TypeScript."""

    # Test Tuple
    CONFIG.none_as_null = True
    t = generate_ts(py_types)
    ts_str = str(t)

    assert isinstance(t, TSRecordType)
    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    assert ts_str == expected_ts_str, f"Expected {expected_ts_str}, but got {ts_str}"


def test_nested_record():
    class InnerRecord(TypedDict):
        s: str

    t = generate_ts(Dict[str, InnerRecord])
    ts_str = str(t)
    print(ts_str, flush=True)
    assert "Record<string, InnerRecord>" in ts_str
