# Graph Report - .  (2026-07-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1131 nodes · 2758 edges · 100 communities (68 shown, 32 thin omitted)
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 1005 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `790cba22`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CaptureResult
- PyatsJob
- diff_snapshots
- views.py
- run_compliance
- CredentialProtocolChoices
- PyatsSnapshotDiff
- DiffStatusChoices
- jobs.py
- _flagged
- PyatsSnapshotDiffModelTest
- What You Must Do When Invoked
- SnapshotKindChoices
- test_pyatsjob.py
- PyatsSnapshot
- PyatsComplianceRunModelTest
- _cred_resolver_factory
- EncryptDecryptTest
- Troubleshooting
- contributing.md
- test_testbed.py
- platform_to_pyats_os
- PyatsComplianceRunViewTest
- template_content.py
- testbed.py
- test_graphify_scrub_guard.py
- Remote access to the dev NetBox UI over Tailscale
- build_testbed
- test_supported_platforms.py
- DeviceBulkCaptureView
- Contributing to netbox-pyats
- Usage guide
- _extract_snapshot_raw
- ADR-0002: Multi-vendor graceful degradation pattern
- Graphify MCP HTTP server — multi-host / shared-service runbook
- Dev environment bring-up
- PyatsCredentialModelTest
- netbox-pyats
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0004: Compliance golden-config comparison shape
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- graphify reference: extra exports and benchmark
- Graphify
- Compliance engine
- PyATS worker deployment
- PyatsCredentialForm
- PyatsCredentialAPITest
- dev-worktree.sh
- [0.1.0] - Unreleased
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Graphify MCP
- Installation
- TestSupportedPlatformsMap
- PyatsCredentialViewTest
- graphify reference: query, path, explain
- graphify-mcp-key.sh
- netbox-pyats documentation
- __init__.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- entrypoint.sh
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify-scrub-guard.sh
- AGENTS.md
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- 0004_reconcile_netboxmodel_fields.py
- 0006_compliance_run_nullable_fks.py
- 0007_snapshot_parsed_os.py
- 0008_pyatssnapshotdiff_nullable_fks.py
- .get_result_color
- .has_drift
- .has_warnings
- .get_enable_secret
- .get_password
- .set_enable_secret
- .set_password
- .is_from_snapshot
- .get_status_color
- .related_result
- .get_status_color
- .has_warnings
- .get_status_color
- .has_changes
- .has_warnings
- extraction-spec.md
- netbox-pyats

## God Nodes (most connected - your core abstractions)
1. `PyatsSnapshot` - 145 edges
2. `PyatsSnapshotDiff` - 131 edges
3. `PyatsJob` - 129 edges
4. `PyatsCredential` - 124 edges
5. `PyatsComplianceRun` - 122 edges
6. `PyatsGoldenConfig` - 116 edges
7. `SnapshotKindChoices` - 90 edges
8. `SnapshotTriggerChoices` - 70 edges
9. `SnapshotStatusChoices` - 56 edges
10. `DiffStatusChoices` - 44 edges

## Surprising Connections (you probably didn't know these)
- `PyatsCredentialSerializer` --uses--> `PyatsComplianceRun`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsCredential`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsGoldenConfig`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsJob`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsSnapshot`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py

## Import Cycles
- None detected.

## Communities (100 total, 32 thin omitted)

### Community 0 - "CaptureResult"
Cohesion: 0.06
Nodes (33): Exception, _capture_config(), capture_snapshot(), capture_snapshot_for_netbox_device(), _capture_state(), CaptureResult, Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u (+25 more)

### Community 1 - "PyatsJob"
Cohesion: 0.09
Nodes (53): Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotTriggerChoices, PyatsComplianceRun, PyatsGoldenConfig, PyatsJob, A golden / reference running-config for a NetBox Device (Phase 4, ATW-15)., One compliance check result: golden config vs. captured snapshot (Phase 4, ATW-1, One plugin job-tracking row across capture / diff / compliance / batch (Phase 5, (+45 more)

### Community 2 - "diff_snapshots"
Cohesion: 0.06
Nodes (28): Any, _diff_dict(), _diff_list(), diff_snapshots(), _diff_value(), DiffResult, _leaf_type(), _node_status() (+20 more)

### Community 3 - "views.py"
Cohesion: 0.15
Nodes (39): PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsSnapshotDiffSerializer, PyatsSnapshotSerializer, Serializer for the PyatsSnapshotDiff model.      Diffs are read-only via the RES, Serializer for the PyatsCredential model.      The ``password`` and ``enable_sec (+31 more)

### Community 4 - "run_compliance"
Cohesion: 0.07
Nodes (17): ComplianceResult, _normalize_lines(), Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift)., Normalize a running-config text into a list of comparable lines.      Drops blan, Compare a golden config text against a snapshot's raw config text and classify., Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_ (+9 more)

### Community 5 - "CredentialProtocolChoices"
Cohesion: 0.08
Nodes (28): CredentialProtocolChoices, CredentialScopeChoices, Choice sets for the netbox-pyats plugin., How a credential is assigned.      ``device`` credentials attach to a single Net, Connection protocol for a PyATS credential., decrypt(), _derive_fernet_key_from_secret_key(), encrypt() (+20 more)

### Community 6 - "PyatsSnapshotDiff"
Cohesion: 0.11
Nodes (29): Meta, Meta, Meta, PyatsCredentialType, PyatsJobType, PyatsSnapshotDiffType, PyatsSnapshotType, Query (+21 more)

### Community 7 - "DiffStatusChoices"
Cohesion: 0.17
Nodes (32): ComplianceResultChoices, DiffStatusChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices, Outcome of a compliance run (Phase 4, ATW-15).      ``compliant`` means the devi, Kind of plugin job a :class:`PyatsJob` row tracks (Phase 5, ATW-16).      Extend, Lifecycle status of a :class:`PyatsJob` row (Phase 5, ATW-16).      Extends ADR- (+24 more)

### Community 8 - "jobs.py"
Cohesion: 0.11
Nodes (28): BaseException, batch_capture_job(), capture_snapshot_job(), _create_pyats_job(), enqueue_batch_capture(), enqueue_capture(), enqueue_compliance(), enqueue_diff() (+20 more)

### Community 9 - "_flagged"
Cohesion: 0.13
Nodes (7): _flagged(), Regression test for the ATW-116 secret/PII detection allowlist/regex.  Validates, Return list of (rule_id, matched_segment) the gitleaks rules would flag., Concrete leaks that MUST be flagged (the ATW-114 regression set)., Placeholder / RFC1918 / loopback forms that MUST NOT be flagged., SecretDetectionNegativeCases, SecretDetectionPositiveCases

### Community 10 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.09
Nodes (8): TestCase, PyatsSnapshotDiffModelTest, PyatsSnapshotModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Persistence and helper behavior of PyatsSnapshot., Regression for ATW-68: a diff error row with before/after NULL must         roun, Regression for ATW-68: ``run_diff_job``'s ``DoesNotExist`` branch must     write, RunDiffJobDoesNotExistTest

### Community 11 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 12 - "SnapshotKindChoices"
Cohesion: 0.11
Nodes (10): What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotKindChoices, SnapshotStatusChoices, APITestCase, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest, REST API tests for the Phase 4 models (PyatsGoldenConfig, PyatsComplianceRun). (+2 more)

### Community 13 - "test_pyatsjob.py"
Cohesion: 0.10
Nodes (8): DeviceBulkCaptureViewTest, DiffJobPyatsJobPlumbingTest, TestCase, PyatsJobModelTest, Tests for the PyatsJob model + job-callable side effects + batch summary (Phase, ADR-0005 §3 plumbing for ``run_diff_job`` (Phase 5, ATW-16)., Persistence + helpers for PyatsJob (Phase 5, ATW-16)., The device-list bulk "PyATS capture" view renders its confirmation     form (Pha

### Community 14 - "PyatsSnapshot"
Cohesion: 0.15
Nodes (16): PyatsSnapshot, One captured config/state/full snapshot for a NetBox Device.      Populated by t, Meta, PyatsComplianceRunTable, PyatsCredentialTable, PyatsGoldenConfigTable, PyatsJobTable, PyatsSnapshotDiffTable (+8 more)

### Community 15 - "PyatsComplianceRunModelTest"
Cohesion: 0.16
Nodes (5): TestCase, PyatsComplianceRunModelTest, PyatsGoldenConfigModelTest, Persistence and helper behavior of PyatsComplianceRun (Phase 4, ATW-15)., Persistence and helper behavior of PyatsGoldenConfig.

### Community 16 - "_cred_resolver_factory"
Cohesion: 0.22
Nodes (6): _cred_resolver_factory(), FakeCredential, FakeDevice, Return a credential_resolver that always returns ``cred`` (or None)., Duck-typed PyatsCredential (avoids DB/NetBox in unit tests)., TestBuildTestbed

### Community 17 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 18 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 19 - "contributing.md"
Cohesion: 0.20
Nodes (7): Contributing to netbox-pyats, Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 20 - "test_testbed.py"
Cohesion: 0.16
Nodes (7): is_supported_os(), True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)., FakeDeviceType, FakeIPAddress, FakeManufacturer, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS, TestIsSupportedOs

### Community 21 - "platform_to_pyats_os"
Cohesion: 0.30
Nodes (4): platform_to_pyats_os(), Map a NetBox ``Platform`` to a pyATS ``os`` string.      Returns the :data:`UNSU, FakePlatform, TestPlatformToOs

### Community 22 - "PyatsComplianceRunViewTest"
Cohesion: 0.14
Nodes (4): TestCase, PyatsComplianceRunViewTest, PyatsGoldenConfigViewTest, View tests for the Phase 4 compliance views (ATW-15).  Requires a running NetBox

### Community 23 - "template_content.py"
Cohesion: 0.19
Nodes (12): _capture_url_for_device(), _compliance_url_for_device(), DevicePyATSPanel, _diff_url_for_device(), Template extensions injecting the PyATS tab into the NetBox Device page.  Phase, Return the POST URL for the device-page capture form., Return the POST URL for the device-page diff form (Phase 3, ATW-14)., Return the POST URL for the device-page compliance form (Phase 4, ATW-15). (+4 more)

### Community 24 - "testbed.py"
Cohesion: 0.18
Nodes (13): _build_device_entry(), _iter_devices(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), NetBox → pyATS testbed bridge.  :func:`build_testbed` constructs a :class:`pyats, Return the management IP for a NetBox Device, preferring primary_ip4.      Retur, Pick the pyATS connection protocol from the credential, defaulting to ssh. (+5 more)

### Community 25 - "test_graphify_scrub_guard.py"
Cohesion: 0.33
Nodes (12): CompletedProcess, _make_tree(), Tests for scripts/graphify-scrub-guard.sh.  The scrub guard is the structural ba, repo_root(), _run(), test_clean_tree_passes(), test_leak_detected_in_check_mode(), test_no_graphify_out_is_clean() (+4 more)

### Community 26 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 27 - "build_testbed"
Cohesion: 0.18
Nodes (7): build_testbed(), _pyats_testbed_cls(), Lazy import of pyATS Testbed class.      pyATS is an optional install (worker-on, Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, Summary of a :func:`build_testbed` run.      Keeps track of which devices were i, True if at least one device was supported AND none errored.          ``build_tes, TestbedBuildReport

### Community 28 - "test_supported_platforms.py"
Cohesion: 0.15
Nodes (6): TestCase, Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, Report contents: the static map renders with per-slug device counts., ADR-0001 §6: the data path the report view reads must not import Genie.      The, SupportedPlatformsReportViewTest, TestSupportedPlatformsReportWebProcessSafety

### Community 29 - "DeviceBulkCaptureView"
Cohesion: 0.19
Nodes (8): DeviceBulkCaptureView, DeviceCaptureView, Endpoint the device-page PyATS panel POSTs to.      Accepts a ``kind`` (config /, Bulk "PyATS capture" action on the NetBox device list (Phase 5, ATW-16).      Th, Static "supported platforms" report (Phase 5, ATW-16, Option A).      ADR-0001 §, SupportedPlatformsReportView, PermissionRequiredMixin, View

### Community 31 - "Contributing to netbox-pyats"
Cohesion: 0.17
Nodes (12): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+4 more)

### Community 32 - "Usage guide"
Cohesion: 0.17
Nodes (12): 1 — Add a credential, 2 — Capture a snapshot, 3 — Diff two snapshots, 4 — Add a golden config, 5 — Run compliance, 6 — Browse everything, 7 — Build a testbed programmatically, Multi-vendor support (+4 more)

### Community 33 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 34 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 35 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.18
Nodes (11): Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites, Remote agent wiring (Senior Dev Engineer), Secret rotation (+3 more)

### Community 36 - "Dev environment bring-up"
Cohesion: 0.18
Nodes (11): Bring-up, Dev environment bring-up, Image overrides (compatibility sweeps), Prerequisites, Remote access, Resource limits, Teardown, `test_netbox` already exists / `EOFError` / "terminating connection due to administrator command" (ATW-85) (+3 more)

### Community 37 - "PyatsCredentialModelTest"
Cohesion: 0.18
Nodes (3): TestCase, PyatsCredentialModelTest, Field-level encryption and validation behavior of PyatsCredential.

### Community 38 - "netbox-pyats"
Cohesion: 0.18
Nodes (11): Capture, Compare, Compatibility matrix, Compliance & Jobs, Device-page UI, Documentation, Getting help, License (+3 more)

### Community 39 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 40 - "ADR-0004: Compliance golden-config comparison shape"
Cohesion: 0.20
Nodes (10): Acceptance, ADR-0004: Compliance golden-config comparison shape, Capture change, Consequences, Considered options, Context, Decision, DoesNotExist error-row persistence (blocker #3, same PR) (+2 more)

### Community 41 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 42 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 43 - "Graphify"
Cohesion: 0.25
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 44 - "Compliance engine"
Cohesion: 0.25
Nodes (8): Classification, Compliance engine, Engine layer, Related, The diff tree, v1 is line-oriented text diff, not Genie-structured diff, What it does, What the snapshot needs

### Community 45 - "PyATS worker deployment"
Cohesion: 0.25
Nodes (8): Option A — install pyats into your own worker, Option B — the shipped worker image (reference / dev), PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, What runs on the `pyats` queue, Why a separate queue

### Community 46 - "PyatsCredentialForm"
Cohesion: 0.25
Nodes (5): PyatsCredentialForm, PyatsGoldenConfigForm, Create/edit form for a PyATS Golden Config (Phase 4, ATW-15).      The operator, Create/edit form for a PyATS Credential.      Plaintext password/enable_secret a, NetBoxModelForm

### Community 48 - "dev-worktree.sh"
Cohesion: 0.61
Nodes (7): cmd_add(), cmd_remove(), cmd_up(), die(), next_free_port(), dev-worktree.sh script, usage()

### Community 49 - "[0.1.0] - Unreleased"
Cohesion: 0.29
Nodes (7): [0.1.0] - Unreleased, Added, Added, Changelog, Compatibility, Dev, Fixed

### Community 50 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 51 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 52 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 53 - "Graphify MCP"
Cohesion: 0.29
Nodes (7): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, remote / HTTP config (multi-host, opt-in), stdio config (single-host, default), Switching from stdio to HTTP, Tools exposed (both transports), When to use which transport

### Community 54 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 57 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 58 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 59 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 60 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 61 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 62 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 63 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **215 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-entrypoint.sh script`, `pyats-worker-entrypoint.sh script`, `Migration` (+210 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PyatsCredential` connect `PyatsSnapshotDiff` to `PyatsJob`, `views.py`, `CredentialProtocolChoices`, `PyatsCredentialModelTest`, `DiffStatusChoices`, `SnapshotKindChoices`, `PyatsCredentialForm`, `PyatsSnapshot`, `.get_enable_secret`, `.get_password`, `.set_enable_secret`, `.set_password`, `PyatsCredentialAPITest`, `testbed.py`, `PyatsCredentialViewTest`, `build_testbed`, `DeviceBulkCaptureView`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `CaptureResult`, `PyatsJob`, `views.py`, `CredentialProtocolChoices`, `PyatsSnapshotDiff`, `DiffStatusChoices`, `jobs.py`, `PyatsSnapshotDiffModelTest`, `SnapshotKindChoices`, `test_pyatsjob.py`, `PyatsCredentialForm`, `PyatsComplianceRunModelTest`, `template_content.py`, `PyatsComplianceRunViewTest`, `.get_status_color`, `.has_warnings`, `DeviceBulkCaptureView`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `PyatsSnapshotDiff` connect `PyatsSnapshotDiff` to `CaptureResult`, `PyatsJob`, `views.py`, `CredentialProtocolChoices`, `DiffStatusChoices`, `jobs.py`, `PyatsSnapshotDiffModelTest`, `SnapshotKindChoices`, `test_pyatsjob.py`, `PyatsCredentialForm`, `PyatsSnapshot`, `template_content.py`, `.get_status_color`, `.has_changes`, `.has_warnings`, `DeviceBulkCaptureView`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 108 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshot` has 108 INFERRED edges - model-reasoned connections that need verification._
- **Are the 102 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 102 INFERRED edges - model-reasoned connections that need verification._
- **Are the 98 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsJob` has 98 INFERRED edges - model-reasoned connections that need verification._
- **Are the 97 inferred relationships involving `PyatsCredential` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsCredential` has 97 INFERRED edges - model-reasoned connections that need verification._