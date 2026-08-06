"""Hardening invariant guard for table ActionsColumn declarations (ATW-582).

ATW-183 was a production HTTP 500: four append-only plugin list views
(snapshots, diffs, compliance-runs, jobs) returned ``NoReverseMatch`` on a
non-existent ``*_edit`` URL because the ``NetBoxTable`` base class declares a
class-level ``actions = columns.ActionsColumn()`` defaulting to
``actions=('edit', 'delete', 'changelog')``. The edit action reverses
``*_edit`` for every row; append-only models have no edit view, so the reverse
raises and the list view 500s. The fix (commit d498417 / PR #57) overrode the
class attribute on the four append-only tables:

    actions = ActionsColumn(actions=('delete', 'changelog'))

Any *new* append-only table that forgets the override regresses the 500 — the
regression class is silent because no test asserts the structural invariant
("every NetBoxTable subclass in the plugin declares an explicit ActionsColumn").
This guard closes that gap.

Two-sided guard, mirroring ``test_navmenu_uniqueness_guard`` (AST parse of the
source module, no Django/NetBox import) and ``test_state_commands_invariant``
(structural invariants on a source declaration):

1. **Every NetBoxTable subclass in tables.py declares an explicit ``actions``
   attribute** that is an ``ActionsColumn(...)`` call. An editable table that
   omits it silently inherits the default (which is correct for editable
   models but masks intent); an append-only table that omits it regresses
   ATW-183. Requiring the declaration on *every* table makes the regression
   structurally impossible to reintroduce — a new append-only table that
   forgets the override fails this guard, not the list view at runtime.

2. **Append-only tables use the restricted action set.** The four append-only
   models (Snapshot, SnapshotDiff, ComplianceRun, Job) must pass
   ``actions=_APPEND_ONLY_ACTIONS`` (or an equivalent tuple literal excluding
   ``'edit'``). This catches a table that declares an explicit ActionsColumn
   but with the wrong action set (e.g. a copy-paste of an editable table's
   ``ActionsColumn()`` default).

Pure-Python: AST-only, no Django/NetBox import. Runs in the fast pytest lane
alongside ``test_navmenu_uniqueness_guard`` and ``test_state_commands_invariant``.
"""

import ast
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
TABLES = PLUGIN / "tables.py"

# Append-only models (the ATW-183 regression class). These models have no
# *_edit URL; their tables must use the restricted action set that drops
# 'edit'. Source: views.py / urls.py — no ObjectEditView for these models.
APPEND_ONLY_TABLES = {
    "PyatsSnapshotTable",
    "PyatsSnapshotDiffTable",
    "PyatsComplianceRunTable",
    "PyatsJobTable",
}

# The restricted action set used by the append-only tables. Defined in
# tables.py as _APPEND_ONLY_ACTIONS = ("delete", "changelog"). Parsed from the
# AST so the guard fails loudly if the constant is renamed/changed.
_APPEND_ONLY_ACTIONS_NAME = "_APPEND_ONLY_ACTIONS"


def _parse_tables_module() -> ast.Module:
    """Parse tables.py into an AST module node."""
    return ast.parse(TABLES.read_text(), filename=str(TABLES))


def _is_netbox_table_subclass(class_node: ast.ClassDef) -> bool:
    """Return True if the class has ``NetBoxTable`` in its direct bases."""
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id == "NetBoxTable":
            return True
        # ``NetBoxTable`` could also appear as an attribute (e.g. tables.NetBoxTable)
        # but in this plugin it is imported as a bare name. Guard for both.
        if isinstance(base, ast.Attribute) and base.attr == "NetBoxTable":
            return True
    return False


def _find_actions_assignment(class_node: ast.ClassDef) -> ast.Assign | None:
    """Return the ``actions = ActionsColumn(...)`` assignment node, or None.

    Walks the *direct* body of the class (not nested classes like ``Meta``)
    to find an ``actions = ...`` assignment whose value is a Call node.
    """
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        if not (isinstance(target, ast.Name) and target.id == "actions"):
            continue
        if not isinstance(stmt.value, ast.Call):
            continue
        return stmt
    return None


def _call_name(call_node: ast.Call) -> str:
    """Resolve the readable name of a Call node's func (e.g. ``ActionsColumn``)."""
    func = call_node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ast.dump(func)


def _resolve_append_only_actions(tree: ast.Module) -> tuple[str, ...] | None:
    """Return the tuple literal assigned to ``_APPEND_ONLY_ACTIONS``, or None.

    Parses the module-level ``_APPEND_ONLY_ACTIONS = (...)`` assignment so the
    guard tracks the canonical constant rather than hard-coding the tuple
    here (a rename or value change fails loudly).
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id == _APPEND_ONLY_ACTIONS_NAME):
                continue
            val = node.value
            if isinstance(val, ast.Tuple):
                return tuple(
                    elt.value for elt in val.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                )
            return None
    return None


def _extract_actions_kwarg(call_node: ast.Call) -> str | None:
    """Return the resolved name of the ``actions=`` keyword argument value.

    The append-only tables pass ``actions=_APPEND_ONLY_ACTIONS`` (a Name node)
    or an inline tuple. Return the Name.id for a Name, or a reconstructed
    string for an inline tuple, or None if the kwarg is absent (the editable
    default: ``ActionsColumn()`` with no actions kwarg).
    """
    for kw in call_node.keywords:
        if kw.arg != "actions":
            continue
        val = kw.value
        if isinstance(val, ast.Name):
            return val.id
        if isinstance(val, ast.Tuple):
            parts = []
            for elt in val.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    parts.append(elt.value)
            return "tuple:" + ",".join(parts)
        return None
    return None


def _extract_all_table_classes() -> list[ast.ClassDef]:
    """Return all ``NetBoxTable`` subclass ClassDef nodes in tables.py."""
    tree = _parse_tables_module()
    return [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and _is_netbox_table_subclass(node)]


class TableActionsColumnGuard(unittest.TestCase):
    """ATW-183 regression guard: every NetBoxTable subclass declares an
    explicit ``actions = ActionsColumn(...)`` attribute."""

    def test_finds_at_least_one_table(self):
        """Sanity: the guard can see the tables (guards against a parse miss
        that would make every other test vacuously pass)."""
        tables = _extract_all_table_classes()
        self.assertGreater(
            len(tables),
            0,
            "no NetBoxTable subclasses found in tables.py — the AST parse is "
            "broken or the plugin lost all its tables",
        )

    def test_every_table_declares_explicit_actions_column(self):
        """Every NetBoxTable subclass must have an explicit
        ``actions = ActionsColumn(...)`` class attribute.

        A table that omits it silently inherits the ``NetBoxTable`` default
        (``ActionsColumn()`` → ``('edit', 'delete', 'changelog')``). For
        append-only models this regresses ATW-183 (list-view 500 on a
        non-existent ``*_edit`` URL). For editable models the inherited
        default is behaviorally correct but masks intent and makes the
        invariant unenforceable — requiring the explicit declaration on
        every table makes the regression structurally impossible to
        reintroduce.
        """
        tables = _extract_all_table_classes()
        missing = []
        for cls in tables:
            if _find_actions_assignment(cls) is None:
                missing.append(cls.name)
        self.assertEqual(
            missing,
            [],
            f"NetBoxTable subclasses without an explicit `actions = "
            f"ActionsColumn(...)` class attribute: {missing}. Every table "
            "must declare its actions column explicitly — an append-only "
            "table that omits it regresses ATW-183 (list-view 500). Add "
            "`actions = ActionsColumn()` (editable) or "
            "`actions = ActionsColumn(actions=_APPEND_ONLY_ACTIONS)` "
            "(append-only).",
        )

    def test_actions_attribute_is_an_actionscolumn_call(self):
        """The ``actions`` attribute must be an ``ActionsColumn(...)`` call,
        not a bare tuple or other value (``Meta.actions`` does NOT override
        the ActionsColumn constructor — that was the ATW-183 first-fix
        mistake, commit ea0e343)."""
        tables = _extract_all_table_classes()
        wrong = []
        for cls in tables:
            assign = _find_actions_assignment(cls)
            if assign is None:
                continue
            call_name = _call_name(assign.value)
            if call_name != "ActionsColumn":
                wrong.append((cls.name, call_name))
        self.assertEqual(
            wrong,
            [],
            f"tables with an `actions` attribute that is NOT an "
            f"ActionsColumn(...) call: {wrong}. Meta.actions only controls "
            "the column sequence, not the ActionsColumn constructor — use "
            "`actions = ActionsColumn(...)` at the class level (ATW-183 "
            "root cause).",
        )

    def test_append_only_tables_use_restricted_action_set(self):
        """The four append-only tables (Snapshot, SnapshotDiff,
        ComplianceRun, Job) must pass ``actions=_APPEND_ONLY_ACTIONS`` —
        the restricted set that drops ``'edit'``.

        Catches a table that declares an explicit ActionsColumn but with
        the editable default (``ActionsColumn()`` → includes 'edit'),
        which would regress the ATW-183 500.
        """
        tree = _parse_tables_module()
        canonical = _resolve_append_only_actions(tree)
        self.assertIsNotNone(
            canonical,
            f"could not resolve `{_APPEND_ONLY_ACTIONS_NAME}` tuple literal "
            "in tables.py — the constant was renamed, removed, or is no "
            "longer a tuple of string literals. Update this guard.",
        )
        self.assertNotIn(
            "edit",
            canonical,
            f"`{_APPEND_ONLY_ACTIONS_NAME}` includes 'edit' — append-only "
            "tables must NOT expose the edit action (ATW-183 regression).",
        )

        tables = _extract_all_table_classes()
        wrong = []
        for cls in tables:
            if cls.name not in APPEND_ONLY_TABLES:
                continue
            assign = _find_actions_assignment(cls)
            # Already asserted non-None above, but guard for ordering.
            if assign is None:
                wrong.append((cls.name, "no actions attribute"))
                continue
            kw = _extract_actions_kwarg(assign.value)
            if kw is None:
                wrong.append((cls.name, "ActionsColumn() with no actions kwarg (uses edit default)"))
                continue
            if kw != _APPEND_ONLY_ACTIONS_NAME:
                wrong.append((cls.name, f"actions={kw!r} (expected {_APPEND_ONLY_ACTIONS_NAME})"))
        self.assertEqual(
            wrong,
            [],
            f"append-only tables with the wrong action set: {wrong}. "
            "Append-only tables must pass "
            f"`actions={_APPEND_ONLY_ACTIONS_NAME}` to drop 'edit' — the "
            "ATW-183 regression class.",
        )

    def test_editable_tables_do_not_use_restricted_action_set(self):
        """Editable tables (the non-append-only models) must NOT pass
        ``_APPEND_ONLY_ACTIONS`` — they have ``*_edit`` URLs and need the
        default action set that includes 'edit'.

        Catches a copy-paste of the append-only override onto an editable
        table, which would silently hide the edit button from operators.
        """
        tables = _extract_all_table_classes()
        wrong = []
        for cls in tables:
            if cls.name in APPEND_ONLY_TABLES:
                continue
            assign = _find_actions_assignment(cls)
            if assign is None:
                continue
            kw = _extract_actions_kwarg(assign.value)
            if kw == _APPEND_ONLY_ACTIONS_NAME:
                wrong.append((cls.name, f"actions={kw!r} (append-only set on an editable table)"))
        self.assertEqual(
            wrong,
            [],
            f"editable tables using the append-only action set: {wrong}. "
            "Editable tables have *_edit URLs and must use the default "
            "ActionsColumn() (includes 'edit'), not _APPEND_ONLY_ACTIONS.",
        )

    def test_known_table_set_present(self):
        """Pin the known set of NetBoxTable subclasses so a silent table
        addition/removal is caught (the guard must see every table)."""
        tables = _extract_all_table_classes()
        actual = {cls.name for cls in tables}
        expected = {
            "PyatsCredentialTable",
            "PyatsSnapshotTable",
            "PyatsSnapshotDiffTable",
            "PyatsGoldenConfigTable",
            "PyatsComplianceRunTable",
            "PyatsJobTable",
            "PyatsCaptureScheduleTable",
            "PyatsParserCatalogRefreshScheduleTable",
        }
        missing = expected - actual
        extra = actual - expected
        self.assertEqual(
            missing,
            set(),
            f"expected NetBoxTable subclasses missing from tables.py: "
            f"{sorted(missing)} — the guard cannot protect tables it "
            "cannot see",
        )
        self.assertEqual(
            extra,
            set(),
            f"unexpected NetBoxTable subclasses in tables.py: "
            f"{sorted(extra)} — add them to this guard's expected set and "
            "classify them as append-only or editable",
        )


if __name__ == "__main__":
    unittest.main()
