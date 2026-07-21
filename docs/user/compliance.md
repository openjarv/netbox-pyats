# Compliance engine

The compliance engine classifies a device's running config against an operator-authored "golden" config. This guide explains what it classifies, how the v1 line-set diff works, and what is deferred to v2.

## What it does

From a device's **PyATS** tab → **Run compliance** picker (shown when the device has ≥1 golden config and ≥1 config/full snapshot), you pick a golden config and a snapshot. The `run_compliance` job:

1. loads the golden's `config_text` and the snapshot's raw `data["config_raw"]` running-config text,
2. normalizes both into line sets (trailing whitespace stripped, blank lines and lone `!` delimiter lines dropped as noise),
3. diffs them as a set,
4. classifies the outcome,
5. persists a `PyatsComplianceRun` row with the diff tree + summary counts + warnings.

The row is **always created**, even on `error`, so the outcome is visible in-line in the device-page PyATS tab and under **Plugins → PyATS → PyATS Compliance Runs**.

## Classification

| Result | Meaning |
|--------|---------|
| `compliant` | the line-set diff between the golden text and the snapshot's raw running-config text has no added/removed lines. |
| `drift` | the diff has any added/removed lines; the diff tree shows *what* drifted. |
| `error` | the golden text is empty, the snapshot has no `config_raw` payload, or the snapshot is `unsupported` / `error`. The row is still created with a warning naming the missing input. |

## v1 is line-oriented text diff, not Genie-structured diff

The golden `config_text` is compared against the snapshot's raw `show running-config` text (stored on `data["config_raw"]` at capture time). Both are normalized into line sets and diffed as a set — a matching golden against a matching snapshot classifies as `compliant`.

The diff is **order-independent**: a re-ordered config is still compliant (correct for "does the device carry the golden lines?"), but it will miss order-sensitive drift (e.g. ACL entry order). Ordered/structured compliance (e.g. "interface X must have MTU 1500") is deferred to v2, where the golden can be parsed with the same Genie parser the snapshot used (requiring a device connection or a parser-only harness).

## The diff tree

The compliance diff tree has the same JSON-serializable shape as `PyatsSnapshotDiff.diff`, so the Phase 3 `inc/diff_tree.html` partial renders it unchanged. Each leaf is a config line marked `unchanged` / `added` / `removed`. The compliance-run viewer (`/plugins/pyats/compliance-runs/<pk>/`) renders the same collapsible before/after tree as the diff viewer, plus a result badge (compliant / drift / error), a drift indicator, and any warnings.

## What the snapshot needs

Compliance uses the new `data["config_raw"]` text path, captured on every config/full snapshot since Phase 4. Legacy snapshots (pre-Phase-4) fall back to `data["config"]["raw"]` — but if you have old snapshots without `config_raw`, re-capture for the cleanest compliance path.

The snapshot's `data["config"]` Genie structured dict is still captured and used by the Phase 3 snapshot-vs-snapshot diff; compliance uses the raw text path only.

## Engine layer

The compliance engine (`netbox_pyats.compliance.run_compliance`) is pure-Python and NetBox/RQ/Genie-free at the engine layer, so it is unit-testable without a device. The job wrapper (`netbox_pyats.jobs`) handles the NetBox model loading and the same-device invariant.

## Related

- [Usage guide](usage.md) — the full capture → diff → compliance workflow.
- [PyATS worker deployment](workers.md) — the `pyats` queue that runs the compliance job.
- [Troubleshooting](troubleshooting.md) — what to check when compliance returns `error` or unexpected `drift`.