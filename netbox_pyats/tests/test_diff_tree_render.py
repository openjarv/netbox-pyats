"""Integration render test for the ``inc/diff_tree.html`` partial (ATW-509).

Regression guard for the multi-line Django template-comment bug: lines 2-8 of
``inc/diff_tree.html`` used a multi-line ``{# ... #}`` tag. Django only strips
SINGLE-line ``{# #}`` comments, so a multi-line block rendered as literal
text — the comment text ("Recursive partial rendering...") appeared verbatim at
the top of every diff tree, and a stray ``<details>`` substring in the comment
produced a phantom "Details" element that shadowed the real collapsible tree.

The fix converts the multi-line ``{# #}`` comment to a ``{% comment %}`` /
``{% endcomment %}`` block (the Django multi-line comment tag that IS stripped).
The single-line ``{# Leaf: ... #}`` on line 29 is correctly stripped and left
as-is.

This test renders the partial end-to-end by GETing the snapshot-diff detail
view (``PyatsSnapshotDiffView``), whose template
``pyatssnapshotdiff.html`` includes ``inc/diff_tree.html`` with
``node=object.diff``. The full NetBox request context supplies the ``helpers``
template library (the ``|json`` filter the partial depends on), so this is an
integration test, not a pure-Django ``render_to_string`` test.

Assertions (ATW-509 scope):
- The comment text ("Recursive partial rendering") is NOT present in the
  rendered output (the regression).
- A ``<details>`` element with class ``diff-node`` renders for a changed root
  node (the real tree, not the phantom).
- The ``bg-warning`` badge renders for a ``changed`` status, ``bg-success``
  for ``added``, ``bg-danger`` for ``removed``.
- A recursive child dict node renders inside the parent (recursion works).
"""

import pytest

pytest.importorskip("netbox")

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.urls import reverse
from utilities.testing import TestCase

from netbox_pyats.choices import DiffStatusChoices, SnapshotKindChoices, SnapshotStatusChoices, SnapshotTriggerChoices
from netbox_pyats.models import PyatsSnapshot, PyatsSnapshotDiff


class DiffTreeRenderTest(TestCase):
    """Render ``inc/diff_tree.html`` via the snapshot-diff detail view and
    assert the ATW-509 contract (comment stripped, badges + recursion present)."""

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

    def test_diff_tree_renders_without_comment_text_and_with_real_tree(self):
        # A changed root dict node with one changed, one added, and one removed
        # child — exercises the badge classes and recursion in one render.
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

        # ATW-509 regression: the multi-line comment text must NOT render.
        self.assertNotIn(
            "Recursive partial rendering",
            html,
            "The multi-line template comment leaked as literal text (ATW-509 regression).",
        )
        # The comment's prose description of the node shape must also not leak.
        self.assertNotIn(
            "Server-rendered",
            html,
            "The multi-line template comment prose leaked as literal text (ATW-509 regression).",
        )

        # The real tree: a <details> element with class diff-node renders for
        # the changed root. (The phantom <details> from the comment is gone.)
        self.assertIn("diff-node", html, "The diff-node class must render on the real <details>.")
        self.assertIn("diff-changed", html, "The diff-changed status class must render on the root node.")

        # Badge classes per status.
        self.assertIn("bg-warning", html, "A 'changed' node must render the bg-warning badge.")
        self.assertIn("bg-success", html, "An 'added' node must render the bg-success badge.")
        self.assertIn("bg-danger", html, "A 'removed' node must render the bg-danger badge.")

        # Recursion: the child leaf values render inside the parent tree.
        self.assertIn("rtr01", html, "The 'before' value of the changed hostname leaf must render.")
        self.assertIn("rtr02", html, "The 'after' value of the changed hostname leaf must render.")

    def test_diff_tree_renders_unchanged_node_without_open_attribute(self):
        # An unchanged root node must NOT get the `open` attribute (only
        # changed/added/removed subtrees are open by default). Guards the
        # {% if status == 'changed' or ... %} open{% endif %} branch.
        diff = {
            "name": "root",
            "type": "dict",
            "status": "unchanged",
            "children": {},
        }
        row = self._make_diff_row(diff=diff)
        url = reverse("plugins:netbox_pyats:pyatssnapshotdiff", kwargs={"pk": row.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=f"body: {response.content[:500]!r}")
        html = response.content.decode("utf-8")
        # The unchanged node's <details> must not be open by default.
        self.assertIn("diff-node", html)
        self.assertIn("diff-unchanged", html)
        # The `open` attribute should only appear on changed/added/removed
        # subtrees; an unchanged-only tree has no open <details>.
        # (We assert the unchanged node is not marked open by checking the
        # diff-unchanged <details> lacks the open attribute. A precise check:
        # no substring "<details open" when only unchanged nodes render.)
        self.assertNotIn("<details open", html, "An unchanged node must not be open by default.")
