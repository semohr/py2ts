from typing import TypedDict


class Config(TypedDict):
    """Configuration for the py2ts module."""

    # The maximum length of a comment line.
    comment_line_length: int

    # Whether to treat None as null in TypeScript. Otherwise, None will be treated as
    # undefined.
    none_as_null: bool


CONFIG = Config(comment_line_length=80, none_as_null=True)
