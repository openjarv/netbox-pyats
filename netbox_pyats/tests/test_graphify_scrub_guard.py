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
