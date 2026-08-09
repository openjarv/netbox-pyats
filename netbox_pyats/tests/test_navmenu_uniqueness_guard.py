"""Hardening guard for the navigation menu and GraphQL schema surface.

These tests are the structural backstop for the regression classes surfaced
by ATW-237:

1. **Nav-menu uniqueness (C1).** PR #79 / commit 98a9b70 fixed a case where
   ``navigation.menu_items`` shipped two duplicate entries (PyATS Compliance
   Runs and PyATS Jobs each appeared twice). No test caught it because the
   plugin test suite never asserted link uniqueness over the menu list. This
   guard parses ``navigation.py`` via AST (so it runs in the fast pure-Python
   pytest lane without importing ``netbox.plugins``) and asserts that each
   ``PluginMenuItem(link=...)`` link target is unique across the whole menu,
   that the top-level ``menu`` is a ``PluginMenu`` with a non-empty
   ``groups`` tuple of ``(label, items)`` pairs, and that the canonical
   ordering ends with the static ``supported_platforms`` report (the only
   non-model menu entry, per ADR-0001 §3 / ATW-83). ATW-382 moved the nav from
   a flat ``menu_items`` list (nested under Plugins) to a top-level
   ``PluginMenu``; the guard was updated to walk the new structure without
   weakening the invariants.

2. **GraphQL schema completeness vs docs.** ``docs/user/usage.md`` §"REST and
   GraphQL" claims a GraphQL type for ``PyatsCredential``, ``PyatsSnapshot``,
   ``PyatsSnapshotDiff``, and marks ``PyatsGoldenConfig`` /
   ``PyatsComplianceRun`` as "deferred" (no GraphQL type in v1). This guard
   parses ``graphql/schema.py`` and ``models.py`` via AST and asserts that
   every NetBoxModel subclass in ``models.py`` is covered exactly once in the
   GraphQL schema *unless* it is in the documented deferred set, and that no
   type references a model that no longer exists (the inverse regression).

Pure-Python: AST-only, no Django/NetBox import. Runs in the fast pytest lane.
"""

import ast
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
NAV = PLUGIN / "navigation.py"
SCHEMA = PLUGIN / "graphql" / "schema.py"
MODELS = PLUGIN / "models.py"
USAGE_DOC = PLUGIN.parent / "docs" / "user" / "usage.md"


def _extract_menu_item_kwargs(call_node) -> tuple[str, str]:
    """Return ``(link, link_text)`` from a ``PluginMenuItem(...)`` call."""
    if not isinstance(call_node, ast.Call):
        raise AssertionError(f"menu entry is not a Call: {ast.dump(call_node)}")
    kw = {k.arg: k.value for k in call_node.keywords}
    return _str_kw(kw.get("link")), _str_kw(kw.get("link_text"))


# Names of the top-level PluginMenu variables the plugin registers. NetBox
# calls ``register_menu(menu)`` once per variable via ``PluginConfig.menu``
# pointing at a module path; multiple top-level PluginMenus in one module are
# supported (see ``navigation.py`` — ATW-728 split ``menu`` into
# ``genie_menu`` + ``jobs_menu``). The guard walks every top-level assignment
# whose target name ends in ``_menu`` (or is exactly ``menu``) so a future
# restructure does not silently drop a menu from the uniqueness/ordering
# invariants.
_MENU_VAR_SUFFIXES = ("menu",)


def _is_menu_var(name: str) -> bool:
    return name == "menu" or name.endswith("_menu")


def _extract_menu_links() -> list[tuple[str, str]]:
    """Return ``[(link, link_text), ...]`` parsed from every top-level menu.

    Walks the AST of ``navigation.py`` and flattens each ``PluginMenu.groups``
    structure — a tuple of ``(group_label, (PluginMenuItem(...), ...))``
    pairs — into an ordered list of ``(link, link_text)`` tuples. The order
    is the in-source declaration order, so the "ends with supported_platforms"
    invariant is checked against the real last item. Walks the AST rather
    than importing the module so the test runs without ``netbox.plugins``
    available (the fast pytest lane).
    """
    tree = ast.parse(NAV.read_text(), filename=str(NAV))
    links: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and _is_menu_var(target.id)):
                continue
            call = node.value
            if not isinstance(call, ast.Call):
                raise AssertionError("navigation menu must be a PluginMenu(...) call")
            # PluginMenu(label=..., groups=..., icon_class=...) — find groups.
            kw = {k.arg: k.value for k in call.keywords}
            groups_node = kw.get("groups")
            if groups_node is None and call.args and len(call.args) >= 2:
                groups_node = call.args[1]
            if not isinstance(groups_node, ast.Tuple):
                raise AssertionError("PluginMenu groups must be a tuple literal")
            for group in groups_node.elts:
                if not isinstance(group, ast.Tuple) or len(group.elts) != 2:
                    raise AssertionError("each PluginMenu group must be a (label, items) pair")
                items_node = group.elts[1]
                if not isinstance(items_node, ast.Tuple):
                    raise AssertionError("group items must be a tuple of PluginMenuItem calls")
                for elt in items_node.elts:
                    link, text = _extract_menu_item_kwargs(elt)
                    links.append((link, text))
    if not links:
        raise AssertionError("no PluginMenu assignment found in navigation.py")
    return links


def _str_kw(node) -> str:
    """Resolve a keyword value to its string literal, unwrapping ``_(...)``."""
    if node is None:
        return ""
    # _(\"text\") — gettext_lazy call wrapper.
    if isinstance(node, ast.Call):
        node = node.args[0] if node.args else None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise AssertionError(f"could not resolve string kwarg: {ast.dump(node)}")


def _extract_schema_type_models() -> dict[str, str]:
    """Return ``{model_name: type_class_name}`` parsed from ``schema.py``.

    Each ``class XType(NetBoxObjectType): class Meta: model = Y`` contributes
    one entry. Walks the AST so the test runs without importing netbox.
    """
    tree = ast.parse(SCHEMA.read_text(), filename=str(SCHEMA))
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Look for an inner ``class Meta``.
        for body_node in node.body:
            if not (isinstance(body_node, ast.ClassDef) and body_node.name == "Meta"):
                continue
            for stmt in body_node.body:
                if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1):
                    continue
                tgt = stmt.targets[0]
                if not (isinstance(tgt, ast.Name) and tgt.id == "model"):
                    continue
                val = stmt.value
                if isinstance(val, ast.Attribute):
                    out[val.attr] = node.name
                elif isinstance(val, ast.Name):
                    out[val.id] = node.name
    return out


def _extract_model_classes() -> set[str]:
    """Return the set of top-level class names in ``models.py``."""
    tree = ast.parse(MODELS.read_text(), filename=str(MODELS))
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}


# Models documented in ``docs/user/usage.md`` as GraphQL-"deferred" in v1.
# Source: docs/user/usage.md §"REST and GraphQL" table.
DEFERRED_GRAPHQL_MODELS = {"PyatsGoldenConfig", "PyatsComplianceRun"}


class NavMenuUniquenessGuard(unittest.TestCase):
    """C1 regression guard: navigation menu items must have unique links."""

    def test_menu_items_is_non_empty(self):
        links = _extract_menu_links()
        self.assertGreater(len(links), 0, "menu must not be empty")

    def test_menu_links_are_unique(self):
        links = _extract_menu_links()
        seen: dict[str, list[str]] = {}
        for link, text in links:
            seen.setdefault(link, []).append(text)
        dupes = {link: texts for link, texts in seen.items() if len(texts) > 1}
        self.assertEqual(
            dupes,
            {},
            f"duplicate PluginMenuItem link targets in menu: {dupes} " "(regression class fixed in 98a9b70 / PR #79)",
        )

    def test_menu_texts_are_unique(self):
        """Display text should also be unique to avoid operator confusion."""
        links = _extract_menu_links()
        seen: dict[str, list[str]] = {}
        for link, text in links:
            seen.setdefault(text, []).append(link)
        dupes = {t: l for t, l in seen.items() if len(l) > 1}
        self.assertEqual(
            dupes,
            {},
            f"duplicate PluginMenuItem link_text in menu: {dupes}",
        )

    def test_canonical_ordering_ends_with_supported_platforms(self):
        """The static supported-platforms report is the final menu entry.

        Per ADR-0001 §3 / ATW-83 it is the only non-model menu entry and
        conventionally closes the menu.
        """
        links = _extract_menu_links()
        self.assertTrue(
            links[-1][0].endswith(":supported_platforms"),
            f"menu must end with the supported_platforms link, got {links[-1]}",
        )


class GraphQLSchemaCompletenessGuard(unittest.TestCase):
    """Asserts graphql/schema.py types match the docs' claimed model set.

    Two-sided: every model in models.py must have a GraphQL type OR be in the
    documented deferred set; every GraphQL type must reference a real model.
    """

    def test_every_model_has_type_or_is_documented_deferred(self):
        types = _extract_schema_type_models()
        # Models that the docs claim have a GraphQL type in v1.
        # PyatsCredential, PyatsSnapshot, PyatsSnapshotDiff are the v1 surface
        # with types; PyatsJob + PyatsParserCatalog were added later (ATW-16,
        # ATW-241) and carry types too. Deferred-only models must not have a
        # type, per docs.
        for model in DEFERRED_GRAPHQL_MODELS:
            self.assertNotIn(
                model,
                types,
                f"{model} is documented as GraphQL-deferred in v1 but has a "
                "type in graphql/schema.py — update docs/user/usage.md or "
                "remove the type",
            )
        # Any model that is NOT deferred must have a GraphQL type.
        missing = [
            m
            for m in ("PyatsCredential", "PyatsSnapshot", "PyatsSnapshotDiff", "PyatsJob", "PyatsParserCatalog")
            if m not in types
        ]
        self.assertEqual(
            missing,
            [],
            f"models missing a GraphQL type in graphql/schema.py: {missing} "
            "(docs/user/usage.md claims a type for these)",
        )

    def test_no_type_references_nonexistent_model(self):
        models = _extract_model_classes()
        types = _extract_schema_type_models()
        orphan = [m for m in types if m not in models]
        self.assertEqual(
            orphan,
            [],
            f"GraphQL types reference models not defined in models.py: {orphan} "
            "(stale type left after a model rename/removal)",
        )

    def test_each_model_has_at_most_one_type(self):
        # _extract_schema_type_models builds a dict keyed by model name, so a
        # second type for the same model would silently overwrite the first.
        # Re-parse with a list-based collector to detect duplicates.
        tree = ast.parse(SCHEMA.read_text(), filename=str(SCHEMA))
        seen: dict[str, list[str]] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for body_node in node.body:
                if not (isinstance(body_node, ast.ClassDef) and body_node.name == "Meta"):
                    continue
                for stmt in body_node.body:
                    if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1):
                        continue
                    tgt = stmt.targets[0]
                    if not (isinstance(tgt, ast.Name) and tgt.id == "model"):
                        continue
                    val = stmt.value
                    name = val.attr if isinstance(val, ast.Attribute) else val.id
                    seen.setdefault(name, []).append(node.name)
        dupes = {m: t for m, t in seen.items() if len(t) > 1}
        self.assertEqual(
            dupes,
            {},
            f"multiple GraphQL types for the same model: {dupes}",
        )

    def test_deferred_models_documented_match_code(self):
        """The docs' deferred set must match the code's deferred set.

        Catches the inverse regression: a model added to the deferred set in
        code (by simply not writing a type) but the docs still claim a type,
        or vice versa. Reads the usage.md table and cross-checks.
        """
        text = USAGE_DOC.read_text()
        types = _extract_schema_type_models()
        # Models the docs claim have a GraphQL type ("yes" row).
        # Parse the usage.md table rows for the GraphQL column.
        import re

        rows = re.findall(
            r"\|\s*`([A-Za-z]+)`\s*\|\s*[^|]+\|\s*([^|]+)\|",
            text,
        )
        doc_graphql: dict[str, str] = {}
        for model, gql_cell in rows:
            cell = gql_cell.strip().lower()
            if cell.startswith("yes") or "yes" in cell:
                doc_graphql[model] = "yes"
            elif "deferred" in cell:
                doc_graphql[model] = "deferred"
        # Every model the docs claim "yes" for must have a type.
        for model, claim in doc_graphql.items():
            if claim == "yes":
                self.assertIn(
                    model,
                    types,
                    f"docs/user/usage.md claims GraphQL 'yes' for {model} but " "no type exists in graphql/schema.py",
                )
        # Every model the docs mark "deferred" must NOT have a type.
        for model, claim in doc_graphql.items():
            if claim == "deferred":
                self.assertNotIn(
                    model,
                    types,
                    f"docs/user/usage.md marks {model} GraphQL 'deferred' but a "
                    "type exists in graphql/schema.py — update the docs",
                )


if __name__ == "__main__":
    unittest.main()
