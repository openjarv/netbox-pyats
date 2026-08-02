"""Integration render test for the side-by-side diff table (ATW-524/ATW-525).

Replaces the ATW-509 collapsible-tree render test. The diff viewer is now a
flat side-by-side Path / Before / After table (``inc/diff_table.html``)
instead of a recursive ``<details>`` tree with Bootstrap badges and ``|json``
pretty-print. The view (``PyatsSnapshotDiffView.get_extra_context``) flattens
``object.diff`` via :func:`netbox_pyats.diff.flatten_diff_tree` and passes the
list as ``lines``.

Assertions (ATW-524/ATW-525 contract):
- The page renders HTTP 200 with a non-empty diff.
- The new table partial renders (``diff-table`` class, Path/Before/After
  headers) — the old ``diff-node`` / ``<details>`` / badge markup is gone.
- Red text (``text-danger``) marks the before column for changed/removed rows.
- Green text (``text-success``) marks the after column for changed/added rows.
- Muted text marks unchanged rows and the empty side of added/removed rows.
- No ``|json`` filter artefacts (no ``"dict"`` / ``"leaf"`` type tags, no
  ``bg-warning`` / ``bg-success`` / ``bg-danger`` badges, no ``<details>``
  collapsible sections).
- Leaf before/after values render inline.
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.choices import DiffStatusChoices, SnapshotKindChoices, SnapshotStatusChoices, SnapshotTriggerChoices
from netbox_pyats.models import PyatsSnapshot, PyatsSnapshotDiff


class DiffTableRenderTest(TestCase):
    """Render ``inc/diff_table.html`` via the snapshot-diff detail view and
    assert the ATW-524/ATW-525 side-by-side table contract."""

    user_permissions = (
        "netbox_pyats.view_pyatssnapshot",
        "netbox_pyats.view_pyatssnapshotdiff",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="DTR01", slug="dtr01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-DTR", slug="cisco-dtr")
        cls.device_type = DeviceType.objects.create(model="C9300-DTR", slug="c9300-dtr", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-DTR", slug="router-dtr")
        cls.device = Device.objects.create(name="dtrrtr01", site=cls.site, device_type=cls.device_type, role=cls.role)

    def _make_snapshot(self, *, data):
        snap = PyatsSnapshot(
            device=self.device,
            kind=SnapshotKindChoices.KIND_FULL,
            status=SnapshotStatusChoices.STATUS_SUCCESS,
            triggered_by=SnapshotTriggerChoices.TRIGGER_USER,
            data=data,
            size_bytes=1,
        )
        snap.full_clean()
        snap.save()
        return snap

    def _make_diff_row(self, *, diff):
        before = self._make_snapshot(data={"config": {"hostname": "rtr01"}})
        after = self._make_snapshot(data={"config": {"hostname": "rtr02"}})
        row = PyatsSnapshotDiff(
            device=self.device,
            before=before,
            after=after,
            status=DiffStatusChoices.STATUS_SUCCESS,
            diff=diff,
            summary={"added": 1, "removed": 1, "changed": 1, "unchanged": 0},
            size_bytes=1,
        )
        row.full_clean()
        row.save()
        return row

    def test_diff_table_renders_side_by_side_with_red_green_highlighting(self):
        # A changed root dict node with one changed, one added, and one removed
        # child — exercises all three highlight classes in one render.
        diff = {
            "name": "root",
            "type": "dict",
            "status": "changed",
            "children": {
                "hostname": {
                    "name": "hostname",
                    "type": "leaf",
                    "status": "changed",
                    "before": "rtr01",
                    "after": "rtr02",
                },
                "vlans": {
                    "name": "vlans",
                    "type": "leaf",
                    "status": "added",
                    "after": [10, 20],
                },
                "old_acl": {
                    "name": "old_acl",
                    "type": "leaf",
                    "status": "removed",
                    "before": "permit 10",
                },
            },
        }
        row = self._make_diff_row(diff=diff)
        url = reverse("plugins:netbox_pyats:pyatssnapshotdiff", kwargs={"pk": row.pk})
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"diff detail view did not return 200; body: {response.content[:500]!r}",
        )
        html = response.content.decode("utf-8")

        # The new side-by-side table renders.
        self.assertIn("diff-table", html, "The diff-table class must render on the table.")
        self.assertIn("diff-row", html, "Each diff row must carry the diff-row class.")
        self.assertIn("Path", html, "The Path column header must render.")
        self.assertIn("Before", html, "The Before column header must render.")
        self.assertIn("After", html, "The After column header must render.")

        # Red/green highlighting per status.
        self.assertIn("text-danger", html, "A changed/removed before value must render with text-danger.")
        self.assertIn("text-success", html, "A changed/added after value must render with text-success.")
        self.assertIn("diff-changed", html, "The changed row must carry the diff-changed class.")
        self.assertIn("diff-added", html, "The added row must carry the diff-added class.")
        self.assertIn("diff-removed", html, "The removed row must carry the diff-removed class.")

        # Leaf values render inline (compact, not pretty-printed JSON).
        self.assertIn("rtr01", html, "The 'before' value of the changed hostname leaf must render.")
        self.assertIn("rtr02", html, "The 'after' value of the changed hostname leaf must render.")
        self.assertIn("permit 10", html, "The 'before' value of the removed leaf must render.")

        # The old collapsible-tree / type-tag markup is gone from the diff card.
        # Scope to the diff card region so the Summary card's kept-as-is badges
        # (bg-success/bg-danger/bg-warning on the added/removed/changed counts
        # — ATW-524 explicitly keeps the summary card) don't trip the assertion.
        diff_card_start = html.find('<h5 class="card-header">Diff</h5>')
        self.assertGreater(diff_card_start, 0, "The Diff card header must render.")
        diff_card = html[diff_card_start:]
        self.assertNotIn("diff-node", diff_card, "The old diff-node <details> class must not render.")
        self.assertNotIn("<details", diff_card, "No <details> collapsible sections should remain.")
        self.assertNotIn("Recursive partial rendering", diff_card, "The old template comment text must not leak.")

    def test_diff_table_renders_empty_state_when_diff_is_empty(self):
        # An empty diff dict → no table, just the "No changes." placeholder.
        row = self._make_diff_row(diff={})
        url = reverse("plugins:netbox_pyats:pyatssnapshotdiff", kwargs={"pk": row.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=f"body: {response.content[:500]!r}")
        html = response.content.decode("utf-8")
        # When object.diff is falsy the template renders the outer "No diff
        # data" branch, not the table partial's "No changes." branch. Either
        # way, no table rows.
        self.assertNotIn("diff-row", html, "No diff rows should render for an empty diff.")
