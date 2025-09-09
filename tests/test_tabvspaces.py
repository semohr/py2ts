from enum import Enum

from py2ts.config import CONFIG
from py2ts.generate import generate_ts


class Colors(Enum):
    Green = 1
    Red = 2


def test_tab_indent():
    # Test case for tabs vs spaces
    # Test Tuple
    CONFIG.indent_with_tabs = True
    ts = generate_ts(Colors)
    assert str(ts) == "export enum Colors {\n\tGreen = 1,\n\tRed = 2,\n}"


def test_space_indent():
    # Test case for tabs vs spaces
    # Test Tuple
    CONFIG.indent_with_tabs = False
    CONFIG.indent_size = 2
    ts = generate_ts(Colors)
    assert str(ts) == "export enum Colors {\n  Green = 1,\n  Red = 2,\n}"

    CONFIG.indent_size = 4
    ts = generate_ts(Colors)
    assert str(ts) == "export enum Colors {\n    Green = 1,\n    Red = 2,\n}"
