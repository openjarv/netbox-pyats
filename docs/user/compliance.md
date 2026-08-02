# Compliance engine

The compliance engine classifies a device's running config against an operator-authored "golden" config. This guide explains what it classifies and how the two comparison modes (v2 ordered, v1 set) work.

## What it does

From a device's **PyATS** tab → **Run compliance** picker (shown when the device has ≥1 golden config and ≥1 config/full snapshot), you pick a golden config, a snapshot, and a **Mode**:

- **Ordered (v2, default)** — compares the config lines as an ordered sequence (`difflib.SequenceMatcher`). Catches order-sensitive drift (ACL entry order, route-map sequence, interface definition order). A re-ordered line is reported as a `removed` (at its golden position) + an `added` (at its snapshot position), so re-ordering shows up as drift.
- **Set (v1)** — compares the lines as an order-independent set. A re-ordered config with the same lines classifies as `compliant`. Use this if your configs legitimately vary in section order between captures and you only want "does the device carry the golden lines?".

The `run_compliance` job:

1. loads the golden's `config_text` and the snapshot's raw `data["config_raw"]` running-config text,
2. normalizes both into line sequences (trailing whitespace stripped, blank lines and lone `!` delimiter lines dropped as noise),
3. diffs them in the chosen mode,
4. classifies the outcome,
5. persists a `PyatsComplianceRun` row with the diff tree + summary counts + warnings, and records the `mode` that produced it.

The row is **always created**, even on `error`, so the outcome is visible in-line in the device-page PyATS tab and under **PyATS → PyATS Compliance Runs**. The `mode` is shown as a badge on the run detail, a column in the runs list, and a filter (`?mode=ordered` / `?mode=set`).

## Classification

| Result | Meaning |
|--------|---------|
| `compliant` | the diff between the golden text and the snapshot's raw running-config text has no added/removed lines. |
| `drift` | the diff has any added/removed lines; the diff view shows *what* drifted. In ordered mode, re-ordered lines count as drift. |
| `error` | the golden text is empty, the snapshot has no `config_raw` payload, or the snapshot is `unsupported` / `error`. The row is still created with a warning naming the missing input. |

## Both modes are line-oriented text diff, not Genie-structured diff

The golden `config_text` is compared against the snapshot's raw `show running-config` text (stored on `data["config_raw"]` at capture time). Both are normalized into line sequences and diffed — a matching golden against a matching snapshot (in the same order) classifies as `compliant`.

The comparison is pure-Python and Genie-free: `difflib` (stdlib) for ordered mode, set arithmetic for set mode. No worker-only Genie parse of the golden is needed — `show running-config` has no Genie parser that runs without a live device connection (confirmed against genie 26.6), and pulling a live device into the compliance path would break the "no extra SSH round-trip" contract. The snapshot's `parsed_os` is recorded for future structured-compliance work that has a connected device; the v2 ordered text diff does not consume it. See ADR-0004 §"v2 ordered text diff".

## The diff view

The compliance diff tree has the same JSON-serializable shape as `PyatsSnapshotDiff.diff`, so the Phase 3 `inc/diff_table.html` partial renders it unchanged. The view flattens the tree into a list of `DiffLine` rows (`netbox_pyats.diff.flatten_diff_tree`); each leaf is a config line marked `unchanged` / `added` / `removed`. The compliance-run viewer (`/plugins/pyats/compliance-runs/<pk>/`) renders the same side-by-side before/after table as the diff viewer — a `Path / Before / After` column per leaf with red/green monospace values — plus a result badge (compliant / drift / error), a mode badge (Ordered / Set), a drift indicator, and any warnings.

Duplicate line texts (e.g. two ` ip address` lines from two interfaces) are disambiguated with a `#<n>` suffix on the tree key so each leaf renders distinctly; the un-suffixed line is the common case.

## What the snapshot needs

Compliance uses the `data["config_raw"]` text path, captured on every config/full snapshot since Phase 4. Legacy snapshots (pre-Phase-4) fall back to `data["config"]["raw"]` — but if you have old snapshots without `config_raw`, re-capture for the cleanest compliance path.

The snapshot's `data["config"]` Genie structured dict is still captured and used by the Phase 3 snapshot-vs-snapshot diff; compliance uses the raw text path only.

## Engine layer

The compliance engine (`netbox_pyats.compliance.run_compliance`) is pure-Python and NetBox/RQ/Genie-free at the engine layer, so it is unit-testable without a device. The job wrapper (`netbox_pyats.jobs`) handles the NetBox model loading and the same-device invariant, and passes the operator-selected `mode` through to the engine.

## Related

- [Usage guide](usage.md) — the full capture → diff → compliance workflow.
- [PyATS worker deployment](workers.md) — the `pyats` queue that runs the compliance job.
- [Troubleshooting](troubleshooting.md) — what to check when compliance returns `error` or unexpected `drift`.