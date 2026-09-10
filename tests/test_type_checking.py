"""Tests for annotations referencing names imported under TYPE_CHECKING.

Projects commonly import annotation-only names inside an ``if TYPE_CHECKING:``
block (enforced by e.g. ruff's TC rules). ``typing.get_type_hints`` evaluates
those annotations at runtime, so such names are missing from the module
globals and resolution fails with a ``NameError``.
"""

from __future__ import annotations

import importlib
import linecache
import logging
import sys
import textwrap
import types
import typing
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import pytest

from py2ts import generate_ts

if TYPE_CHECKING:
    from datetime import datetime

if typing.TYPE_CHECKING:
    from datetime import datetime as datetime_alias


class Event(TypedDict):
    """Event whose annotation name only exists for type checkers."""

    name: str
    created_at: datetime


class Timestamped(TypedDict):
    """Event using the ``typing.TYPE_CHECKING`` attribute instead."""

    updated_at: datetime_alias


class Missing(TypedDict):
    """Event referencing a name that does not exist at all."""

    value: DoesNotExist  # noqa: F821


@pytest.fixture
def tmp_modules(tmp_path, monkeypatch):
    """Import modules from source files written to a temporary directory."""
    monkeypatch.syspath_prepend(str(tmp_path))

    def load(
        module_name: str,
        source: str,
        relative_path: str | None = None,
    ) -> types.ModuleType:
        path = tmp_path / (relative_path or f"{module_name}.py")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        importlib.invalidate_caches()
        return importlib.import_module(module_name)

    yield load

    for name in list(sys.modules):
        if name.startswith("_py2ts_fixture"):
            del sys.modules[name]


def test_annotation_from_type_checking_import():
    """Annotations from TYPE_CHECKING imports must still be generated."""
    ts = generate_ts(Event)

    assert "interface Event" in str(ts)
    assert "name: string" in str(ts)
    assert "created_at: Date" in str(ts)


def test_annotation_from_typing_module_attribute():
    """``typing.TYPE_CHECKING`` checks must be recognized as well."""
    ts = generate_ts(Timestamped)

    assert "interface Timestamped" in str(ts)
    assert "updated_at: Date" in str(ts)


def test_missing_annotation_still_raises():
    """A name missing everywhere must still raise a NameError."""
    with pytest.raises(NameError, match="DoesNotExist"):
        generate_ts(Missing)


def test_unparseable_source_is_ignored(tmp_modules):
    """Source that cannot be parsed must not mask the original NameError."""
    module = tmp_modules(
        "_py2ts_fixture_syntax",
        textwrap.dedent(
            """\
            from __future__ import annotations
            from typing import TYPE_CHECKING, TypedDict

            if TYPE_CHECKING:
                from datetime import datetime


            class Event(TypedDict):
                created_at: datetime
            """
        ),
    )
    # Simulate source that no longer matches the imported module.
    Path(module.__file__).write_text("this is not valid python !!!")
    linecache.clearcache()

    with pytest.raises(NameError, match="datetime"):
        generate_ts(module.Event)


def test_module_without_file_is_ignored(monkeypatch):
    """Modules without ``__file__`` are skipped without raising TypeError."""
    module = types.ModuleType("_py2ts_fixture_no_file")
    monkeypatch.setitem(sys.modules, module.__name__, module)

    class NoFile(TypedDict):
        value: DoesNotExist  # noqa: F821

    NoFile.__module__ = module.__name__

    with pytest.raises(NameError, match="DoesNotExist"):
        generate_ts(NoFile)


def test_failing_block_is_logged(tmp_modules, caplog):
    """Failures while evaluating a block are logged with module and error."""
    module = tmp_modules(
        "_py2ts_fixture_broken",
        textwrap.dedent(
            """\
            from __future__ import annotations
            from typing import TYPE_CHECKING, TypedDict

            if TYPE_CHECKING:
                raise RuntimeError("boom")
                from datetime import datetime


            class Event(TypedDict):
                created_at: datetime
            """
        ),
    )

    with caplog.at_level(logging.DEBUG, logger="py2ts"):
        with pytest.raises(NameError):
            generate_ts(module.Event)

    assert "_py2ts_fixture_broken" in caplog.text
    assert "boom" in caplog.text


def test_nested_type_checking_block_is_not_evaluated(tmp_modules):
    """Only top-level TYPE_CHECKING blocks are evaluated."""
    module = tmp_modules(
        "_py2ts_fixture_nested",
        textwrap.dedent(
            """\
            from __future__ import annotations
            from typing import TYPE_CHECKING, TypedDict

            USE_FEATURE = False

            if USE_FEATURE:
                if TYPE_CHECKING:
                    from datetime import datetime


            class Event(TypedDict):
                created_at: datetime
            """
        ),
    )

    with pytest.raises(NameError, match="datetime"):
        generate_ts(module.Event)


def test_relative_import_and_alias_are_resolved(tmp_modules):
    """Relative imports and aliases inside the block are resolved."""
    tmp_modules(
        "_py2ts_fixture_pkg",
        "",
        relative_path="_py2ts_fixture_pkg/__init__.py",
    )
    tmp_modules(
        "_py2ts_fixture_pkg.base",
        textwrap.dedent(
            """\
            from __future__ import annotations


            class Real:
                pass
            """
        ),
        relative_path="_py2ts_fixture_pkg/base.py",
    )
    module = tmp_modules(
        "_py2ts_fixture_pkg.model",
        textwrap.dedent(
            """\
            from __future__ import annotations
            from typing import TYPE_CHECKING, TypedDict

            if TYPE_CHECKING:
                from .base import Real
                Renamed = Real


            class Model(TypedDict):
                value: Renamed
            """
        ),
        relative_path="_py2ts_fixture_pkg/model.py",
    )

    ts = generate_ts(module.Model)

    assert "value: Real" in str(ts)


def test_failing_block_does_not_stop_later_modules(tmp_modules):
    """A failing block must not prevent later MRO modules from being used.

    Dataclasses keep their bases in ``__mro__``, so annotations of the base
    are evaluated with the globals of the base module.
    """
    tmp_modules(
        "_py2ts_fixture_base",
        textwrap.dedent(
            """\
            from __future__ import annotations
            from dataclasses import dataclass
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from datetime import datetime


            @dataclass
            class Base:
                created_at: datetime
            """
        ),
    )
    module = tmp_modules(
        "_py2ts_fixture_mid",
        textwrap.dedent(
            """\
            from __future__ import annotations
            from dataclasses import dataclass
            from typing import TYPE_CHECKING

            from _py2ts_fixture_base import Base

            if TYPE_CHECKING:
                raise RuntimeError("boom")


            @dataclass
            class Mid(Base):
                pass
            """
        ),
    )

    ts = generate_ts(module.Mid)

    assert "created_at: Date" in ts.full_str()
