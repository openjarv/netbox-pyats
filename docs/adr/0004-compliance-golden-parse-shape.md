# ADR-0004: Compliance golden-config comparison shape

Date: 2026-07-21
Status: Accepted (CTO; implemented on the `phase4-compliance-rereview` branch as PR #20, re-review on [ATW-62](/ATW/issues/ATW-62) and [ATW-64](/ATW/issues/ATW-64))
Supersedes: —
Superseded by: —
Related: [ATW-15](/ATW/issues/ATW-15), [ATW-62](/ATW/issues/ATW-62), [ATW-64](/ATW/issues/ATW-64), [ATW-65](/ATW/issues/ATW-65)

## Context

Phase 4 ships a compliance engine that compares a **golden config** against a
**snapshot's config** and classifies the device as `compliant` / `drift` /
`error`. The shipped v1 (PR #16) did not deliver its core intent: a clean
golden run against a matching snapshot always classified as `drift`, never
`compliant` (filed as [ATW-64](/ATW/issues/ATW-64), blocker in the
[ATW-62](/ATW/issues/ATW-62) code-quality review).

The root cause was a **shape mismatch** between the two inputs to the Phase 3
`diff_snapshots` engine:

| Side | Source (shipped v1) | Shape |
|---|---|---|
| Snapshot config | `capture._capture_config` → `pyats_device.parse("show running-config")` | Genie abstract-config: nested dicts/scalars keyed by feature (`hostname`, `interfaces`, …) |
| Golden config | `jobs._golden_text_to_config_dict` → line-oriented Cisco running-config parse | Dict-of-lists keyed by raw section header (`{"hostname rtr01": [], "interface GigabitEthernet0/0": [" ip address …", …]}`) |

These shapes are not directly comparable. Every top-level key was `added` or
`removed`, and matched keys compared a list-of-strings to a scalar/dict →
`changed`. The diff engine faithfully reported this as a full-tree diff, so
`run_compliance` classified `drift` even when the device matched the golden.

The constraint: the compliance job runs on the `pyats` RQ queue and must not
require a **live device connection** to parse the golden text (the whole point
of Phase 4 is to compare a stored golden against a stored snapshot, with no
extra SSH round-trip). Genie's parser is driven by a connected `Device`, so
the naive "parse golden with the same Genie parser" path needs a device.

## Considered options

1. **Parse golden with the same Genie parser the snapshot used.** Rejected: the
   `show running-config` parser is not in the standard Genie parser registry
   (`get_parser("show running-config", dev)` raises `ParserNotFound`); it is
   driven by Genie's abstract-config engine which requires a connected Device
   / built abstract tree. There is no worker-only harness that parses a
   free-text golden into the Genie abstract-config shape. Pulling a live
   device into the compliance path breaks the "no extra SSH round-trip"
   Phase 4 contract. Confirmed locally with `pyats[full]` 26.6 + `genie` 26.6
   installed.
2. **Store golden as a parsed dict at authoring time** (parse on save in the
   form/view). Rejected: the NetBox web process deliberately does **not**
   install `pyats[full]` (the plugin is importable without it); the parser
   only runs on the worker. Coupling the golden form to the Genie parser
   forces the operator to re-parse on every golden edit and breaks the
   "web process is pyATS-free" boundary (ADR-0001).
3. **Normalize both sides into a section→keyed-children tree** (the original
   ADR-0004 "Proposed" decision). Rejected after CTO review: walking the
   Genie tree and emitting `"<feature>: <value>"` section keys is a lossy
   projection that is non-trivial to write and **Genie-shape-coupled** — every
   Genie release that changes the abstract-config shape breaks the
   normalizer. The normalizer would have to track Genie's per-feature schema
   across the supported OS matrix, which is exactly the maintenance burden
   Phase 4 was designed to avoid.
4. **Line-oriented text diff against the snapshot's raw running-config text**
   (chosen). Capture and store the raw `show running-config` text on the
   snapshot as `data["config_raw"]`, alongside the existing Genie structured
   `data["config"]` (kept for Phase 3 snapshot-vs-snapshot diffs). The
   compliance engine compares the golden `config_text` against the snapshot's
   `config_raw` as a **line-set diff**.

## Decision

**v1 compliance is line-oriented text diff.** The golden `config_text` is
compared against the snapshot's raw `data["config_raw"]` running-config text
(captured at snapshot time and stored as a plain string). Both sides are
normalized into line sets (trailing whitespace stripped; blank lines and lone
`!` delimiter lines dropped as Cisco running-config noise) and diffed as a
**set** (order-independent). A matching golden against a matching snapshot
classifies as `compliant`; a divergence classifies as `drift`.

This:

- **Delivers the Phase 4 intent** ("does the running config match the golden?")
  — a matching golden → `compliant`, the test the original v1 lacked.
- **Runs on the worker with no extra device connection** — the snapshot
  already carries the raw text; the golden is operator-authored text.
- **Is unit-testable without Genie installed** — the pure-Python tests feed
  strings, so `test_compliance.py` runs on the CI unit lane (ATW-59).
- **Is additive and decoupled from Genie's shape** — the snapshot's
  `data["config"]` Genie structured dict is still captured and used by Phase 3
  snapshot-vs-snapshot diffs; compliance uses the new `data["config_raw"]`
  text path. The raw text is stable across Genie releases; the compliance
  engine does not break when Genie's abstract-config shape changes.
- **Makes the docstring honest** — the original v1 docstring claimed a
  "scaffold" parse using the snapshot's parsed config; that scaffold was
  never implemented. The line-oriented path is now what the docstring says.

### v1 line-set diff semantics (documented limitation)

The diff is a **set** comparison (order-independent). This means a
re-ordered config classifies as `compliant` — correct for the common "does
the device carry the golden lines?" question, but it will miss
**order-sensitive drift** (e.g. ACL entry order). A "changed" line in the
running config is reported as a `removed` (the golden's line) + an `added`
(the snapshot's line) — `summary["changed"]` is always 0 for the line-set
diff. Ordered/structured compliance (e.g. "interface X must have MTU 1500",
ACL order) is explicitly **v2**, where the golden can be parsed with the
same Genie parser the snapshot used (requiring a device connection or a
parser-only harness we do not ship in v1).

The diff tree has the same shape as `PyatsSnapshotDiff.diff` (a `dict` root
node with `children` keyed by line, each child a `leaf` node with `status`
`unchanged` / `added` / `removed`) so the Phase 3 `inc/diff_tree.html`
partial renders it unchanged (no new rendering code).

### Capture change

`capture._capture_config` now returns a `(config_dict, raw_text)` pair.
`capture_snapshot` stores both on config/full snapshots:
`data["config"]` (the Genie structured dict, for Phase 3 diffs) and
`data["config_raw"]` (the raw text, for Phase 4 compliance). On
parser-failure-with-execute-success, `config_raw` is still populated from
the successful `execute("show running-config")` call; on
parser-failure-and-execute-failure, `config_raw` is `""` and compliance
against that snapshot classifies as `error` with "snapshot raw config is
empty" (graceful degradation, ADR-0002).

Legacy snapshots captured before `config_raw` was added (migration 0006
onward populates it on new captures) fall back to `data["config"]["raw"]`
if the parser had failed at capture time (the pre-rework fallback path
already stored raw text under that key).

## Acceptance

- A unit test in `test_compliance.py` exercises the **full shipped path**:
  `golden config_text` (Cisco running-config text) + a realistic snapshot
  `config_raw` text → `compliant` when they match, `drift` when they differ.
  This is the test that was missing in the original v1 and let the bug ship.
  (`TestEndToEndCompliancePath` — 4 tests covering matching, IP drift,
  interface added, interface missing.)
- The existing hand-crafted-dict tests are replaced by text-based tests
  reflecting the new engine shape (the engine no longer takes dicts).
- `test_compliance.py` and `test_jobs.py` remain pure-Python and run on the
  CI unit lane.
- The compliance diff tree renders unchanged in the Phase 3 viewer (same
  JSONB shape).

## Consequences

- The compliance diff tree is keyed by **config line**, not by Genie feature
  name. Operators comparing a golden against a snapshot see line-level
  `added` / `removed` leaves, which matches the golden-text mental model and
  is more familiar to a NetBox operator reading a running config than Genie's
  abstract keys.
- Snapshot-vs-snapshot diffs (Phase 3) are **unaffected** — they still diff
  the raw Genie tree (`data["config"]`). Only the compliance path uses
  `config_raw`.
- Snapshot rows now carry an extra `config_raw` string in their JSONB
  payload — a small size increase (the raw text is roughly the same size as
  the Genie dict it was parsed from). Acceptable for the compliance value it
  unlocks.
- v2 can revisit: if a connected device is available at compliance time,
  parse the golden with Genie and diff the raw trees for feature-semantic
  comparison. The line-oriented path remains the fallback for the
  no-connection case and the default for v1.

## DoesNotExist error-row persistence (blocker #3, same PR)

`run_compliance_job`'s `DoesNotExist` handler builds a `PyatsComplianceRun`
with `golden_id`/`snapshot_id` set to ids whose rows were just confirmed
missing. With the original v1's `on_delete=CASCADE` + non-nullable FKs,
`full_clean()` rejected the dangling FK before `save()`, so the error-row
the handler was trying to write could never persist — the operator saw no
error row, only a crashed job.

Fix (migration `0006_compliance_run_nullable_fks`): make
`PyatsComplianceRun.golden` and `.snapshot` nullable with
`on_delete=SET_NULL`. In the `DoesNotExist` branch, set `golden=None` /
`snapshot=None` and record the missing ids in `parser_warnings`. The row
still surfaces the failure in-line (preserving the ADR-0002 graceful-
degradation contract) without a dangling FK. This matches the Phase 3
`PyatsSnapshotDiff.before` / `.after` nullability (migration 0003), which
solves the same problem for the diff job.

The device-mismatch branch's FKs point at rows that **do** exist, so that
branch keeps the FKs (no nullability needed there).

## End-to-end coverage (blocker #2, same PR)

`test_compliance.py::TestEndToEndCompliancePath` exercises the exact path
the RQ job runs: golden text → snapshot raw text → `run_compliance` →
classification. Four scenarios: matching (compliant), IP address drifted
(drift), interface added on device (drift), interface missing on device
(drift). This is the test the original v1 lacked — CI green masked the bug
because no test fed `_golden_text_to_config_dict(...)` output into
`run_compliance` against a realistic Genie-shaped snapshot. The new tests
feed the same raw text shapes the job extracts from
`PyatsGoldenConfig.config_text` and `PyatsSnapshot.data["config_raw"]`.

`test_jobs.py` covers the snapshot-raw extraction logic (the
`data["config_raw"]` field with a legacy `data["config"]["raw"]` fallback
for snapshots captured before `config_raw` was added) — 7 tests covering
the normal path, legacy fallback, precedence, state-only snapshots,
unsupported snapshots, and corrupt-JSONB defense.