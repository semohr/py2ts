from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from typing_extensions import NotRequired


class MinimalConfig(TypedDict):
    """Configuration for the py2ts module."""

    # The maximum length of a comment line.
    comment_line_length: NotRequired[int]

    # Whether to treat None as null in TypeScript. Otherwise, None will be treated as
    # undefined.
    none_as_null: NotRequired[bool]

    # Add "export" keyword to generated interfaces and enums
    export_interfaces: NotRequired[bool]

    # Any as unknown
    any_as_unknown: NotRequired[bool]

    indent_with_tabs: NotRequired[bool]
    indent_size: NotRequired[int]


@dataclass
class Config:
    """Configuration for the py2ts module."""

    # The maximum length of a comment line.
    comment_line_length: int = 80

    # Whether to treat None as null in TypeScript. Otherwise, None will be treated as
    # undefined.
    none_as_null: bool = True

    # Add "export" keyword to generated interfaces and enums
    export_interfaces: bool = True

    # Any as unknown
    any_as_unknown: bool = True

    # Tabs vs Space
    indent_with_tabs: bool = True
    # Only used if indent_with_tabs is False
    indent_size: int = 4

    def override(self, config: MinimalConfig) -> Config:
        """Override the configuration with the provided configuration."""
        return Config(
            comment_line_length=config.get(
                "comment_line_length", self.comment_line_length
            ),
            none_as_null=config.get("none_as_null", self.none_as_null),
            export_interfaces=config.get("export_interfaces", self.export_interfaces),
            indent_with_tabs=config.get("indent_with_tabs", self.indent_with_tabs),
            indent_size=config.get("indent_size", self.indent_size),
            any_as_unknown=config.get("any_as_unknown", self.any_as_unknown),
        )

    @property
    def TAB(self):
        """Return the indentation string based on the configuration."""
        return "\t" if self.indent_with_tabs else " " * self.indent_size


CONFIG = Config()
