"""Regression guard for ``inc/diff_tree.html`` comment rendering (ATW-508/509/510).

The diff-tree partial's header comment was originally written as a multi-line
Django ``{# ... #}`` single-line comment tag spanning several lines. Django
only strips SINGLE-line ``{# #}`` comments — a multi-line ``{# #}`` block is
not stripped and renders as literal text in the page (the board's screenshot:
the comment text appeared as one unformatted line, and the stray ``<details>``
substring in the comment produced a phantom "Details" element). The fix
converts the multi-line comment to a ``{% comment %}...{% endcomment %}``
block, which Django does strip across multiple lines.

This module has two layers:

- **Source-level structural guard** (pure-Python, runs in the unit lane): asserts
  the header comment uses ``{% comment %}``/``{% endcomment %}`` and that no
  multi-line ``{# ... #}`` comment (a ``{#`` whose matching ``#}`` is on a
  later line) remains. This is the cheap, fast regression guard.
- **NetBox-gated render guard** (skipped when ``netbox``/Django is not
  importable): renders the partial with a minimal diff node and asserts the
  comment text does not leak into the output and the ``<details>`` tree renders.
"""

from pathlib import Path

import pytest

_TMPL = Path(__file__).resolve().parents[1] / "templates" / "netbox_pyats" / "inc" / "diff_tree.html"


def _lines():
    return _TMPL.read_text().splitlines()


# --- Source-level structural guard (pure-Python, unit lane) --------------- #


def test_header_comment_uses_block_comment_tag():
    """The header comment must use ``{% comment %}``/``{% endcomment %}``,
    not a multi-line ``{# ... #}`` (which Django does not strip and renders as
    literal text). ATW-508/509 regression guard.
    """
    src = _TMPL.read_text()
    assert "{% comment %}" in src, "header comment must open with {% comment %}"
    assert "{% endcomment %}" in src, "header comment must close with {% endcomment %}"


def test_no_multiline_single_line_comment_tag_remains():
    """No ``{#`` whose matching ``#}`` is on a later line may remain — Django
    does not strip multi-line ``{# #}`` blocks and they render as literal
    text. Single-line ``{# ... #}`` comments (open and close on the same line)
    are fine and are left in place (line 29's leaf comment).
    """
    for idx, line in enumerate(_lines(), start=1):
        if "{#" in line and "#}" in line:
            # Single-line comment — open and close on the same line: fine.
            continue
        if "{#" in line and "#}" not in line:
            pytest.fail(
                f"line {idx}: multi-line {{# ... #}} comment detected (open with "
                f"no close on the same line) — Django renders this as literal text. "
                f"Use {{% comment %}}...{{% endcomment %}} instead."
            )


# --- NetBox-gated render guard ------------------------------------------- #

try:
    import netbox  # noqa: F401

    _HAS_NETBOX = True
except ImportError:  # pragma: no cover - unit lane has no netbox installed
    _HAS_NETBOX = False

if _HAS_NETBOX:
    from django.template.loader import render_to_string


@pytest.mark.skipif(not _HAS_NETBOX, reason="render guard needs Django + netbox")
class TestDiffTreeRendersWithoutCommentLeak:
    """Render ``inc/diff_tree.html`` with a minimal node and assert the
    comment text does not leak and the collapsible ``<details>`` tree renders.
    """

    def test_comment_text_does_not_leak_into_rendered_output(self):
        node = {
            "type": "leaf",
            "status": "unchanged",
            "value": "foo",
        }
        html = render_to_string(
            "netbox_pyats/inc/diff_tree.html",
            {"node": node},
        )
        # The header comment text must NOT appear in the rendered HTML.
        assert "Recursive partial rendering" not in html
        assert "PyatsSnapshotDiff diff node" not in html
        assert "Server-rendered" not in html
        # The stray "<details>" substring from the comment must not produce a
        # phantom Details element — only the real <details> tree should render.
        # A single leaf node renders exactly one <details> element.
        assert html.count("<details") == 1
        # The leaf value renders inside the output.
        assert "foo" in html

    def test_changed_dict_node_renders_open_details_and_badges(self):
        node = {
            "type": "dict",
            "status": "changed",
            "name": "config",
            "children": {
                "hostname": {
                    "type": "leaf",
                    "status": "changed",
                    "before": "rtr01",
                    "after": "rtr02",
                },
            },
        }
        html = render_to_string(
            "netbox_pyats/inc/diff_tree.html",
            {"node": node},
        )
        # Changed subtrees render <details ... open ...> (board contract).
        assert "open" in html
        # Status + type badges render.
        assert "changed" in html
        assert "dict" in html
        # The child leaf's before/after render.
        assert "rtr01" in html
        assert "rtr02" in html
        # No comment text leaks.
        assert "Recursive partial rendering" not in html
