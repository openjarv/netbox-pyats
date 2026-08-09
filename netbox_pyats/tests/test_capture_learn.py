"""Tests for the Genie Ops Learn capture (ATW-730).

Pure-Python: exercises :func:`netbox_pyats.capture._capture_learn` and the
``kind='learn'`` path of :func:`netbox_pyats.capture.capture_snapshot` against
a fake pyATS Device and a stubbed ``genie.ops.utils.Lookup`` (no NetBox, no
RQ, no real Genie). The helper imports ``genie.ops.utils`` lazily inside the
function, so we inject a fake module into ``sys.modules`` so the lazy import
resolves — the same pattern as ``test_parser_catalog.py``.

Covers:
- Unsupported platform → ``status="unsupported"`` (the shared short-circuit
  in :func:`capture_snapshot`, before any Genie import).
- Successful Learn → ``data["learn"]`` keyed by Ops feature name.
- Per-feature graceful degradation: one feature raising a non-AttributeError
  exception is recorded as a warning and omitted, the rest still captured.
- ``AttributeError`` from a feature (the Ops framework exposes features the
  device's os does not implement) is skipped silently.
- Empty learn (no features discovered) → ``status="error"`` with a warning.
- ``Lookup.from_device`` failure → empty learn with a warning, error status.
- ``genie.ops.utils`` import failure → empty learn with a warning, error status.
"""

import pytest

pytest.importorskip("pyats")

from netbox_pyats.capture import capture_snapshot
from netbox_pyats.choices import SnapshotKindChoices, SnapshotStatusChoices
from netbox_pyats.testbed import UNSUPPORTED_OS


class FakeOpsInstance:
    """Duck-typed Genie Ops instance returned by an Ops class factory.

    ``_capture_learn`` calls ``factory(device).learn()`` then reads
    ``.ops`` (falling back to ``.data``) for the structured payload.
    """

    def __init__(self, payload, learn_exc=None):
        self._payload = payload
        self._learn_exc = learn_exc

    def learn(self):
        if self._learn_exc is not None:
            raise self._learn_exc

    @property
    def ops(self):
        return self._payload


class FakeOpsFactory:
    """Callable that returns a :class:`FakeOpsInstance` when called with a device."""

    def __init__(self, payload, learn_exc=None):
        self._payload = payload
        self._learn_exc = learn_exc

    def __call__(self, device):
        return FakeOpsInstance(self._payload, learn_exc=self._learn_exc)


class FakeOpsClassModule:
    """Duck-typed 2nd-level ``lookup.ops.<feature>.<feature>`` module.

    Exposes the concrete Ops class under the capitalized feature name
    (e.g. ``.Interface`` for feature ``interface``), matching the real Genie
    2-level ``ops.<feature>.<feature>.<ClassName>`` resolution.
    """

    def __init__(self, class_name, ops_class):
        setattr(self, class_name, ops_class)


class FakeOpsFeatureModule:
    """Duck-typed 1st-level ``lookup.ops.<feature>`` AbstractedModule.

    Exposes the 2nd-level module under the same feature name
    (``lookup.ops.interface.interface``).
    """

    def __init__(self, feature_name, class_module):
        setattr(self, feature_name, class_module)


class FakeOpsNamespace:
    """Duck-typed ``lookup.ops`` namespace exposing 2-level feature modules."""

    def __init__(self, features):
        # features: dict of {name: FakeOpsFactory}
        for name, factory in features.items():
            class_module = FakeOpsClassModule(name.capitalize(), factory)
            setattr(self, name, FakeOpsFeatureModule(name, class_module))


class FakeLookup:
    """Duck-typed ``genie.ops.utils.Lookup`` instance."""

    def __init__(self, ops_namespace):
        self.ops = ops_namespace


class _FakeModuleInfo:
    """Duck-typed ``pkgutil.ModuleInfo`` for ``pkgutil.iter_modules``."""

    def __init__(self, name):
        self.name = name


def _patch_genie_ops(monkeypatch, lookup=None, from_device_exc=None, features=None):
    """Inject a fake ``genie.ops.utils.Lookup`` + ``genie.libs.ops`` into ``sys.modules``.

    ``_capture_learn`` does ``import genie.libs.ops`` and
    ``from genie.ops.utils import Lookup`` inside the function. We register a
    fake package chain so the lazy imports resolve, with ``Lookup.from_device``
    returning the configured lookup (or raising). ``features`` (a dict of
    {name: factory}) drives both the fake namespace and the patched
    ``pkgutil.iter_modules`` feature-name enumeration.
    """
    import sys
    import types

    if features is None:
        features = {}

    fake_genie = types.ModuleType("genie")
    fake_genie_libs = types.ModuleType("genie.libs")
    fake_genie_libs_ops = types.ModuleType("genie.libs.ops")
    fake_genie_libs_ops.__path__ = []  # marks it as a package for pkgutil
    fake_genie_ops = types.ModuleType("genie.ops")
    fake_genie_ops_utils = types.ModuleType("genie.ops.utils")

    class _FakeLookupClass:
        @staticmethod
        def from_device(device, packages=None):
            if from_device_exc is not None:
                raise from_device_exc
            return lookup

    fake_genie_ops_utils.Lookup = _FakeLookupClass

    monkeypatch.setitem(sys.modules, "genie", fake_genie)
    monkeypatch.setitem(sys.modules, "genie.libs", fake_genie_libs)
    monkeypatch.setitem(sys.modules, "genie.libs.ops", fake_genie_libs_ops)
    monkeypatch.setitem(sys.modules, "genie.ops", fake_genie_ops)
    monkeypatch.setitem(sys.modules, "genie.ops.utils", fake_genie_ops_utils)

    # Attach genie.libs.ops as an attribute of genie.libs so
    # ``import genie.libs.ops`` inside _capture_learn resolves the attribute.
    fake_genie_libs.ops = fake_genie_libs_ops
    fake_genie.libs = fake_genie_libs

    # Patch pkgutil.iter_modules to return the fake feature list when called
    # against the fake genie.libs.ops package (``__path__ == []``).
    import pkgutil as _pkgutil

    real_iter_modules = _pkgutil.iter_modules

    def _fake_iter_modules(path, prefix=""):
        if path == []:
            return [_FakeModuleInfo(name) for name in sorted(features)]
        return real_iter_modules(path, prefix)

    monkeypatch.setattr(_pkgutil, "iter_modules", _fake_iter_modules)


class FakePyatsDevice:
    """Minimal duck-typed pyATS Device for Learn tests.

    The Learn path only reads ``name`` and ``os`` (no ``parse``/``execute``);
    the Genie Ops framework is stubbed via the patched ``Lookup``.
    """

    def __init__(self, name="rtr01", os="iosxe"):
        self.name = name
        self.os = os


class TestLearnUnsupportedPlatform:
    def test_unsupported_os_short_circuits_before_genie_import(self):
        # The shared short-circuit in capture_snapshot returns unsupported
        # before _capture_learn (and its genie import) is reached.
        d = FakePyatsDevice(os=UNSUPPORTED_OS)
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_UNSUPPORTED
        assert result.data == {}
        assert any("no Genie parser" in w for w in result.warnings)


class TestLearnCapture:
    def test_successful_learn_writes_data_keyed_by_feature(self, monkeypatch):
        features = {
            "interface": FakeOpsFactory({"interfaces": {"Gig0": {"enabled": True}}}),
            "bgp": FakeOpsFactory({"neighbors": {"1.1.1.1": {"state": "Established"}}}),
        }
        ops = FakeOpsNamespace(features)
        _patch_genie_ops(monkeypatch, lookup=FakeLookup(ops), features=features)
        d = FakePyatsDevice(os="iosxe")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "learn" in result.data
        assert set(result.data["learn"].keys()) == {"interface", "bgp"}
        assert result.data["learn"]["interface"]["interfaces"]["Gig0"]["enabled"] is True
        assert result.warnings == []

    def test_learn_carries_parsed_os(self, monkeypatch):
        features = {"interface": FakeOpsFactory({"x": 1})}
        ops = FakeOpsNamespace(features)
        _patch_genie_ops(monkeypatch, lookup=FakeLookup(ops), features=features)
        d = FakePyatsDevice(os="nxos")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.parsed_os == "nxos"

    def test_per_feature_failure_is_warning_not_fatal(self, monkeypatch):
        # One feature raises a non-AttributeError exception → recorded as a
        # warning and omitted; the other feature is still captured.
        features = {
            "interface": FakeOpsFactory({"ok": True}),
            "bgp": FakeOpsFactory(None, learn_exc=RuntimeError("bgp learn boom")),
        }
        ops = FakeOpsNamespace(features)
        _patch_genie_ops(monkeypatch, lookup=FakeLookup(ops), features=features)
        d = FakePyatsDevice(os="iosxe")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "interface" in result.data["learn"]
        assert "bgp" not in result.data["learn"]
        assert any("bgp" in w and "learn failed" in w for w in result.warnings)

    def test_attribute_error_feature_is_silently_skipped(self, monkeypatch):
        # AttributeError from a feature (the Ops framework exposes features
        # the device's os does not implement) is skipped silently with a debug
        # log — not a warning, not fatal.
        features = {
            "interface": FakeOpsFactory({"ok": True}),
            "bgp": FakeOpsFactory(None, learn_exc=AttributeError("not applicable")),
        }
        ops = FakeOpsNamespace(features)
        _patch_genie_ops(monkeypatch, lookup=FakeLookup(ops), features=features)
        d = FakePyatsDevice(os="iosxe")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "interface" in result.data["learn"]
        assert "bgp" not in result.data["learn"]
        # AttributeError is silent — no warning for the skipped feature.
        assert not any("bgp" in w for w in result.warnings)

    def test_no_features_discovered_is_error_with_warning(self, monkeypatch):
        ops = FakeOpsNamespace({})
        _patch_genie_ops(monkeypatch, lookup=FakeLookup(ops), features={})
        d = FakePyatsDevice(os="iosxe")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"learn": {}}
        assert any("no Ops feature" in w for w in result.warnings)

    def test_lookup_from_device_failure_is_error(self, monkeypatch):
        _patch_genie_ops(monkeypatch, from_device_exc=RuntimeError("lookup boom"))
        d = FakePyatsDevice(os="iosxe")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"learn": {}}
        assert any("Lookup.from_device failed" in w for w in result.warnings)

    def test_genie_ops_import_failure_is_error(self, monkeypatch):
        # If the genie.ops.utils import itself fails (e.g. genie not installed
        # on the worker), _capture_learn returns an empty learn with a warning
        # and the capture is an error (no data).
        import sys

        # Ensure the real genie.ops.utils is absent so the lazy import fails.
        for mod in ("genie", "genie.libs", "genie.libs.ops", "genie.ops", "genie.ops.utils"):
            monkeypatch.setitem(sys.modules, mod, None)
        d = FakePyatsDevice(os="iosxe")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_ERROR
        assert result.data == {"learn": {}}
        assert any("import failed" in w for w in result.warnings)

    def test_feature_with_no_payload_is_warning_and_omitted(self, monkeypatch):
        # An Ops feature whose .learn() succeeds but produces no .ops/.data
        # payload is recorded as a warning and omitted (not an empty entry).
        class _NonePayloadOps(FakeOpsInstance):
            @property
            def ops(self):
                return None

        class _NonePayloadFactory(FakeOpsFactory):
            def __call__(self, device):
                return _NonePayloadOps(None)

        features = {
            "interface": FakeOpsFactory({"ok": True}),
            "empty": _NonePayloadFactory(None),
        }
        ops = FakeOpsNamespace(features)
        _patch_genie_ops(monkeypatch, lookup=FakeLookup(ops), features=features)
        d = FakePyatsDevice(os="iosxe")
        result = capture_snapshot(d, kind=SnapshotKindChoices.KIND_LEARN)
        assert result.status == SnapshotStatusChoices.STATUS_SUCCESS
        assert "interface" in result.data["learn"]
        assert "empty" not in result.data["learn"]
        assert any("empty" in w and "no payload" in w for w in result.warnings)
