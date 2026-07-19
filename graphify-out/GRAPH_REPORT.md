# Graph Report - netbox-pyats  (2026-07-20)

## Corpus Check
- 72 files · ~51,216 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 815 nodes · 1956 edges · 67 communities (43 shown, 24 thin omitted)
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 704 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `598d997d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .has_warnings
- SnapshotKindChoices
- diff_snapshots
- PyatsSnapshot
- .get_enable_secret
- .right_page
- capture_snapshot
- build_testbed
- EncryptDecryptTest
- PyatsCredentialAPITest
- conftest.py
- PyatsCredentialViewTest
- __init__.py
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- What You Must Do When Invoked
- netbox-pyats
- SnapshotStatusChoices
- PyatsSnapshotDiffModelTest
- .get_status_color
- ADR-0002: Multi-vendor graceful degradation pattern
- PyatsCredentialModelTest
- Contributing to netbox-pyats
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- crypto.py
- jobs.py
- netbox-pyats
- PyATS worker deployment
- graphify reference: extra exports and benchmark
- run_compliance
- [0.1.0] - Unreleased
- ADR-0001: Plugin package layout
- PyatsComplianceRunModelTest
- Architecture Decision Records
- PyatsCredentialForm
- graphify reference: query, path, explain
- ComplianceResultChoices
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- PyatsComplianceRunViewTest
- Dev environment bring-up
- Graphify
- dev-worktree.sh
- extraction-spec.md
- 0004_reconcile_netboxmodel_fields.py
- .get_result_color
- .has_drift
- .has_warnings
- .get_password
- .set_enable_secret
- .set_password
- .is_from_snapshot
- .get_status_color
- .has_changes
- .has_warnings

## God Nodes (most connected - your core abstractions)
1. `PyatsSnapshot` - 119 edges
2. `PyatsCredential` - 108 edges
3. `PyatsSnapshotDiff` - 107 edges
4. `PyatsComplianceRun` - 107 edges
5. `PyatsGoldenConfig` - 101 edges
6. `SnapshotKindChoices` - 74 edges
7. `SnapshotTriggerChoices` - 60 edges
8. `SnapshotStatusChoices` - 45 edges
9. `ComplianceResultChoices` - 39 edges
10. `DiffStatusChoices` - 36 edges

## Surprising Connections (you probably didn't know these)
- `CaptureResult` --uses--> `SnapshotKindChoices`  [INFERRED]
  netbox_pyats/capture.py → netbox_pyats/choices.py
- `CaptureResult` --uses--> `SnapshotStatusChoices`  [INFERRED]
  netbox_pyats/capture.py → netbox_pyats/choices.py
- `PyatsCredentialForm` --uses--> `CredentialProtocolChoices`  [INFERRED]
  netbox_pyats/forms.py → netbox_pyats/choices.py
- `PyatsGoldenConfigForm` --uses--> `CredentialProtocolChoices`  [INFERRED]
  netbox_pyats/forms.py → netbox_pyats/choices.py
- `PyatsComplianceRun` --uses--> `CredentialProtocolChoices`  [INFERRED]
  netbox_pyats/models.py → netbox_pyats/choices.py

## Import Cycles
- None detected.

## Communities (67 total, 24 thin omitted)

### Community 1 - "SnapshotKindChoices"
Cohesion: 0.19
Nodes (29): CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, GoldenConfigSourceChoices, How a credential is assigned.      ``device`` credentials attach to a single Net, What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Connection protocol for a PyATS credential., Outcome of a snapshot diff (Phase 3, ATW-14).      ``success`` means a structure (+21 more)

### Community 2 - "diff_snapshots"
Cohesion: 0.06
Nodes (28): Any, _diff_dict(), _diff_list(), diff_snapshots(), _diff_value(), DiffResult, _leaf_type(), _node_status() (+20 more)

### Community 3 - "PyatsSnapshot"
Cohesion: 0.05
Nodes (123): Meta, PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsSnapshotDiffSerializer, PyatsSnapshotSerializer, Serializer for the PyatsSnapshotDiff model.      Diffs are read-only via the RES, Serializer for the PyatsGoldenConfig model (Phase 4, ATW-15).      Golden config (+115 more)

### Community 5 - ".right_page"
Cohesion: 0.22
Nodes (8): _capture_url_for_device(), _compliance_url_for_device(), _diff_url_for_device(), Return the POST URL for the device-page capture form., Return the POST URL for the device-page diff form (Phase 3, ATW-14)., Return the POST URL for the device-page compliance form (Phase 4, ATW-15)., Return the filtered snapshot-list URL for this device., _snapshot_list_url_for_device()

### Community 6 - "capture_snapshot"
Cohesion: 0.08
Nodes (29): Exception, _capture_config(), capture_snapshot(), capture_snapshot_for_netbox_device(), _capture_state(), CaptureResult, Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u (+21 more)

### Community 7 - "build_testbed"
Cohesion: 0.05
Nodes (37): _build_device_entry(), build_testbed(), is_supported_os(), _iter_devices(), _mgmt_address(), platform_to_pyats_os(), _protocol_for(), _pyats_device_cls() (+29 more)

### Community 8 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 10 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 12 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 15 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 22 - "SnapshotStatusChoices"
Cohesion: 0.12
Nodes (12): Choice sets for the netbox-pyats plugin., Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotStatusChoices, Migration, Migration, Migration, Migration, Models for the netbox-pyats plugin.  Phase 1 (ATW-12) shipped :class:`PyatsCrede (+4 more)

### Community 23 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.12
Nodes (5): TestCase, PyatsSnapshotDiffModelTest, PyatsSnapshotModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Persistence and helper behavior of PyatsSnapshot.

### Community 25 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 26 - "PyatsCredentialModelTest"
Cohesion: 0.18
Nodes (3): TestCase, PyatsCredentialModelTest, Field-level encryption and validation behavior of PyatsCredential.

### Community 27 - "Contributing to netbox-pyats"
Cohesion: 0.18
Nodes (11): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+3 more)

### Community 28 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 29 - "crypto.py"
Cohesion: 0.16
Nodes (14): decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), is_encrypted_token(), Encryption helpers for the plugin-local PyATS credential store.  Field-level enc, Decrypt a Fernet token produced by :func:`encrypt`.      Empty input round-trips (+6 more)

### Community 30 - "jobs.py"
Cohesion: 0.11
Nodes (17): capture_snapshot_job(), enqueue_capture(), enqueue_compliance(), enqueue_diff(), _golden_text_to_config_dict(), NetBox background jobs for the netbox-pyats plugin.  Phase 2 (ATW-13) ships the, RQ worker entry point — capture a snapshot and persist it.      NetBox's :class:, Enqueue a snapshot diff job on the dedicated ``pyats`` RQ queue.      This is th (+9 more)

### Community 31 - "netbox-pyats"
Cohesion: 0.18
Nodes (11): CI, Compatibility matrix, Credential encryption, Development, Installation, Installing pyATS on the worker (required for snapshots), License, Multi-vendor support (+3 more)

### Community 32 - "PyATS worker deployment"
Cohesion: 0.22
Nodes (8): Capturing a snapshot, Option A: the shipped worker image (dev / reference), Option B: install pyats into your own worker, PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, Why a separate queue

### Community 33 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 34 - "run_compliance"
Cohesion: 0.08
Nodes (15): ComplianceResult, Compliance engine — golden config vs. snapshot diff (Phase 4, ATW-15).  :func:`r, Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift)., Compare a golden config dict against a snapshot's config dict and classify., run_compliance(), Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15).  Pure-Python: exerci (+7 more)

### Community 35 - "[0.1.0] - Unreleased"
Cohesion: 0.29
Nodes (6): [0.1.0] - Unreleased, Added, Changelog, Compatibility, Dev, Fixed

### Community 36 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 37 - "PyatsComplianceRunModelTest"
Cohesion: 0.15
Nodes (5): TestCase, PyatsComplianceRunModelTest, PyatsGoldenConfigModelTest, Persistence and helper behavior of PyatsComplianceRun (Phase 4, ATW-15)., Persistence and helper behavior of PyatsGoldenConfig.

### Community 39 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 40 - "PyatsCredentialForm"
Cohesion: 0.25
Nodes (5): PyatsCredentialForm, PyatsGoldenConfigForm, Create/edit form for a PyATS Golden Config (Phase 4, ATW-15).      The operator, Create/edit form for a PyATS Credential.      Plaintext password/enable_secret a, NetBoxModelForm

### Community 41 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 42 - "ComplianceResultChoices"
Cohesion: 0.14
Nodes (6): ComplianceResultChoices, Outcome of a compliance run (Phase 4, ATW-15).      ``compliant`` means the devi, APITestCase, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest, REST API tests for the Phase 4 models (PyatsGoldenConfig, PyatsComplianceRun).

### Community 43 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 44 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 45 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 50 - "PyatsComplianceRunViewTest"
Cohesion: 0.14
Nodes (4): TestCase, PyatsComplianceRunViewTest, PyatsGoldenConfigViewTest, View tests for the Phase 4 compliance views (ATW-15).  Requires a running NetBox

### Community 51 - "Dev environment bring-up"
Cohesion: 0.20
Nodes (9): Bring-up, Dev environment bring-up, Prerequisites, Remote access, Resource limits, Teardown, Troubleshooting, Working in parallel (+1 more)

### Community 52 - "Graphify"
Cohesion: 0.22
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 53 - "dev-worktree.sh"
Cohesion: 0.61
Nodes (7): cmd_add(), cmd_remove(), cmd_up(), die(), next_free_port(), dev-worktree.sh script, usage()

## Knowledge Gaps
- **119 isolated node(s):** `pyats-entrypoint.sh script`, `pyats-worker-entrypoint.sh script`, `Migration`, `Migration`, `Migration` (+114 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PyatsCredential` connect `PyatsSnapshot` to `SnapshotKindChoices`, `.get_enable_secret`, `build_testbed`, `PyatsCredentialForm`, `PyatsCredentialAPITest`, `ComplianceResultChoices`, `PyatsCredentialViewTest`, `crypto.py`, `SnapshotStatusChoices`, `PyatsCredentialModelTest`, `.get_password`, `.set_enable_secret`, `.set_password`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `.has_warnings`, `SnapshotKindChoices`, `PyatsComplianceRunModelTest`, `PyatsCredentialForm`, `ComplianceResultChoices`, `PyatsComplianceRunViewTest`, `SnapshotStatusChoices`, `PyatsSnapshotDiffModelTest`, `.get_status_color`, `jobs.py`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `PyatsComplianceRun` connect `PyatsSnapshot` to `SnapshotKindChoices`, `PyatsComplianceRunModelTest`, `PyatsCredentialForm`, `ComplianceResultChoices`, `PyatsComplianceRunViewTest`, `SnapshotStatusChoices`, `.get_result_color`, `.has_drift`, `.has_warnings`, `jobs.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshot` has 86 INFERRED edges - model-reasoned connections that need verification._
- **Are the 81 inferred relationships involving `PyatsCredential` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsCredential` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 80 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 79 inferred relationships involving `PyatsComplianceRun` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsComplianceRun` has 79 INFERRED edges - model-reasoned connections that need verification._