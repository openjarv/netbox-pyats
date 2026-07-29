"""Tests for scripts/graphify-scrub-guard.sh.

The scrub guard is the structural backstop against the absolute home-path
leak class that regressed on PR #41 (ATW-112 Security gate, fixed in
90435be). These tests synthesize leaked/clean graphify-out/ trees in tmp
dirs and assert the guard's check / scrub / recheck behaviour for the three
matched path classes (/home, /Users, /root).

Refs: ATW-125, ATW-112, ATW-121, PR #41.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "graphify-scrub-guard.sh"

LEAKED_REPORT = "# Graph Report - {home}  (2026-07-24)\n\n## Corpus\n- foo\n"
LEAKED_HTML = "<html><head><title>graphify - {home}/graphify-out/graph.html</title></head></html>\n"
CLEAN_REPORT = "# Graph Report - .  (2026-07-24)\n\n## Corpus\n- foo\n"
CLEAN_HTML = "<html><head><title>graphify - graphify-out/graph.html</title></head></html>\n"


def _make_tree(tmp: Path, report: str, html: str) -> Path:
    gout = tmp / "graphify-out"
    gout.mkdir()
    (gout / "GRAPH_REPORT.md").write_text(report)
    (gout / "graph.html").write_text(html)
    (gout / "graph.json").write_text('{"nodes": []}\n')
    (gout / "manifest.json").write_text("{}\n")
    return tmp


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    return _make_tree(tmp_path, CLEAN_REPORT, CLEAN_HTML)


def test_clean_tree_passes(repo_root: Path):
    res = _run(str(repo_root))
    assert res.returncode == 0, res.stderr
    assert "clean" in res.stdout.lower()


@pytest.mark.parametrize(
    "home",
    [
        "/home/hermes/netbox-pyats",
        "/Users/alice/code/netbox-pyats",
        "/root/netbox-pyats",
    ],
)
def test_leak_detected_in_check_mode(repo_root: Path, home: str):
    (repo_root / "graphify-out" / "GRAPH_REPORT.md").write_text(LEAKED_REPORT.format(home=home))
    res = _run(str(repo_root))
    assert res.returncode == 1, res.stderr
    assert "leak" in res.stderr.lower()


@pytest.mark.parametrize(
    "home",
    [
        "/home/hermes/netbox-pyats",
        "/Users/alice/code/netbox-pyats",
        "/root/netbox-pyats",
    ],
)
def test_scrub_rewrites_and_reverifies(repo_root: Path, home: str):
    (repo_root / "graphify-out" / "GRAPH_REPORT.md").write_text(LEAKED_REPORT.format(home=home))
    (repo_root / "graphify-out" / "graph.html").write_text(LEAKED_HTML.format(home=home))
    res = _run("--scrub", "--check", str(repo_root))
    assert res.returncode == 0, res.stderr
    report = (repo_root / "graphify-out" / "GRAPH_REPORT.md").read_text()
    html = (repo_root / "graphify-out" / "graph.html").read_text()
    assert home not in report
    assert home not in html
    assert report.startswith("# Graph Report - .")
    assert "graphify - graphify-out/graph.html" in html


def test_scrub_is_idempotent(repo_root: Path):
    (repo_root / "graphify-out" / "GRAPH_REPORT.md").write_text(LEAKED_REPORT.format(home="/home/hermes/netbox-pyats"))
    assert _run("--scrub", "--check", str(repo_root)).returncode == 0
    assert _run(str(repo_root)).returncode == 0
    assert _run("--scrub", str(repo_root)).returncode == 0


def test_no_graphify_out_is_clean(tmp_path: Path):
    res = _run(str(tmp_path))
    assert res.returncode == 0


def test_unknown_flag_rejected(repo_root: Path):
    res = _run("--bogus", str(repo_root))
    assert res.returncode == 2


# --- ATW-312: extended scan surface (cache/, dated backups, internal state) ---

LEAKED_CACHE_JSON = '{{"path": "{home}/netbox_pyats/forms.py", "nodes": []}}\n'
LEAKED_DATED_REPORT = "# Graph Report - {home}  (2026-07-24)\n\n## Corpus\n- foo\n"
LEAKED_STATE_JSON = '{{"root": "{home}", "labels": []}}\n'
CLEAN_CACHE_JSON = '{"path": "netbox_pyats/forms.py", "nodes": []}\n'
CLEAN_STATE_JSON = '{"root": ".", "labels": []}\n'


def _make_extended_tree(tmp: Path) -> Path:
    """Build a tree with cache/, a dated backup dir, and .graphify_* state."""
    gout = tmp / "graphify-out"
    gout.mkdir()
    (gout / "GRAPH_REPORT.md").write_text(CLEAN_REPORT)
    (gout / "graph.html").write_text(CLEAN_HTML)
    (gout / "graph.json").write_text('{"nodes": []}\n')
    (gout / "manifest.json").write_text("{}\n")
    # cache/ with stat-index.json + an AST cache file under cache/ast/<ver>/
    cache = gout / "cache"
    (cache / "ast" / "v0.9.20").mkdir(parents=True)
    (cache / "stat-index.json").write_text(CLEAN_CACHE_JSON)
    (cache / "ast" / "v0.9.20" / "abc123.json").write_text(CLEAN_CACHE_JSON)
    # dated snapshot dir
    dated = gout / "2026-07-24"
    dated.mkdir()
    (dated / "GRAPH_REPORT.md").write_text(CLEAN_REPORT)
    (dated / "graph.json").write_text('{"nodes": []}\n')
    # graphify internal-state files
    (gout / ".graphify_analysis.json").write_text(CLEAN_STATE_JSON)
    (gout / ".graphify_labels.json").write_text(CLEAN_STATE_JSON)
    return tmp


@pytest.fixture()
def extended_repo(tmp_path: Path) -> Path:
    return _make_extended_tree(tmp_path)


def test_extended_clean_tree_passes(extended_repo: Path):
    """A tree with clean cache/dated/state files must pass the guard."""
    res = _run(str(extended_repo))
    assert res.returncode == 0, res.stderr
    assert "clean" in res.stdout.lower()


@pytest.mark.parametrize(
    "home",
    [
        "/home/hermes/netbox-pyats",
        "/Users/alice/code/netbox-pyats",
        "/root/netbox-pyats",
    ],
)
def test_cache_leak_detected_in_check_mode(extended_repo: Path, home: str):
    """A leak in cache/stat-index.json must be caught (ATW-307 regression class)."""
    (extended_repo / "graphify-out" / "cache" / "stat-index.json").write_text(LEAKED_CACHE_JSON.format(home=home))
    res = _run(str(extended_repo))
    assert res.returncode == 1, res.stderr
    assert "leak" in res.stderr.lower()
    assert "stat-index.json" in res.stderr


@pytest.mark.parametrize(
    "home",
    [
        "/home/hermes/netbox-pyats",
        "/Users/alice/code/netbox-pyats",
        "/root/netbox-pyats",
    ],
)
def test_cache_ast_leak_detected_in_check_mode(extended_repo: Path, home: str):
    """A leak in a nested cache/ast/<ver>/*.json must be caught."""
    ast_file = extended_repo / "graphify-out" / "cache" / "ast" / "v0.9.20" / "abc123.json"
    ast_file.write_text(LEAKED_CACHE_JSON.format(home=home))
    res = _run(str(extended_repo))
    assert res.returncode == 1, res.stderr
    assert "leak" in res.stderr.lower()
    assert "abc123.json" in res.stderr


@pytest.mark.parametrize(
    "home",
    [
        "/home/hermes/netbox-pyats",
        "/Users/alice/code/netbox-pyats",
        "/root/netbox-pyats",
    ],
)
def test_dated_backup_leak_detected_in_check_mode(extended_repo: Path, home: str):
    """A leak in graphify-out/2026-07-24/GRAPH_REPORT.md must be caught."""
    (extended_repo / "graphify-out" / "2026-07-24" / "GRAPH_REPORT.md").write_text(
        LEAKED_DATED_REPORT.format(home=home)
    )
    res = _run(str(extended_repo))
    assert res.returncode == 1, res.stderr
    assert "leak" in res.stderr.lower()
    assert "2026-07-24" in res.stderr


@pytest.mark.parametrize(
    "home",
    [
        "/home/hermes/netbox-pyats",
        "/Users/alice/code/netbox-pyats",
        "/root/netbox-pyats",
    ],
)
def test_internal_state_leak_detected_in_check_mode(extended_repo: Path, home: str):
    """A leak in .graphify_analysis.json must be caught."""
    (extended_repo / "graphify-out" / ".graphify_analysis.json").write_text(LEAKED_STATE_JSON.format(home=home))
    res = _run(str(extended_repo))
    assert res.returncode == 1, res.stderr
    assert "leak" in res.stderr.lower()
    assert ".graphify_analysis.json" in res.stderr


@pytest.mark.parametrize(
    "home",
    [
        "/home/hermes/netbox-pyats",
        "/Users/alice/code/netbox-pyats",
        "/root/netbox-pyats",
    ],
)
def test_extended_scrub_rewrites_and_reverifies(extended_repo: Path, home: str):
    """--scrub --check must rewrite leaks across all extended surfaces."""
    gout = extended_repo / "graphify-out"
    (gout / "cache" / "stat-index.json").write_text(LEAKED_CACHE_JSON.format(home=home))
    (gout / "cache" / "ast" / "v0.9.20" / "abc123.json").write_text(LEAKED_CACHE_JSON.format(home=home))
    (gout / "2026-07-24" / "GRAPH_REPORT.md").write_text(LEAKED_DATED_REPORT.format(home=home))
    (gout / ".graphify_analysis.json").write_text(LEAKED_STATE_JSON.format(home=home))
    res = _run("--scrub", "--check", str(extended_repo))
    assert res.returncode == 0, res.stderr
    # All leaks rewritten.
    assert home not in (gout / "cache" / "stat-index.json").read_text()
    assert home not in (gout / "cache" / "ast" / "v0.9.20" / "abc123.json").read_text()
    assert home not in (gout / "2026-07-24" / "GRAPH_REPORT.md").read_text()
    assert home not in (gout / ".graphify_analysis.json").read_text()
    # GRAPH_REPORT.md (dated and root) collapses to "."
    assert (gout / "2026-07-24" / "GRAPH_REPORT.md").read_text().startswith("# Graph Report - .")


def test_extended_scrub_is_idempotent(extended_repo: Path):
    """Scrubbing an already-clean extended tree is a no-op."""
    gout = extended_repo / "graphify-out"
    (gout / "cache" / "stat-index.json").write_text(LEAKED_CACHE_JSON.format(home="/home/hermes/netbox-pyats"))
    assert _run("--scrub", "--check", str(extended_repo)).returncode == 0
    # Second pass on the now-clean tree must also be clean.
    assert _run(str(extended_repo)).returncode == 0
    assert _run("--scrub", str(extended_repo)).returncode == 0


def test_extended_tree_missing_cache_is_clean(tmp_path: Path):
    """A fresh checkout with no cache/ or dated dirs must still pass."""
    gout = tmp_path / "graphify-out"
    gout.mkdir()
    (gout / "GRAPH_REPORT.md").write_text(CLEAN_REPORT)
    (gout / "graph.html").write_text(CLEAN_HTML)
    (gout / "graph.json").write_text('{"nodes": []}\n')
    (gout / "manifest.json").write_text("{}\n")
    res = _run(str(tmp_path))
    assert res.returncode == 0
