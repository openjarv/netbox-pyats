"""Tests for scripts/pr-body-scrub-guard.sh.

The PR body scrub guard is the structural backstop against Paperclip
control-plane metadata (agent UUIDs, `agent://` URIs, internal org-role
titles) leaking into public GitHub PR bodies — the repeat finding across
PRs #44-#47 (ATW-159). These tests feed the guard synthetic clean/leaked
PR bodies via the PR_BODY env var and assert the pass/fail behaviour for
each leak class.

Refs: ATW-159, ATW-112, ATW-55. Sibling: test_graphify_scrub_guard.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "pr-body-scrub-guard.sh"


def _run(body: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env={"PR_BODY": body, "PATH": "/usr/bin:/bin"},
    )


# --- clean bodies (must pass) ---------------------------------------------


def test_clean_body_passes():
    res = _run("## Summary\nAdds upgrade docs.\n\n" "## Notes for reviewers\nReviewer: CTO. Merger: CEO.")
    assert res.returncode == 0, res.stderr
    assert "clean" in res.stdout.lower()


def test_role_only_prose_passes():
    """Role words in normal prose (not on a reviewer/merger line) are fine."""
    res = _run("## Summary\nThe CTO signed off. The QA Engineer will run regression.\n" "- Closes #155")
    assert res.returncode == 0, res.stderr


def test_commit_short_sha_passes():
    """An 8-char commit short-SHA must NOT trip the agent-prefix pattern."""
    res = _run("## Changes\n- Commit 1d8cfb9 applies the readability review.\n" "Reviewer: CTO. Merger: CEO.")
    assert res.returncode == 0, res.stderr


def test_empty_body_passes():
    res = _run("")
    assert res.returncode == 0, res.stderr


# --- leaked bodies (must fail) ---------------------------------------------


# Synthetic UUIDs (RFC-4122 variant, documentation/test-only) — do NOT resolve
# to any real Paperclip agent. The guard patterns are shape-keyed, so these
# exercise identical coverage without leaking the live agent fleet.
_FAKE_CTO_UUID = "11111111-2222-4333-8444-555555555555"
_FAKE_CEO_UUID = "66666666-7777-4888-8999-000000000000"
_FAKE_BARE_UUID = "aaaaaaa1-bbbb-4ccc-8ddd-eeeeeeeeeeee"
_FAKE_CTO_PREFIX = "11111111"
_FAKE_CEO_PREFIX = "66666666"


def test_agent_uri_leak_fails():
    """PR #44/#45 form: `[@CTO](agent://<uuid>)`."""
    res = _run(
        "reviewer: [@CTO](agent://%s)\n"
        "merger: [@Chief of staff](agent://%s)" % (_FAKE_CTO_UUID, _FAKE_CEO_UUID)
    )
    assert res.returncode == 1, res.stdout + res.stderr
    assert "agent:// URI" in res.stderr


def test_bare_uuid_leak_fails():
    """A bare RFC-4122 UUID anywhere in the body is caught."""
    res = _run("## Notes\nContact: %s for review." % _FAKE_BARE_UUID)
    assert res.returncode == 1, res.stdout + res.stderr
    assert "bare UUID" in res.stderr


def test_agent_prefix_leak_fails():
    """PR #47 form: `reviewer: @CTO (agent <prefix>)`."""
    res = _run(
        "reviewer: @CTO (agent %s)\nmerger: @CEO (agent %s)"
        % (_FAKE_CTO_PREFIX, _FAKE_CEO_PREFIX)
    )
    assert res.returncode == 1, res.stdout + res.stderr
    assert "agent <prefix>" in res.stderr


def test_pr47_full_form_fails():
    """The exact PR #47 leaked line — prefix + role, caught by the prefix."""
    res = _run(
        "reviewer: @CTO (agent %s)\nmerger: @CEO (agent %s, Chief of staff)"
        % (_FAKE_CTO_PREFIX, _FAKE_CEO_PREFIX)
    )
    assert res.returncode == 1, res.stdout + res.stderr
