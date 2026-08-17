# ADR-0007: Device-page tab via `register_model_view` + `ObjectView` + `ViewTab`

Date: 2026-07-31
Status: Accepted
Supersedes: —
Superseded by: —
Amends: [ADR-0001](0001-plugin-layout.md) §34 (template_content.py description)

## Context

ADR-0001 locked the package layout and recorded `template_content.py` as
"PluginTemplateExtension → Device page 'PyATS' tab." The original
implementation registered the extension via `right_page()`, which injects a
card into the **right-hand column** of the NetBox Device detail page. As the
panel grew (capture form, recent snapshots, diff picker, compliance picker,
multiple history tables) the right-column card became crowded and crowded the
core device layout on every device page load.

The board (via [ATW-393](/ATW/issues/ATW-393)) asked the plugin to own a
**dedicated tab** on the device page (alongside Inventory, Status, etc.),
giving the PyATS UI room to grow without crowding core device layout.

The approved plan considered two primitives:

- **`full_width_page()`** — a `PluginTemplateExtension` method that renders a
  full-width band *beneath* the two-column device layout. Verified against
  NetBox 4.6.5 source: `netbox/ui/layout.py` `SimpleLayout` places
  `PluginContentPanel('full_width_page')` in a second `Row` under the
  `left_page`/`right_page` columns. `DeviceView` (`dcim/views.py:2614`) uses
  `SimpleLayout` with no `tab`. So `full_width_page` is a bottom full-width
  row, **not a tab** — it does not deliver the board's stated goal.
- **`register_model_view` + `ObjectView` + `ViewTab`** — the idiomatic NetBox
  way to register a real device-page tab (Inventory, Status, Config Context,
  Render Config all use this path). `utilities/views.py:354`
  `register_model_view` registers an `ObjectView` subclass at
  `/dcim/devices/<id>/<path>/` with a `ViewTab` carrying `label`/`weight`/
  `permission`. This is a true nav-tab with its own URL.

The CTO decision ([ATW-395](/ATW/issues/ATW-395)) chose Option B
(`register_model_view`) because it delivers the board's stated goal, is the
plan's own pre-authorized fallback ("If `full_width_page` is not the right
primitive in 4.6, fall back to the documented NetBox 'object tab' registration"),
and is a small, idiomatic, upgrade-safe surface.

## Decision

Replace the `PluginTemplateExtension` (`right_page` card in
`template_content.py`) with a real NetBox object tab registered via
`register_model_view(Device, 'pyats', path='pyats')` + a GET-only
`ObjectView` subclass with a `ViewTab`.

Concretely:

1. **`views.py`**: new `DevicePyATSTabView(generic.ObjectView)` registered via
   `@register_model_view(Device, 'pyats', path='pyats')`. GET-only;
   `queryset = Device.objects.all()`; `base_template = 'dcim/device/base.html'`;
   `template_name = 'netbox_pyats/inc/device_tab.html'`;
   `tab = ViewTab(label='PyATS', weight=550,
   permission='netbox_pyats.view_pyatssnapshot')`. The context-building logic
   (snapshots, diffs, golden configs, compliance runs, platform support, diff
   grouping) moves from the old `DevicePyATSPanel.right_page` into
   `get_extra_context`. The helper functions (`_capture_url_for_device`,
   `_diff_url_for_device`, `_compliance_url_for_device`,
   `_snapshot_list_url_for_device`, `_parse_url_for_device`,
   `_group_snapshots_by_kind`) move from `template_content.py` to `views.py`.
2. **`template_content.py`**: **deleted**. The tab view owns the full UI; no
   `PluginTemplateExtension` is needed. No double-render (the right-column
   panel is gone).
3. **`__init__.py`**: `template_extensions` registration removed (the plugin
   no longer uses a template extension).
4. **Template rename**: `inc/device_panel.html` → `inc/device_tab.html`.
   The template now `{% extends base_template %}` with `{% block content %}`
   (the tab provides the page container via `dcim/device/base.html`). The
   outer `<div class="card">…<h5 class="card-header">` chrome is removed. The
   inner content (forms + history tables) is preserved 1:1 so no operator
   workflow changes.
5. **No new models, migrations, or JS.** The existing
   `device_capture`/`device_diff`/`device_compliance`/`device_parse`/
   `device_refresh_parser_catalog` POST/GET endpoints stay unchanged and
   redirect back to `device.get_absolute_url()`; the tab re-renders on the
   next GET (ADR-0001 §4 no-JS rule stays in force).
6. **Tab weight 550** sits just above Inventory Items (590) so PyATS appears
   near the top of the tab list, after the main detail but before the
   component tabs.
7. **Tab permission** `netbox_pyats.view_pyatssnapshot` hides the tab for
   users without plugin view perms (matches NetBox convention — see
   `DeviceInventoryView` `permission='dcim.view_inventoryitem'`).

## Consequences

- **Positive:** the PyATS UI lives in a true device-page tab with its own URL
  (`/dcim/devices/<id>/pyats/`), decluttering the core device layout and
  giving the plugin room to grow (parse sub-tab, future features) without
  crowding the right column.
- **Positive:** upgrade-safe — `register_model_view` + `ObjectView` +
  `ViewTab` is the documented NetBox tab API (present in NetBox 3.5+ through
  4.6).
- **Positive:** no double-render — the old right-column panel is removed; the
  tab view is the single render path.
- **Negative:** one new view + one new URL (`register_model_view(Device,
  'pyats', path='pyats')`) — within the locked package layout (no new
  top-level package, no new model, no migration).
- **Negative:** the visual container changes (card chrome removed); the tab
  provides the container via `dcim/device/base.html`. QA verifies the tab
  looks right and forms/tables still align.
- **Negative:** any operator-doc screenshot referencing the old right-column
  card will be stale; screenshot refresh is a follow-up (out of scope).

## Alternatives considered

- **`full_width_page()` (Option A).** Rejected: verified to be a bottom
  full-width row, not a tab. Does not deliver the board's stated goal and
  would need a follow-up conversion to a real tab anyway.
- **Keep `right_page()` and shrink the card.** Rejected: the card is already
  dense and will only grow; a tab is the better UX and the board asked for it.
- **Monkey-patch core device template to inject a tab.** Rejected: fragile,
  breaks on NetBox upgrades, and `register_model_view` is the documented path.

## References

- [ATW-393](/ATW/issues/ATW-393) (Device page UX — plan + delegation)
- [ATW-394](/ATW/issues/ATW-394) (implementation)
- [ATW-395](/ATW/issues/ATW-395) (CTO decision: Option B)
- [ADR-0001](0001-plugin-layout.md) (plugin layout; §4 no-JS rule; §16
  layout lock)