# ADR-0004: Compliance comparison shape — Genie parser harness on the worker

- **Status:** Accepted
- **Date:** 2026-07-21
- **Supersedes:** none
- **Related:** [ATW-64](/ATW/issues/ATW-64), [ATW-15](/ATW/issues/ATW-15), [ATW-61](/ATW/issues/ATW-61), [ADR-0003](0003-netbox46-migration-and-worker-toolchain.md), `netbox_pyats/golden_parse.py`, `netbox_pyats/compliance.py`, `netbox_pyats/jobs.py`

## Context

Phase 4 (ATW-15) shipped a compliance engine that compares an operator-authored golden running-config against a captured snapshot's parsed config. The first implementation (PR #16, reverted) parsed the golden text with a lightweight line-oriented parser into `{section_header_str: [raw_line_str, ...]}` — a dict of lists of raw strings. The snapshot's `data["config"]` is Genie's structured abstract-config dict (nested dicts/scalars). The two shapes are not directly comparable: every top-level key is `added` on one side or `removed` on the other, and matched keys compare a list-of-strings to a scalar/dict → `changed`. **A clean golden run against a matching snapshot always classified as `drift`, never `compliant`** — the compliance engine was structurally broken. See ATW-64 for the full bug analysis.

The compliance engine needs both sides (golden and snapshot config) in the same structured shape so the Phase 3 `diff_snapshots` engine and `inc/diff_tree.html` partial render meaningful results. Three options were considered:

1. **Genie parser harness on the worker** — parse the golden text with the same Genie parser the snapshot used, on the `pyats` worker, via a parser-only harness (no live device).
2. **Parse on save** — parse the golden text into a structured dict at authoring time (in the form/view when the golden config row is saved).
3. **Line-oriented both sides** — store raw `show running-config` text on `PyatsSnapshot` and diff raw text vs. raw golden text line-by-line.

## Decision

**Option 1: parse the golden config text with the same Genie parser the snapshot used, on the `pyats` worker, via a parser-only harness (no live device).**

`parse_golden_config_text(text, *, os)` constructs a minimal in-memory `pyats.topology.Device` with `os=<os>` and calls `device.parse("show running-config", output=text)`. The Genie parser discovery selects the right parser package for `(os, "show running-config")` and feeds the text through it without opening a connection. This produces a Genie abstract-config dict in the same shape as `snapshot.data["config"]`, so `diff_snapshots` can diff them directly and the Phase 3 viewer renders the result unchanged.

The snapshot's OS is derived from `snapshot.device.platform` via `testbed.PLATFORM_SLUG_TO_PYATS_OS` (the same mapping `capture` uses) and stored on a new `PyatsSnapshot.parsed_os` field (migration `0006`) so compliance runs against a deleted device still know the OS.

### Why Option 1

- **Keeps the ADR-0003 invariant:** the web process is Genie-free. Genie only lives on the `pyats` worker, where `pyats[full]` is installed. The compliance job already runs there on the dedicated queue.
- **Same shape on both sides:** the golden is parsed with the same Genie parser that produced the snapshot's `data["config"]`, so the diff is meaningful and the Phase 3 viewer renders it unchanged.
- **No second parser to maintain:** the golden text is parsed by the same Genie parser packages that already need to be installed for snapshot capture. No custom parsing logic that could drift from Genie's shape.

### Why not Option 2 (parse on save)

Parse-on-save either moves Genie into the web container (breaks the ADR-0003 invariant, doubles the Genie install matrix) or invents a second parser (which is exactly the shape-mismatch bug again — a non-Genie parser producing a different shape). Golden authoring stays a plain text field; parsing happens at compliance-run time on the worker.

### Why not Option 3 (line-oriented both sides)

Line-oriented diff requires storing raw `show running-config` text on `PyatsSnapshot`, abandoning the structured Phase 3 diff-tree reuse that is the entire architectural justification for `compliance.py`, and standing up a separate text-diff viewer path. The cost is larger than Option 1 and it loses the structured "what drifted, where" tree the Phase 3 viewer already renders.

## Consequences

- **`PyatsSnapshot.parsed_os`** (new field, migration `0006`): records the Genie parser's os at capture time so compliance runs can select the same parser even after the device is deleted. Set by `capture_snapshot_job` from `CaptureResult.parsed_os`.
- **`PyatsComplianceRun.golden`/`.snapshot` FKs softened to `SET_NULL`** (migration `0006`): compliance history survives golden/snapshot deletion (audit contract, consistent with `source_snapshot`). `null=True` on both.
- **`golden_parse.py`** (new module): worker-only Genie parser harness. Imports Genie lazily so the module is importable in the web process without genie installed (ADR-0003 invariant preserved). `GoldenParseError` surfaces parse failures to the compliance job, which records them as an `error` row.
- **Compliance job needs Genie installed** (unlike the diff job, which operates on persisted JSONB). The `pyats` worker image already installs `pyats[full]`; the README and worker docs make this clear.
- **The `run_compliance` job-level e2e test** (`test_golden_parse.py::TestComplianceE2E`) is the regression test for the original shape-mismatch bug: a matching golden must classify as `compliant`, not `drift`. It requires Genie installed and skips cleanly when absent.

## References

- [ATW-64](/ATW/issues/ATW-64) — the shape-mismatch bug and CTO fix-path decision (Option 1).
- [ATW-61](/ATW/issues/ATW-61) — CTO architectural review where the decision was recorded.
- [ATW-15](/ATW/issues/ATW-15) — parent compliance-engine issue.
- [ADR-0003](0003-netbox46-migration-and-worker-toolchain.md) — web process is Genie-free invariant.
- `netbox_pyats/golden_parse.py` — the parser harness.
- `netbox_pyats/compliance.py` — the compliance engine (unchanged; receives comparable dicts).
- `netbox_pyats/jobs.py` — the `run_compliance_job` that calls `parse_golden_config_text`.
- `netbox_pyats/migrations/0006_compliance_reland_parsed_os_setnull.py` — the migration.