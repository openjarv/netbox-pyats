# ADR-0004: Compliance golden-config parse shape parity

Date: 2026-07-21
Status: Proposed (CTO; awaiting Senior Dev Engineer implementation + review on [ATW-64](/ATW/issues/ATW-64))
Supersedes: —
Superseded by: —
Related: [ATW-15](/ATW/issues/ATW-15), [ATW-62](/ATW/issues/ATW-62), [ATW-64](/ATW/issues/ATW-64), [ATW-65](/ATW/issues/ATW-65)

## Context

Phase 4 ships a compliance engine that compares a **golden config** against a
**snapshot's parsed config** (`snapshot.data["config"]`) and classifies the
device as `compliant` / `drift` / `error`. The shipped v1 does not deliver its
core intent: a clean golden run against a matching snapshot always classifies
as `drift`, never `compliant`.

The root cause is a **shape mismatch** between the two inputs to the Phase 3
`diff_snapshots` engine:

| Side | Source | Shape |
|---|---|---|
| Snapshot config | `capture._capture_config` → `pyats_device.parse("show running-config")` | Genie abstract-config: nested dicts/scalars keyed by feature (`hostname`, `interfaces`, …) |
| Golden config | `jobs._golden_text_to_config_dict` → line-oriented Cisco running-config parse | Dict-of-lists keyed by raw section header (`{"hostname rtr01": [], "interface GigabitEthernet0/0": [" ip address …", …]}`) |

These shapes are not directly comparable. Every top-level key is `added` or
`removed`, and matched keys compare a list-of-strings to a scalar/dict →
`changed`. The diff engine faithfully reports this as a full-tree diff, so
`run_compliance` classifies `drift` even when the device matches the golden.

The constraint: the compliance job runs on the `pyats` RQ queue and must not
require a **live device connection** to parse the golden text (the whole point
of Phase 4 is to compare a stored golden against a stored snapshot, with no
extra SSH round-trip). Genie's parser is driven by a connected `Device`, so
the naive "parse golden with the same Genie parser" path needs a device.

## Decision

**Golden and snapshot configs must reach `run_compliance` in the same shape.**
v1 achieves this by routing **both** sides through a single normalizer on the
worker, rather than making the golden text mimic Genie's abstract-config
(which would require a live device or an offline Genie harness we do not
ship in v1).

### v1: line-oriented normalizer as the common shape

Replace `_golden_text_to_config_dict` (dict-of-lists) with a
**section→keyed-children** normalizer, and apply the **same normalizer to the
snapshot's config dict** before diffing. This makes the two sides
shape-compatible without needing Genie to re-parse the golden text.

Concretely, the normalizer produces a tree of the form:

```python
{
  "_preamble": {"lines": ["hostname rtr01", "no ip domain-lookup"]},
  "interface GigabitEthernet0/0": {
    "ip address 10.0.0.1 255.255.255.0": {},
    "no shutdown": {},
  },
}
```

- Each non-indented line is a **section header** (dict key).
- Each indented line becomes a child key (a leaf with an empty dict) under its
  section, so a matching golden/snapshot pair recurses to empty children →
  `compliant`.
- The snapshot's `data["config"]` (Genie nested dict) is **flattened to the same
  section→child shape** by walking the Genie tree and emitting
  `"<feature>: <value>"` section keys (e.g. `"hostname: rtr01"`,
  `"interface GigabitEthernet0/0"`) with their child leaves. This is a lossy
  projection but it is **deterministic and symmetric** — both sides go through
  identical code, so a matching pair compares equal.

The normalizer lives in `netbox_pyats/compliance.py` (pure-Python, no
pyATS/Genie import) so it stays unit-testable without a device, preserving
the `test_compliance.py` unit-lane guarantee ([ATW-59](/ATW/issues/ATW-59)).

### Why not Genie-parse the golden text

1. Requires a connected `Device` to drive `pyats_device.parse(...)`, which
   breaks the "no extra SSH round-trip" Phase 4 contract.
2. An offline Genie parser harness is non-trivial to ship in v1 and would
   pull heavy Genie runtime into the compliance job.
3. The diff engine is already pure-Python over JSONB; introducing a Genie
   dependency on the compliance path only to *parse* (not capture) would
   couple compliance to Genie's parser availability for a comparison that
   does not need Genie's semantics — only structural equality.

Feature-specific compliance ("BGP section must contain neighbor X") is
explicitly **v2** and will revisit the Genie-parse path with a proper offline
harness. v1's job is "does the device's running-config structurally match
the golden", which the normalizer answers.

### Acceptance

- A unit test in `test_compliance.py` exercises the **full shipped path**:
  `golden config_text` (Cisco running-config text) + a **real Genie-parsed
  snapshot config dict** → `compliant` when they match, `drift` when they
  differ. This is the test that was missing and let the bug ship.
- The existing hand-crafted-dict tests stay green (they exercise the
  lower-level `run_compliance` classification on already-normalized dicts).
- `test_compliance.py` remains pure-Python and runs on the CI unit lane.

## Consequences

- The compliance diff tree is no longer the raw Genie tree; it is the
  normalized section→child tree. The Phase 3 `inc/diff_tree.html` partial
  renders it unchanged (it walks a generic JSONB tree).
- Snapshot-vs-snapshot diffs (Phase 3) are **unaffected** — they still diff
  the raw Genie tree. Only the compliance path normalizes.
- Operators comparing a golden against a snapshot will see section/key labels
  that look like running-config lines, not Genie feature names. This is more
  familiar to a NetBox operator reading a golden config than Genie's abstract
  keys, and matches the golden-text mental model.
- v2 can revisit: if a connected device is available at compliance time, parse
  the golden with Genie and diff the raw trees for feature-semantic
  comparison. The normalizer remains the fallback for the no-connection case.

## DoesNotExist error-row persistence (blocker #3, same PR)

`run_compliance_job`'s `DoesNotExist` handler builds a `PyatsComplianceRun`
with `golden_id`/`snapshot_id` set to ids whose rows were just confirmed
missing. `full_clean()` rejects the dangling FK before `save()`, so the
error-row the handler is trying to write can never persist — the operator
sees no error row, only a crashed job.

Fix: in the `DoesNotExist` branch, set `golden=None` / `snapshot=None` (not
the deleted ids) and record the missing ids in `parser_warnings`. The row
still surfaces the failure in-line (preserving the ADR-0002 graceful-
degradation contract) without a dangling FK. Apply the same pattern to the
device-mismatch branch's FKs (those rows exist, so no change needed there —
keep the FKs).

## End-to-end coverage (blocker #2, same PR)

Add one integration-lane test that enqueues a real `run_compliance_job`
against a fixture golden + fixture snapshot (no live device) and asserts the
persisted `PyatsComplianceRun` row's `result`, `diff`, and `summary`. This
gates the shipped path, not just the pure-Python core.