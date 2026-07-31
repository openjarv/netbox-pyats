"""Structural guard for the device-page PyATS tab registration (ATW-393 / ADR-0007).

Pure-Python (AST-only, no ``netbox`` import): asserts that

- ``DevicePyATSTabView`` is registered via ``register_model_view(Device, 'pyats',
  path='pyats')`` in ``views.py`` (a real NetBox object tab, not a
  ``PluginTemplateExtension`` right-column card).
- ``template_content.py`` is gone (the old ``PluginTemplateExtension`` is
  removed; the tab view owns the full UI).
- ``__init__.py`` no longer declares ``template_extensions``.
- The rendered template is ``inc/device_tab.html`` (not the retired
  ``inc/device_panel.html``) and extends the device base template with no
  card chrome (the tab provides the container).

This is the regression guard for the ADR-0007 move from a right-column card
to a dedicated device-page tab.
"""

import ast
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
_VIEWS = _PKG / "views.py"
_INIT = _PKG / "__init__.py"
_TEMPLATES = _PKG / "templates" / "netbox_pyats"
_TEMPLATE_CONTENT = _PKG / "template_content.py"


def _read_source(path: Path) -> ast.Module:
    return ast.parse(path.read_text())


def test_template_content_module_removed():
    """ADR-0007: the PluginTemplateExtension module is deleted."""
    assert not _TEMPLATE_CONTENT.exists(), "template_content.py was removed in ADR-0007"


def test_device_tab_view_registered_with_register_model_view():
    """DevicePyATSTabView must be decorated with register_model_view(Device, 'pyats')."""
    src = _VIEWS.read_text()
    tree = _read_source(_VIEWS)
    cls = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "DevicePyATSTabView")
    decorators = cls.decorator_list
    assert decorators, "DevicePyATSTabView must have a register_model_view decorator"
    # The decorator is register_model_view(Device, 'pyats', path='pyats').
    # Check the source contains the call with 'pyats' as the name arg.
    assert any(
        (isinstance(d, ast.Call) and getattr(d.func, "id", "") == "register_model_view") for d in decorators
    ), "DevicePyATSTabView must be decorated with register_model_view"
    assert "'pyats'" in src or '"pyats"' in src, "register_model_view name must be 'pyats'"


def test_device_tab_view_uses_object_view_base():
    """DevicePyATSTabView must subclass generic.ObjectView."""
    tree = _read_source(_VIEWS)
    cls = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "DevicePyATSTabView")
    bases = [getattr(b, "attr", getattr(b, "id", "")) for b in cls.bases]
    assert any("ObjectView" in b for b in bases), "DevicePyATSTabView must subclass generic.ObjectView"


def test_device_tab_view_has_viewtab():
    """DevicePyATSTabView must declare a ViewTab with label='PyATS'."""
    src = _VIEWS.read_text()
    assert "ViewTab(" in src, "DevicePyATSTabView must declare a ViewTab"
    assert "'PyATS'" in src or '"PyATS"' in src, "ViewTab label must be 'PyATS'"


def test_init_does_not_declare_template_extensions():
    """ADR-0007: __init__.py must not register template_extensions."""
    src = _INIT.read_text()
    assert "template_extensions" not in src, "template_extensions registration removed in ADR-0007"


def test_render_template_is_device_tab():
    """The view's template_name must reference inc/device_tab.html."""
    src = _VIEWS.read_text()
    assert "netbox_pyats/inc/device_tab.html" in src
    assert "netbox_pyats/inc/device_panel.html" not in src


def test_device_tab_template_exists_and_panel_template_gone():
    assert (_TEMPLATES / "inc" / "device_tab.html").exists(), "device_tab.html must exist"
    assert not (
        _TEMPLATES / "inc" / "device_panel.html"
    ).exists(), "device_panel.html was renamed to device_tab.html (ADR-0007)"


def test_device_tab_template_extends_device_base():
    """ADR-0007: the tab template extends the device base template."""
    tmpl = (_TEMPLATES / "inc" / "device_tab.html").read_text()
    assert (
        "extends base_template" in tmpl or "extends 'dcim/device/base.html'" in tmpl
    ), "device_tab.html must extend base_template (dcim/device/base.html)"


def test_device_tab_template_has_no_card_chrome():
    """ADR-0007: the tab provides the container, so card chrome is removed."""
    tmpl = (_TEMPLATES / "inc" / "device_tab.html").read_text()
    assert 'class="card"' not in tmpl, 'card chrome (<div class="card">) removed in ADR-0007'
    assert "card-header" not in tmpl, "card-header chrome removed in ADR-0007"


def test_get_extra_context_injects_base_template():
    """ATW-409 regression guard: DevicePyATSTabView.get_extra_context must
    include ``base_template`` in the dict it returns.

    NetBox's ``ObjectView.get`` only merges the ``get_extra_context`` return
    value into the template context — class attributes are NOT auto-injected.
    The tab template does ``{% extends base_template %}``, so a missing key
    raises ``TemplateSyntaxError`` -> HTTP 500 (the PR #86 regression). The
    pre-existing render test in ``test_diff_form_qa.py`` masked the bug by
    passing ``base_template`` directly into the render context; this structural
    guard inspects the source so it fails if the one-line fix is reverted.
    Pure-Python (AST-only), no NetBox/DB dependency.
    """
    tree = ast.parse(_VIEWS.read_text())
    cls = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "DevicePyATSTabView")
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "get_extra_context")
    return_node = next(
        node for node in ast.walk(method) if isinstance(node, ast.Return) and node.value is not None
    )
    value = return_node.value
    assert isinstance(value, ast.Dict), "get_extra_context must return a dict literal"
    key_strs = [k.value for k in value.keys if isinstance(k, ast.Constant)]
    assert "base_template" in key_strs, (
        "get_extra_context must inject 'base_template' into its returned dict "
        "(ATW-409: ObjectView.get does not merge class attributes into the context)"
    )
