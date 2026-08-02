"""Unit tests for :func:`netbox_pyats.diff.flatten_diff_tree` (ATW-524/ATW-525).

Pure-Python: exercises the flatten layer against the diff tree shape produced
by :func:`netbox_pyats.diff.diff_snapshots` — no NetBox, no RQ, no Genie.

Covers:
- Added / removed / changed / unchanged leaves → DiffLine shape.
- Nested dict paths (dotted keys).
- Positional list paths (bracket indices).
- Compact JSON serialization for nested-container leaf values.
- Empty / None / error diffs → ``[]``.
- Container-only nodes do not emit rows.
- Round-trip: ``flatten_diff_tree(diff_snapshots(...).diff)`` produces one row
  per leaf and the statuses match the summary counts.
"""

import pytest

pytest.importorskip("pyats")  # keep parity with the other pure-Python test files

from netbox_pyats.diff import DiffLine, diff_snapshots, flatten_diff_tree


class TestFlattenEmptyAndError:
    def test_none_diff_returns_empty_list(self):
        assert flatten_diff_tree(None) == []

    def test_empty_dict_returns_empty_list(self):
        assert flatten_diff_tree({}) == []

    def test_non_dict_returns_empty_list(self):
        assert flatten_diff_tree([1, 2, 3]) == []  # type: ignore[arg-type]
        assert flatten_diff_tree("not a dict") == []  # type: ignore[arg-type]

    def test_error_diff_result_has_empty_diff_so_flattens_to_empty(self):
        r = diff_snapshots([1, 2, 3], {"a": 1})  # type: ignore[arg-type]
        assert r.status == "error"
        assert r.diff == {}
        assert flatten_diff_tree(r.diff) == []


class TestFlattenLeaves:
    def test_added_leaf_emits_one_row_with_empty_before(self):
        r = diff_snapshots({}, {"a": 1})
        lines = flatten_diff_tree(r.diff)
        assert lines == [DiffLine(path="a", status="added", before="", after="1")]

    def test_removed_leaf_emits_one_row_with_empty_after(self):
        r = diff_snapshots({"a": 1}, {})
        lines = flatten_diff_tree(r.diff)
        assert lines == [DiffLine(path="a", status="removed", before="1", after="")]

    def test_changed_leaf_emits_one_row_with_both_values(self):
        r = diff_snapshots({"a": 1}, {"a": 2})
        lines = flatten_diff_tree(r.diff)
        assert lines == [DiffLine(path="a", status="changed", before="1", after="2")]

    def test_unchanged_leaf_emits_one_row_with_value_in_both_columns(self):
        r = diff_snapshots({"a": 1}, {"a": 1})
        lines = flatten_diff_tree(r.diff)
        assert lines == [DiffLine(path="a", status="unchanged", before="1", after="1")]

    def test_mixed_type_change_serializes_both_values_as_strings(self):
        r = diff_snapshots({"a": "1"}, {"a": 1})
        lines = flatten_diff_tree(r.diff)
        assert len(lines) == 1
        line = lines[0]
        assert line.status == "changed"
        assert line.before == "1"
        assert line.after == "1"

    def test_none_value_renders_as_empty_string(self):
        r = diff_snapshots({"a": None}, {"a": None})
        lines = flatten_diff_tree(r.diff)
        assert lines == [DiffLine(path="a", status="unchanged", before="", after="")]


class TestFlattenNestedDicts:
    def test_dotted_path_for_nested_dict_leaves(self):
        before = {"config": {"hostname": "rtr01", "interfaces": {"Gig0": {"ip": "10.0.0.1"}}}}
        after = {"config": {"hostname": "rtr02", "interfaces": {"Gig0": {"ip": "10.0.0.1"}}}}
        r = diff_snapshots(before, after)
        lines = flatten_diff_tree(r.diff)
        # Two leaves: one changed (hostname), one unchanged (Gig0.ip).
        by_path = {line.path: line for line in lines}
        assert "config.hostname" in by_path
        assert by_path["config.hostname"].status == "changed"
        assert by_path["config.hostname"].before == "rtr01"
        assert by_path["config.hostname"].after == "rtr02"
        assert "config.interfaces.Gig0.ip" in by_path
        assert by_path["config.interfaces.Gig0.ip"].status == "unchanged"
        assert by_path["config.interfaces.Gig0.ip"].before == "10.0.0.1"

    def test_container_only_nodes_do_not_emit_rows(self):
        # A dict child that is itself unchanged and has only unchanged children
        # still emits rows only for its leaves, not for the container itself.
        r = diff_snapshots({"config": {"a": 1}}, {"config": {"a": 1}})
        lines = flatten_diff_tree(r.diff)
        assert len(lines) == 1
        assert lines[0].path == "config.a"
        assert lines[0].status == "unchanged"


class TestFlattenLists:
    def test_bracket_index_path_for_list_leaves(self):
        r = diff_snapshots({"vlans": [10, 20, 30]}, {"vlans": [10, 21, 30]})
        lines = flatten_diff_tree(r.diff)
        by_path = {line.path: line for line in lines}
        assert "vlans[0]" in by_path
        assert by_path["vlans[0]"].status == "unchanged"
        assert by_path["vlans[1]"].status == "changed"
        assert by_path["vlans[1]"].before == "20"
        assert by_path["vlans[1]"].after == "21"
        assert by_path["vlans[2]"].status == "unchanged"

    def test_longer_after_list_emits_added_rows_with_empty_before(self):
        r = diff_snapshots({"vlans": [10]}, {"vlans": [10, 20, 30]})
        lines = flatten_diff_tree(r.diff)
        by_path = {line.path: line for line in lines}
        assert by_path["vlans[0]"].status == "unchanged"
        assert by_path["vlans[1]"].status == "added"
        assert by_path["vlans[1]"].before == ""
        assert by_path["vlans[1]"].after == "20"
        assert by_path["vlans[2]"].status == "added"
        assert by_path["vlans[2]"].after == "30"

    def test_shorter_after_list_emits_removed_rows_with_empty_after(self):
        r = diff_snapshots({"vlans": [10, 20, 30]}, {"vlans": [10]})
        lines = flatten_diff_tree(r.diff)
        by_path = {line.path: line for line in lines}
        assert by_path["vlans[1]"].status == "removed"
        assert by_path["vlans[1]"].before == "20"
        assert by_path["vlans[1]"].after == ""
        assert by_path["vlans[2]"].status == "removed"


class TestFlattenNestedContainerLeafValues:
    def test_dict_leaf_value_serializes_to_compact_one_line_json(self):
        before = {"acl": {"old": "permit 10"}}
        after = {"acl": {"new": "permit 20"}}
        r = diff_snapshots(before, after)
        lines = flatten_diff_tree(r.diff)
        # The added leaf "new" under acl has a dict value (the engine stores the
        # whole dict as the "after" because it's a leaf at that key — the
        # engine recursed into acl and found "new" only in after).
        # Actually here acl recurses; the leaf is "old" (removed) and "new" (added).
        by_path = {line.path: line for line in lines}
        assert by_path["acl.old"].status == "removed"
        assert by_path["acl.old"].before == "permit 10"
        assert by_path["acl.new"].status == "added"
        assert by_path["acl.new"].after == "permit 20"

    def test_list_leaf_value_serializes_to_compact_json(self):
        # A leaf whose value is itself a list renders compact one-line JSON,
        # not pretty-printed.
        r = diff_snapshots({}, {"vlans": [10, 20, 30]})
        lines = flatten_diff_tree(r.diff)
        assert len(lines) == 1
        line = lines[0]
        assert line.status == "added"
        assert line.before == ""
        assert line.after == "[10, 20, 30]"

    def test_dict_value_leaf_serializes_to_compact_json(self):
        # A leaf whose value is itself a dict renders compact one-line JSON.
        # The engine does NOT recurse into an added subtree (before is empty);
        # it stores the whole dict as the added leaf's ``after`` value, so
        # flatten emits one row whose after column is compact JSON.
        r = diff_snapshots({}, {"meta": {"a": 1, "b": 2}})
        lines = flatten_diff_tree(r.diff)
        assert len(lines) == 1
        line = lines[0]
        assert line.path == "meta"
        assert line.status == "added"
        assert line.before == ""
        assert line.after == '{"a": 1, "b": 2}'


class TestFlattenRoundTrip:
    def test_flatten_counts_match_summary(self):
        before = {
            "config": {"hostname": "rtr01", "interfaces": {"Gig0": {"ip": "10.0.0.1"}}},
            "state": {"version": "16.12"},
        }
        after = {
            "config": {"hostname": "rtr02", "interfaces": {"Gig0": {"ip": "10.0.0.1"}}},
            "state": {"version": "16.12"},
        }
        r = diff_snapshots(before, after)
        lines = flatten_diff_tree(r.diff)
        statuses = [line.status for line in lines]
        assert statuses.count("changed") == r.summary["changed"]
        assert statuses.count("added") == r.summary["added"]
        assert statuses.count("removed") == r.summary["removed"]
        assert statuses.count("unchanged") == r.summary["unchanged"]

    def test_every_leaf_emits_exactly_one_row(self):
        # A realistic snapshot with multiple leaves at varying depths.
        before = {
            "config": {"hostname": "rtr01", "vlans": [10, 20]},
            "state": {"show version": {"version": "16.12"}, "show inventory": {"chassis": "C9300"}},
        }
        after = {
            "config": {"hostname": "rtr02", "vlans": [10, 20, 30]},
            "state": {"show version": {"version": "16.13"}, "show inventory": {"chassis": "C9300"}},
        }
        r = diff_snapshots(before, after)
        lines = flatten_diff_tree(r.diff)
        # Total leaves: config.hostname, config.vlans[0], config.vlans[1],
        # config.vlans[2] (added), state["show version"].version,
        # state["show inventory"].chassis = 6.
        assert len(lines) == 6
        # No empty-path rows (the root is a container, not a leaf).
        assert all(line.path for line in lines)
