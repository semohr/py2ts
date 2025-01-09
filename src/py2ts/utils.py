from types import UnionType
from typing import List, Union, get_args, get_origin


def split_comment(comment: str | None, n: int) -> list[str]:
    """Split a comment into lines of length n characters.

    For a line length of e.g. 80 characters, you need to adjust n to account for the
    padding added by the comment prefix. For example, if the comment prefix is "// ",
    then n should be 77.
    """
    if comment is None or len(comment) == 0:
        return []

    lines: List[str] = []
    s = comment.split("\n")
    for line in s:
        line = line.strip()
        t = [line[i : i + n] for i in range(0, len(line), n)]
        lines.extend(t)
    return lines


def is_optional_type(expected_type: type | UnionType) -> bool:
    """Check if the type is Optional[T]."""
    return get_origin(expected_type) is Union and type(None) in get_args(expected_type)
