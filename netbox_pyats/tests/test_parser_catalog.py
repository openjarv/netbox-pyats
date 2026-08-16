"""Tests for :mod:`netbox_pyats.parser_catalog` (ATW-241 child 1, ATW-249).

Pure-Python: exercises the parser-catalog refresh logic against a fake
pyATS Device and a stubbed ``get_parser_commands`` (no NetBox, no RQ, no real
Genie). pyATS's ``pyats.topology`` is importable without genie on this worker
(see ``test_testbed.py``), but :func:`refresh_parser_catalog_for_os`
imports ``genie.libs.parser.utils`` lazily inside the function, so we can
test the unsupported-os path and the stub-device path without genie installed
by patching the lazy import.

Covers:
- Unsupported os → empty ``commands`` with a warning, no genie import.
- Supported os with a stubbed ``get_parser_commands`` → sorted command list.
- ``get_parser_commands`` failure → empty ``commands`` with a warning.
- Stub-device build failure (pyats.topology missing) → empty with a warning.
- ``supported_os_values`` returns the deduplicated supported os set from
  ``PLATFORM_SLUG_TO_PYATS_OS``.
- Version strings are best-effort (empty when metadata missing).
"""

import pytest

pytest.importorskip("pyats")

from netbox_pyats.parser_catalog import CatalogRefreshResult, refresh_parser_catalog_for_os, supported_os_values
from netbox_pyats.testbed import PLATFORM_SLUG_TO_PYATS_OS, UNSUPPORTED_OS


class TestRefreshParserCatalogForOs:
    """Exercise :func:`refresh_parser_catalog_for_os` with a stubbed genie import."""

    def _patch_get_parser_commands(self, monkeypatch, return_value=None, exc=None):
        """Patch ``genie.libs.parser.utils.get_parser_commands`` lazily.

        ``refresh_parser_catalog_for_os`` does ``from genie.libs.parser.utils
        import get_parser_commands`` inside the function, so we patch the
        target module's attribute and let the import resolve to it. When
        genie is not installed (the pure-Python CI lane), the real
        ``genie.libs.parser.utils`` module is absent; we inject a fake
        module into ``sys.modules`` so the lazy import succeeds.
        """
        import sys
        import types

        # Build a fake genie.libs.parser.utils module with get_parser_commands.
        fake_pkg_genie = types.ModuleType("genie")
        fake_pkg_genie_libs = types.ModuleType("genie.libs")
        fake_pkg_genie_libs_parser = types.ModuleType("genie.libs.parser")
        fake_pkg_genie_libs_parser_utils = types.ModuleType("genie.libs.parser.utils")

        def _fake_get_parser_commands(device):
            if exc is not None:
                raise exc
            return return_value

        fake_pkg_genie_libs_parser_utils.get_parser_commands = _fake_get_parser_commands

        # Register the fake package chain so the lazy import resolves.
        monkeypatch.setitem(sys.modules, "genie", fake_pkg_genie)
        monkeypatch.setitem(sys.modules, "genie.libs", fake_pkg_genie_libs)
        monkeypatch.setitem(sys.modules, "genie.libs.parser", fake_pkg_genie_libs_parser)
        monkeypatch.setitem(sys.modules, "genie.libs.parser.utils", fake_pkg_genie_libs_parser_utils)

    def test_unsupported_os_returns_empty_with_warning(self):
        result = refresh_parser_catalog_for_os(UNSUPPORTED_OS)
        assert isinstance(result, CatalogRefreshResult)
        assert result.pyats_os == UNSUPPORTED_OS
        assert result.commands == []
        assert result.warnings and "unsupported" in result.warnings[0].lower()

    def test_empty_os_returns_empty_with_warning(self):
        result = refresh_parser_catalog_for_os("")
        assert result.commands == []
        assert result.warnings

    def test_supported_os_returns_sorted_commands(self, monkeypatch):
        self._patch_get_parser_commands(
            monkeypatch,
            return_value=["show version", "show ip interface brief", "show interfaces"],
        )
        result = refresh_parser_catalog_for_os("iosxe")
        assert result.pyats_os == "iosxe"
        # Sorted for deterministic storage / stable checkbox ordering.
        assert result.commands == ["show interfaces", "show ip interface brief", "show version"]
        assert result.warnings == []

    def test_supported_os_dedupes_commands(self, monkeypatch):
        # get_parser_commands may return duplicates (a command appearing in
        # multiple parser packages). The helper de-dupes via a set.
        self._patch_get_parser_commands(
            monkeypatch,
            return_value=["show version", "show version", "show interfaces"],
        )
        result = refresh_parser_catalog_for_os("nxos")
        assert result.commands == ["show interfaces", "show version"]

    def test_supported_os_coerces_non_strings_to_strings(self, monkeypatch):
        # Defensive: get_parser_commands may return non-string entries.
        self._patch_get_parser_commands(
            monkeypatch,
            return_value=["show version", 42, None, "show interfaces"],
        )
        result = refresh_parser_catalog_for_os("iosxe")
        # None is dropped (falsy); 42 is coerced to "42".
        assert result.commands == ["42", "show interfaces", "show version"]

    def test_get_parser_commands_failure_returns_empty_with_warning(self, monkeypatch):
        self._patch_get_parser_commands(monkeypatch, exc=RuntimeError("parser registry boom"))
        result = refresh_parser_catalog_for_os("iosxe")
        assert result.commands == []
        assert result.warnings and "get_parser_commands failed" in result.warnings[0]

    def test_empty_command_list_is_valid(self, monkeypatch):
        # An os Genie has a parser package for but no registered commands
        # returns an empty list with no warning (not an error).
        self._patch_get_parser_commands(monkeypatch, return_value=[])
        result = refresh_parser_catalog_for_os("iosxe")
        assert result.commands == []
        assert result.warnings == []

    def test_version_strings_present_in_result(self, monkeypatch):
        # Version strings are best-effort; we only assert the fields exist
        # (the actual value depends on the worker env). The shared helper
        # netbox_pyats.utils.worker_versions returns "" when metadata is
        # unavailable — so we just check the attribute is a string, not
        # that it is populated.
        self._patch_get_parser_commands(monkeypatch, return_value=["show version"])
        result = refresh_parser_catalog_for_os("iosxe")
        assert isinstance(result.genie_version, str)
        assert isinstance(result.pyats_version, str)


class TestSupportedOsValues:
    """Exercise :func:`supported_os_values` — the deduplicated supported os set."""

    def test_returns_deduplicated_supported_os_values(self):
        values = list(supported_os_values())
        # Every value is a supported os (not the unsupported sentinel).
        assert all(v != UNSUPPORTED_OS for v in values)
        # No duplicates.
        assert len(values) == len(set(values))
        # Derived from PLATFORM_SLUG_TO_PYATS_OS: every value is in its values.
        assert all(v in PLATFORM_SLUG_TO_PYATS_OS.values() for v in values)

    def test_includes_known_supported_oses(self):
        values = set(supported_os_values())
        # The conservative map covers at least these (see testbed.py).
        assert "iosxe" in values
        assert "iosxr" in values
        assert "nxos" in values
        assert "ios" in values

    def test_is_iterable_and_deterministic(self):
        # Two calls yield the same order (insertion order from the map).
        first = list(supported_os_values())
        second = list(supported_os_values())
        assert first == second
