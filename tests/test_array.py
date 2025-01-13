from typing import List, Sequence
import pytest
from collections.abc import Sequence as ABCSequence

from py2ts.config import CONFIG
from py2ts.generate import generate_ts
from py2ts.data import TSArrayType, TSPrimitiveType, TypescriptPrimitive


@pytest.mark.parametrize(
    "py_type, expected_ts_type, expected_ts_str",
    [
        (
            str,
            TSArrayType(TSPrimitiveType(TypescriptPrimitive.STRING)),
            "Array<string>",
        ),
        (
            int,
            TSArrayType(TSPrimitiveType(TypescriptPrimitive.NUMBER)),
            "Array<number>",
        ),
        (
            float,
            TSArrayType(TSPrimitiveType(TypescriptPrimitive.NUMBER)),
            "Array<number>",
        ),
        (
            bool,
            TSArrayType(TSPrimitiveType(TypescriptPrimitive.BOOLEAN)),
            "Array<boolean>",
        ),
        (
            type(None),
            TSArrayType(TSPrimitiveType(TypescriptPrimitive.NULL)),
            "Array<null>",
        ),
    ],
)
def test_basic_array(py_type, expected_ts_type, expected_ts_str):
    """Test conversion of basic Python types to TypeScript."""

    # Test List
    CONFIG.none_as_null = True
    t = generate_ts(List[py_type])

    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    assert str(t) == expected_ts_str, f"Expected {expected_ts_str}, but got {str(t)}"

    # Test list
    t = generate_ts(list[py_type])

    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    assert str(t) == expected_ts_str, f"Expected {expected_ts_str}, but got {str(t)}"

    # Test sequence
    t = generate_ts(Sequence[py_type])

    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    assert str(t) == expected_ts_str, f"Expected {expected_ts_str}, but got {str(t)}"

    # Test ABCSequence
    t = generate_ts(ABCSequence[py_type])

    assert t == expected_ts_type, f"Expected {expected_ts_type}, but got {t}"
    assert str(t) == expected_ts_str, f"Expected {expected_ts_str}, but got {str(t)}"
