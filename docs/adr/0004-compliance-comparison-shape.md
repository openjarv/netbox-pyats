# ADR-0004: Compliance comparison shape — line-oriented raw-text diff (Option 3)

- **Status:** Accepted (revised 2026-07-21 — supersedes the Option 1 draft)
- **Date:** 2026-07-21
- **Supersedes:** the Option 1 ("Genie parser harness") draft of this same ADR, which was rendered unachievable by the empirical finding below.
- **Related:** [ATW-64](/ATW/issues/ATW-64), [ATW-15](/ATW/issues/ATW-15), [ATW-61](/ATW/issues/ATW-61), [ATW-65](/ATW/issues/ATW-65), [ADR-0003](0003-netbox46-migration-and-worker-toolchain.md), `netbox_pyats/compliance.py`, `netbox_pyats/jobs.py`, `netbox_pyats/capture.py`

## Context

Phase 4 (ATW-15) shipped a compliance engine that compares an operator-authored golden running-config against a captured snapshot's parsed config. The first implementation (PR #16, reverted on `main` as `53ccb75`) parsed the golden text with a lightweight line-oriented parser into `{section_header_str: [raw_line_str, ...]}` — a dict of lists of raw strings. The snapshot's `data["config"]` was assumed to be Genie's structured abstract-config dict (nested dicts/scalars). The two shapes are not directly comparable: every top-level key is `added` on one side or `removed` on the other, and matched keys compare a list-of-strings to a scalar/dict → `changed`. **A clean golden run against a matching snapshot always classified as `drift`, never `compliant`** — the compliance engine was structurally broken. See [ATW-64](/ATW/issues/ATW-64) for the full bug analysis.

Three options were considered for making both sides comparable:

1. **Genie parser harness on the worker** — parse the golden text with the same Genie parser the snapshot used, on the `pyats` worker, via a parser-only harness (no live device).
2. **Parse on save** — parse the golden text into a structured dict at authoring time (in the form/view when the golden config row is saved).
3. **Line-oriented both sides** — store raw `show running-config` text on `PyatsSnapshot` and diff raw text vs. raw golden text line-by-line.

## Empirical finding (Genie 26.6, verified 2026-07-21)

**Option 1 is structurally unachievable in Genie 26.6.** There is no bare `show running-config` parser registered for `iosxe` (or `ios`) in this version. Verified three ways:

- `genie.libs.parser.utils.get_parser("show running-config", Device(os="iosxe"))` raises `ParserNotFound` (exact and `fuzzy=True`).
- `genie.abstract.Lookup.from_device(Device(os="iosxe"))` exposes no `parser` package (`KeyError`).
- Direct enumeration of `genie/libs/parser/iosxe/show_run.py` shows only **section-specific** parsers (`ShowRunInterface`, `ShowRunningConfigAAAUsername`, `ShowRunMdnsSd`, `ShowRunInterfaceAllSectionInterface`, `show running-config | section bgp`, `show running-config aaa`, `show running-config nve`, `show running-config vrf`, …) — **zero** bare `show running-config` parsers.

A connected device's `parse("show running-config")` uses the **same** `get_parser` registry that the unconnected probe does — `Device.parse` is bound at connect time by the connection plugin, which dispatches to the same parser lookup. There is no separate runtime path. In production, `capture._capture_config`'s `pyats_device.parse("show running-config")` would therefore fall through to the raw-text fallback `{"raw": ..., "_parser_error": "ParserNotFound..."}` — meaning **the snapshot side is also unstructured in practice for iosxe**, not just the golden side. The original compliance engine's premise (`snapshot.data["config"]` is Genie-structured) does not hold.

This was not a known limitation when Option 1 was selected; it surfaced when the Senior Dev Engineer ran the e2e test against the installed Genie and escalated (ATW-64 comment `4e16128a`).

## Decision

**Option 3: line-oriented raw-text diff, both sides.**

Compliance compares the **raw text** of the golden config against the **raw text** of the snapshot's running config, both as plain strings:

- `data["config_raw"]` (new) on `PyatsSnapshot` carries the raw `show running-config` text captured by `execute("show running-config")` alongside the (now-fallback) structured `data["config"]`.
- `golden.config_text` is the raw golden text (unchanged — authoring stays a plain text field).
- `run_compliance(golden_text, snapshot_text)` normalizes both into line sets (dropping blank lines and lone `!` delimiters, stripping trailing whitespace), diffs them as sets, and classifies `compliant` (no added/removed) / `drift` (any added/removed) / `error` (either side empty).

This is what the working-tree `compliance.py` already implements (the SDE's rewrite is correct). The Phase 3 `inc/diff_tree.html` partial renders the result unchanged because `run_compliance` produces a diff tree with the same `{name, type, status, children}` shape as `diff_snapshots`, with leaves keyed by line.

### Why Option 3 (corrected)

- **Option 1 is not achievable** in Genie 26.6 (see finding above). Composing the bare config dict from the ~22 section-specific parsers is fragile, version-coupled, and a maintenance trap — it would break on any Genie parser registry change and is not a credible v1 contract.
- **Pinning a different Genie version for a bare parser is unverified and locks the project to one version.** No evidence a version ships a bare `show running-config` parser for iosxe; pinning a runtime dependency on an unverified assumption is the wrong architectural move.
- **Option 2 (parse on save) is rejected unchanged** — it breaks the ADR-0003 invariant (web process is Genie-free) or invents a second parser (the shape-mismatch bug again).
- **Option 3 is honest about what v1 can deliver.** The raw-text path runs on the `pyats` worker with no extra device connection, is unit-testable without Genie, and a matching golden against a matching snapshot classifies as `compliant` — the Phase 4 intent. The structured "what drifted, where" tree is preserved at the line level.

### Documented v1 limitation

Line-set diff is order-independent (a re-ordered config classifies as `compliant`). This is correct for the common "does the device carry the golden lines?" question but misses order-sensitive drift (e.g. ACL entry order). Ordered/structured compliance is **v2** — it requires either (a) a Genie version with a bare config parser, (b) a standalone config parser outside Genie, or (c) an ordered line-diff. v2 is explicitly out of scope for the re-land.

## Consequences

- **`PyatsSnapshot.parsed_os`** (new field, migration `0006`): retained. Records the pyATS os at capture time so future structured compliance (v2) can select a parser even after the device is deleted. Set by `capture_snapshot_job` from `CaptureResult.parsed_os`. Not used by the v1 raw-text compliance path, but cheap to carry and unblocks v2.
- **`PyatsComplianceRun.golden`/`.snapshot` FKs softened to `SET_NULL`** (migration `0006`): compliance history survives golden/snapshot deletion (audit contract, consistent with `source_snapshot`). `null=True` on both. This fix is independent of the comparison-shape decision and lands regardless.
- **`data["config_raw"]`** (new on `PyatsSnapshot.data`): the raw `show running-config` text. Captured by `_capture_config` via `execute("show running-config")` (already in the code path as the parser-failure fallback). `capture.py` is updated to always populate `config_raw` on config/full captures, not only on parser failure.
- **`golden_parse.py` is removed.** The Genie parser harness is not needed for the raw-text path. The migration, FK softening, `parsed_os`, and DoesNotExist error-row fix are retained.
- **`compliance.py` signature changes** from `run_compliance(golden_config_dict, snapshot_config_dict)` to `run_compliance(golden_text, snapshot_text)` (both strings). `jobs.py` calls `run_compliance(golden.config_text, snapshot.data.get("config_raw", ""))`. No `parse_golden_config_text` call.
- **Compliance job does NOT need Genie installed** for the v1 raw-text path (the diff operates on strings). This is a simplification — the `pyats` worker still runs it, but Genie is no longer a compliance-job hard dependency.
- **`test_compliance.py`** is rewritten to feed strings (not dicts) and assert the line-set semantics. `test_golden_parse.py` is removed (no Genie harness). The e2e regression gate becomes `test_compliance_job_e2e` in `test_compliance.py`, feeding a golden text + a matching `config_raw` text and asserting `compliant` — no Genie required, runs in the CI unit lane.
- **`capture.py` `_capture_config` docstring/comment corrected:** remove the false claim "The canonical `show running-config` parser exists for every os we map." Document that `data["config"]` is best-effort structured (Genie when a parser exists; raw-text fallback otherwise) and `data["config_raw"]` is the authoritative raw text for compliance.

## References

- [ATW-64](/ATW/issues/ATW-64) — the shape-mismatch bug, the Option 1 draft decision (superseded), and the empirical Genie finding.
- [ATW-61](/ATW/issues/ATW-61) — CTO architectural review where the original Option 1 decision was recorded.
- [ATW-15](/ATW/issues/ATW-15) — parent compliance-engine issue.
- [ATW-65](/ATW/issues/ATW-65) — re-review gate for PR #20, blocked on ATW-64.
- [ADR-0003](0003-netbox46-migration-and-worker-toolchain.md) — web process is Genie-free invariant (preserved; reinforced — v1 compliance no longer needs Genie).
- `netbox_pyats/compliance.py` — the raw-text line-set compliance engine (v1).
- `netbox_pyats/jobs.py` — the `run_compliance_job` that feeds `config_text` + `config_raw`.
- `netbox_pyats/capture.py` — `_capture_config` (corrected) always populates `data["config_raw"]`.
- `netbox_pyats/migrations/0006_compliance_reland_parsed_os_setnull.py` — `parsed_os` + `SET_NULL` FKs.