"""Tests for :mod:`netbox_pyats.diff`.

Pure-Python: exercises the structured diff engine against plain dicts (no
NetBox, no RQ, no Genie). Covers:

- Added/removed/changed/unchanged leaves at every level.
- Recursive dict nesting (a dict child of a dict child).
- Positional list diffing (common length, longer after, longer before).
- Empty inputs → ``status="empty"``, neutral badge.
- Both-None inputs → ``status="empty"``.
- Non-dict top-level inputs → ``status="error"`` with a warning.
- Summary counts match the tree.
- ``DiffResult.size_bytes`` derives from the JSON-serialized ``diff``.
- ``has_changes`` is False for an all-unchanged diff and True otherwise.
"""

import json

import pytest

pytest.importorskip("pyats")  # keep parity with the other pure-Python test files

from netbox_pyats.choices import DiffStatusChoices
from netbox_pyats.diff import diff_snapshots


class TestAddedRemovedChanged:
    def test_added_key_is_marked_added(self):
        r = diff_snapshots({"a": 1}, {"a": 1, "b": 2})
        assert r.status == DiffStatusChoices.STATUS_SUCCESS
        assert r.summary == {"added": 1, "removed": 0, "changed": 0, "unchanged": 1}
        b_node = r.diff["children"]["b"]
        assert b_node["status"] == "added"
        assert b_node["after"] == 2

    def test_removed_key_is_marked_removed(self):
        r = diff_snapshots({"a": 1, "b": 2}, {"a": 1})
        assert r.summary == {"added": 0, "removed": 1, "changed": 0, "unchanged": 1}
        b_node = r.diff["children"]["b"]
        assert b_node["status"] == "removed"
        assert b_node["before"] == 2

    def test_changed_scalar_is_marked_changed_with_both_values(self):
        r = diff_snapshots({"a": 1}, {"a": 2})
        assert r.summary["changed"] == 1
        a_node = r.diff["children"]["a"]
        assert a_node["status"] == "changed"
        assert a_node["before"] == 1
        assert a_node["after"] == 2

    def test_unchanged_scalar_is_marked_unchanged(self):
        r = diff_snapshots({"a": 1}, {"a": 1})
        assert r.summary == {"added": 0, "removed": 0, "changed": 0, "unchanged": 1}
        a_node = r.diff["children"]["a"]
        assert a_node["status"] == "unchanged"
        assert a_node["value"] == 1

    def test_mixed_type_change_is_marked_changed(self):
        r = diff_snapshots({"a": "1"}, {"a": 1})
        # Different types, unequal values → changed with a "mixed" type tag.
        a_node = r.diff["children"]["a"]
        assert a_node["status"] == "changed"
        assert a_node["before"] == "1"
        assert a_node["after"] == 1
        assert a_node["type"] == "mixed"


class TestNestedDicts:
    def test_nested_dict_change_propagates_to_root_status(self):
        before = {"config": {"hostname": "rtr01", "interfaces": {"Gig0": {"ip": "10.0.0.1"}}}}
        after = {"config": {"hostname": "rtr01", "interfaces": {"Gig0": {"ip": "10.0.0.2"}}}}
        r = diff_snapshots(before, after)
        assert r.status == DiffStatusChoices.STATUS_SUCCESS
        # Only one leaf changed: the IP on Gig0.
        assert r.summary == {"added": 0, "removed": 0, "changed": 1, "unchanged": 1}
        # The root and the "config" container are both "changed" (propagated),
        # but "hostname" under config is unchanged.
        assert r.diff["status"] == "changed"
        config_node = r.diff["children"]["config"]
        assert config_node["status"] == "changed"
        assert config_node["type"] == "dict"
        # hostname is unchanged
        assert config_node["children"]["hostname"]["status"] == "unchanged"
        # The changed leaf is at config > interfaces > Gig0 > ip
        gig0_node = config_node["children"]["interfaces"]["children"]["Gig0"]
        assert gig0_node["status"] == "changed"
        assert gig0_node["children"]["ip"]["before"] == "10.0.0.1"
        assert gig0_node["children"]["ip"]["after"] == "10.0.0.2"

    def test_unchanged_nested_dict_has_unchanged_root(self):
        before = {"config": {"hostname": "rtr01"}}
        after = {"config": {"hostname": "rtr01"}}
        r = diff_snapshots(before, after)
        assert r.diff["status"] == "unchanged"
        assert r.summary == {"added": 0, "removed": 0, "changed": 0, "unchanged": 1}
        assert r.has_changes is False


class TestLists:
    def test_common_length_lists_recurse_per_index(self):
        r = diff_snapshots({"vlans": [10, 20, 30]}, {"vlans": [10, 21, 30]})
        assert r.summary["changed"] == 1
        assert r.summary["unchanged"] == 2
        vlans = r.diff["children"]["vlans"]
        assert vlans["type"] == "list"
        assert vlans["children"]["1"]["status"] == "changed"
        assert vlans["children"]["1"]["before"] == 20
        assert vlans["children"]["1"]["after"] == 21

    def test_longer_after_list_appends_added_entries(self):
        r = diff_snapshots({"vlans": [10]}, {"vlans": [10, 20, 30]})
        assert r.summary["added"] == 2
        assert r.summary["unchanged"] == 1
        vlans = r.diff["children"]["vlans"]
        assert vlans["children"]["1"]["status"] == "added"
        assert vlans["children"]["1"]["after"] == 20
        assert vlans["children"]["2"]["status"] == "added"

    def test_shorter_after_list_appends_removed_entries(self):
        r = diff_snapshots({"vlans": [10, 20, 30]}, {"vlans": [10]})
        assert r.summary["removed"] == 2
        assert r.summary["unchanged"] == 1
        vlans = r.diff["children"]["vlans"]
        assert vlans["children"]["1"]["status"] == "removed"
        assert vlans["children"]["1"]["before"] == 20


class TestEmptyAndError:
    def test_both_empty_dicts_yield_empty_status(self):
        r = diff_snapshots({}, {})
        assert r.status == DiffStatusChoices.STATUS_EMPTY
        assert r.summary == {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
        assert r.has_changes is False

    def test_both_none_inputs_yield_empty_status(self):
        r = diff_snapshots(None, None)
        assert r.status == DiffStatusChoices.STATUS_EMPTY

    def test_one_none_one_populated_treats_none_as_empty(self):
        r = diff_snapshots(None, {"a": 1})
        assert r.status == DiffStatusChoices.STATUS_SUCCESS
        assert r.summary["added"] == 1
        assert r.diff["children"]["a"]["status"] == "added"

    def test_non_dict_top_level_inputs_yield_error(self):
        r = diff_snapshots([1, 2, 3], {"a": 1})  # type: ignore[arg-type]
        assert r.status == DiffStatusChoices.STATUS_ERROR
        assert r.diff == {}
        assert any("must be dicts" in w for w in r.warnings)


class TestDiffResultSizeBytes:
    def test_error_diff_is_zero_bytes(self):
        # Error diffs carry no tree (diff={}), so size_bytes is 0.
        r = diff_snapshots([1, 2, 3], {"a": 1})  # type: ignore[arg-type]
        assert r.status == DiffStatusChoices.STATUS_ERROR
        assert r.size_bytes == 0

    def test_size_bytes_matches_json_length(self):
        r = diff_snapshots({"a": 1}, {"a": 2})
        expected = len(json.dumps(r.diff, default=str).encode("utf-8"))
        assert r.size_bytes == expected
        assert r.size_bytes > 0

    def test_empty_inputs_diff_still_has_a_tree_so_nonzero_bytes(self):
        # Empty inputs produce a minimal tree node (status="empty"), so
        # size_bytes reflects that tree — it is not zero. This is distinct from
        # the error path, where diff={} and size_bytes is 0.
        r = diff_snapshots({}, {})
        assert r.status == DiffStatusChoices.STATUS_EMPTY
        assert r.size_bytes > 0


class TestJsonSerializable:
    def test_diff_tree_is_json_serializable(self):
        """The whole diff tree must round-trip through json.dumps (it's JSONB)."""
        before = {"config": {"hostname": "rtr01", "vlans": [10, 20]}, "state": {"version": "16.12"}}
        after = {"config": {"hostname": "rtr02", "vlans": [10, 20, 30]}, "state": {"version": "16.12"}}
        r = diff_snapshots(before, after)
        blob = json.dumps(r.diff, default=str)
        reloaded = json.loads(blob)
        assert reloaded["status"] == "changed"
        assert reloaded["children"]["config"]["children"]["hostname"]["after"] == "rtr02"
        # Summary is also JSON-serializable.
        json.dumps(r.summary)


class TestRealisticSnapshot:
    """Diff two Genie-parser-shaped snapshot payloads end-to-end."""

    def test_full_snapshot_diff_summary_counts(self):
        before = {
            "config": {"hostname": "rtr01", "interfaces": {"Gig0": {"ip": "10.0.0.1"}}},
            "state": {
                "show version": {"version": "16.12"},
                "show inventory": {"chassis": "C9300"},
                "show ip interface brief": {"Gig0": {"ip": "10.0.0.1"}},
            },
        }
        after = {
            "config": {"hostname": "rtr02", "interfaces": {"Gig0": {"ip": "10.0.0.1"}}},
            "state": {
                "show version": {"version": "16.13"},
                "show inventory": {"chassis": "C9300"},
                "show ip interface brief": {"Gig0": {"ip": "10.0.0.1"}},
            },
        }
        r = diff_snapshots(before, after)
        assert r.status == DiffStatusChoices.STATUS_SUCCESS
        # Two leaves changed: config.hostname and state["show version"].version.
        # Three leaves are unchanged: config.interfaces.Gig0.ip,
        # state["show inventory"].chassis, state["show ip interface brief"].Gig0.ip.
        assert r.summary == {"added": 0, "removed": 0, "changed": 2, "unchanged": 3}
        assert r.has_changes is True
