"""Search-index completeness guard (ATW-816).

AST-only guard asserting every NetBoxModel subclass in models.py has a
matching SearchIndex in search.py, except a documented exclusion set.
Catches the inverse regression: a new model added without a SearchIndex
silently drops out of global search.

Pure-Python (AST), runs in the fast pytest lane without importing netbox.
"""

import ast
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
MODELS = PLUGIN / "models.py"
SEARCH = PLUGIN / "search.py"

# Models intentionally excluded from global search.
# PyatsParserCatalogRefreshSchedule is a singleton intent model (single row,
# no user-facing search term) — global search has nothing to surface.
_EXCLUDED = {"PyatsParserCatalogRefreshSchedule"}


def _extract_netbox_model_subclasses() -> set[str]:
    """Return NetBoxModel subclass names from models.py (AST)."""
    tree = ast.parse(MODELS.read_text(), filename=str(MODELS))
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "NetBoxModel":
                out.add(node.name)
    return out


def _extract_search_index_models() -> set[str]:
    """Return model names registered in search.py (AST).

    Collects ``model = <Name>`` assignments inside SearchIndex subclasses.
    """
    tree = ast.parse(SEARCH.read_text(), filename=str(SEARCH))
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for body_node in node.body:
            if not (isinstance(body_node, ast.Assign) and len(body_node.targets) == 1):
                continue
            tgt = body_node.targets[0]
            if not (isinstance(tgt, ast.Name) and tgt.id == "model"):
                continue
            val = body_node.value
            if isinstance(val, ast.Name):
                out.add(val.id)
    return out


class SearchIndexCompletenessGuard(unittest.TestCase):
    """Every NetBoxModel subclass must have a SearchIndex unless excluded."""

    def test_all_models_have_search_index_or_are_excluded(self):
        models = _extract_netbox_model_subclasses()
        indices = _extract_search_index_models()
        missing = models - indices - _EXCLUDED
        self.assertEqual(
            missing,
            set(),
            f"models without a SearchIndex in search.py: {missing} "
            "(add a SearchIndex or add to _EXCLUDED with a reason)",
        )

    def test_excluded_models_are_documented(self):
        """Excluded models must still exist in models.py (no stale exclusion)."""
        models = _extract_netbox_model_subclasses()
        stale = _EXCLUDED - models
        self.assertEqual(
            stale,
            set(),
            f"_EXCLUDED references models not in models.py: {stale} " "(remove stale exclusion)",
        )


if __name__ == "__main__":
    unittest.main()
