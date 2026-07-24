# Graph Report - .  (2026-07-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1083 nodes · 2681 edges · 91 communities (68 shown, 23 thin omitted)
- Extraction: 63% EXTRACTED · 37% INFERRED · 0% AMBIGUOUS · INFERRED: 1005 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- PyatsSnapshot
- CaptureResult
- diff_snapshots
- views.py
- run_compliance
- DiffStatusChoices
- jobs.py
- build_testbed
- PyatsSnapshotDiffModelTest
- What You Must Do When Invoked
- models.py
- PyatsSnapshotDiff
- SnapshotKindChoices
- PyatsComplianceRunModelTest
- PyatsGoldenConfig
- is_supported_os
- EncryptDecryptTest
- DeviceBulkCaptureView
- urls.py
- Troubleshooting
- SnapshotStatusChoices
- PyatsCredential
- testbed.py
- platform_to_pyats_os
- PyatsGoldenConfigAPITest
- crypto.py
- template_content.py
- Remote access to the dev NetBox UI over Tailscale
- Usage guide
- _extract_snapshot_raw
- ADR-0002: Multi-vendor graceful degradation pattern
- Contributing to netbox-pyats
- Graphify MCP HTTP server — multi-host / shared-service runbook
- Dev environment bring-up
- PyatsCredentialModelTest
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0004: Compliance golden-config comparison shape
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- PyatsJobModelTest
- test_testbed.py
- contributing.md
- graphify reference: extra exports and benchmark
- Graphify
- Compliance engine
- PyATS worker deployment
- PyatsCredentialAPITest
- dev-worktree.sh
- [0.1.0] - Unreleased
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Graphify MCP
- Installation
- SupportedPlatformsReportViewTest
- PyatsCredentialViewTest
- Architecture Decision Records
- PyatsCredentialForm
- graphify reference: query, path, explain
- netbox-pyats
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
- AGENTS.md
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- 0004_reconcile_netboxmodel_fields.py
- 0006_compliance_run_nullable_fks.py
- 0007_snapshot_parsed_os.py
- 0008_pyatssnapshotdiff_nullable_fks.py
- .get_enable_secret
- .is_from_snapshot
- .get_status_color
- .get_status_color
- .has_warnings
- .ok
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

## Communities (91 total, 23 thin omitted)

### Community 0 - "PyatsSnapshot"
Cohesion: 0.10
Nodes (51): Meta, Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotTriggerChoices, PyatsComplianceRun, PyatsJob, PyatsSnapshot, One captured config/state/full snapshot for a NetBox Device.      Populated by t, True if this snapshot row carries parser warnings / error context. (+43 more)

### Community 1 - "CaptureResult"
Cohesion: 0.07
Nodes (26): Exception, _capture_config(), capture_snapshot(), _capture_state(), CaptureResult, Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u, Run parser-based state capture on a connected pyATS Device.      Runs a small, O, Capture a snapshot from a single, already-connected pyATS Device.      This is t (+18 more)

### Community 2 - "diff_snapshots"
Cohesion: 0.06
Nodes (28): Any, _diff_dict(), _diff_list(), diff_snapshots(), _diff_value(), DiffResult, _leaf_type(), _node_status() (+20 more)

### Community 3 - "views.py"
Cohesion: 0.15
Nodes (39): PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsSnapshotDiffSerializer, PyatsSnapshotSerializer, Serializer for the PyatsSnapshotDiff model.      Diffs are read-only via the RES, Serializer for the PyatsCredential model.      The ``password`` and ``enable_sec (+31 more)

### Community 4 - "run_compliance"
Cohesion: 0.07
Nodes (17): ComplianceResult, _normalize_lines(), Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift)., Normalize a running-config text into a list of comparable lines.      Drops blan, Compare a golden config text against a snapshot's raw config text and classify., Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_ (+9 more)

### Community 5 - "DiffStatusChoices"
Cohesion: 0.17
Nodes (39): ComplianceResultChoices, CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices, Outcome of a compliance run (Phase 4, ATW-15).      ``compliant`` means the devi (+31 more)

### Community 6 - "jobs.py"
Cohesion: 0.10
Nodes (32): BaseException, capture_snapshot_for_netbox_device(), Build a single-device testbed, connect, capture, disconnect.      Convenience wr, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, _worker_versions(), batch_capture_job(), capture_snapshot_job(), _create_pyats_job() (+24 more)

### Community 7 - "build_testbed"
Cohesion: 0.16
Nodes (10): build_testbed(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, Summary of a :func:`build_testbed` run.      Keeps track of which devices were i, TestbedBuildReport, _cred_resolver_factory(), FakeCredential, FakeDevice, Return a credential_resolver that always returns ``cred`` (or None). (+2 more)

### Community 8 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.09
Nodes (8): TestCase, PyatsSnapshotDiffModelTest, PyatsSnapshotModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Persistence and helper behavior of PyatsSnapshot., Regression for ATW-68: a diff error row with before/after NULL must         roun, Regression for ATW-68: ``run_diff_job``'s ``DoesNotExist`` branch must     write, RunDiffJobDoesNotExistTest

### Community 9 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 10 - "models.py"
Cohesion: 0.10
Nodes (12): Choice sets for the netbox-pyats plugin., Migration, Migration, Migration, Migration, Migration, Models for the netbox-pyats plugin.  Phase 1 (ATW-12) shipped :class:`PyatsCrede, REST API tests for the PyatsCredential model.  Requires a running NetBox/Django (+4 more)

### Community 11 - "PyatsSnapshotDiff"
Cohesion: 0.14
Nodes (17): PyatsSnapshotDiff, One structured diff between two :class:`PyatsSnapshot` rows of a device.      Po, Map status to a NetBox color label for table badges., Meta, PyatsComplianceRunTable, PyatsCredentialTable, PyatsGoldenConfigTable, PyatsJobTable (+9 more)

### Community 12 - "SnapshotKindChoices"
Cohesion: 0.13
Nodes (11): Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, SnapshotKindChoices, CaptureJobPyatsJobPlumbingTest, DeviceBulkCaptureViewTest, DiffJobPyatsJobPlumbingTest, TestCase, Tests for the PyatsJob model + job-callable side effects + batch summary (Phase (+3 more)

### Community 13 - "PyatsComplianceRunModelTest"
Cohesion: 0.16
Nodes (5): TestCase, PyatsComplianceRunModelTest, PyatsGoldenConfigModelTest, Persistence and helper behavior of PyatsComplianceRun (Phase 4, ATW-15)., Persistence and helper behavior of PyatsGoldenConfig.

### Community 14 - "PyatsGoldenConfig"
Cohesion: 0.17
Nodes (15): Meta, PyatsGoldenConfig, A golden / reference running-config for a NetBox Device (Phase 4, ATW-15)., PyatsComplianceRunIndex, PyatsCredentialIndex, PyatsGoldenConfigIndex, PyatsJobIndex, PyatsSnapshotDiffIndex (+7 more)

### Community 15 - "is_supported_os"
Cohesion: 0.13
Nodes (8): is_supported_os(), True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)., Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, The static map the report renders (Phase 5, ATW-16, Option A)., ADR-0001 §6: the data path the report view reads must not import Genie.      The, TestSupportedPlatformsMap, TestSupportedPlatformsReportWebProcessSafety, TestIsSupportedOs

### Community 16 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 17 - "DeviceBulkCaptureView"
Cohesion: 0.13
Nodes (12): DeviceBulkCaptureView, DeviceCaptureView, DeviceComplianceView, DeviceDiffView, Endpoint the device-page PyATS panel POSTs to.      Accepts a ``kind`` (config /, Endpoint the device-page PyATS panel POSTs to.      Accepts ``before_id`` and ``, Endpoint the device-page PyATS compliance sub-tab POSTs to.      Accepts ``golde, Bulk "PyATS capture" action on the NetBox device list (Phase 5, ATW-16).      Th (+4 more)

### Community 18 - "urls.py"
Cohesion: 0.06
Nodes (8): Encrypt and store the device password (ciphertext only)., Decrypt and return the device password (plaintext)., Encrypt and store the enable/privileged password (ciphertext only)., True if the diff found any added/removed/changed leaves., Map result to a NetBox color label for table badges., True if the diff found any added/removed/changed leaves (drift)., True if this compliance run row carries warnings / error context., The result row this job produced, regardless of type, or None.          Convenie

### Community 19 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 20 - "SnapshotStatusChoices"
Cohesion: 0.14
Nodes (6): Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotStatusChoices, TestCase, PyatsComplianceRunViewTest, PyatsGoldenConfigViewTest, View tests for the Phase 4 compliance views (ATW-15).  Requires a running NetBox

### Community 21 - "PyatsCredential"
Cohesion: 0.18
Nodes (13): Meta, PyatsCredentialType, PyatsJobType, PyatsSnapshotDiffType, PyatsSnapshotType, Query, GraphQL type for the PyatsSnapshot model.      Exposes the full JSONB ``data`` p, GraphQL type for the PyatsSnapshotDiff model (Phase 3, ATW-14).      Exposes the (+5 more)

### Community 22 - "testbed.py"
Cohesion: 0.15
Nodes (15): _build_device_entry(), _iter_devices(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), _pyats_testbed_cls(), NetBox → pyATS testbed bridge.  :func:`build_testbed` constructs a :class:`pyats, Return the management IP for a NetBox Device, preferring primary_ip4.      Retur (+7 more)

### Community 23 - "platform_to_pyats_os"
Cohesion: 0.30
Nodes (4): platform_to_pyats_os(), Map a NetBox ``Platform`` to a pyATS ``os`` string.      Returns the :data:`UNSU, FakePlatform, TestPlatformToOs

### Community 24 - "PyatsGoldenConfigAPITest"
Cohesion: 0.14
Nodes (4): APITestCase, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest, REST API tests for the Phase 4 models (PyatsGoldenConfig, PyatsComplianceRun).

### Community 25 - "crypto.py"
Cohesion: 0.19
Nodes (13): decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), is_encrypted_token(), Encryption helpers for the plugin-local PyATS credential store.  Field-level enc, Decrypt a Fernet token produced by :func:`encrypt`.      Empty input round-trips (+5 more)

### Community 26 - "template_content.py"
Cohesion: 0.19
Nodes (12): _capture_url_for_device(), _compliance_url_for_device(), DevicePyATSPanel, _diff_url_for_device(), Template extensions injecting the PyATS tab into the NetBox Device page.  Phase, Return the POST URL for the device-page capture form., Return the POST URL for the device-page diff form (Phase 3, ATW-14)., Return the POST URL for the device-page compliance form (Phase 4, ATW-15). (+4 more)

### Community 28 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 29 - "Usage guide"
Cohesion: 0.17
Nodes (12): 1 — Add a credential, 2 — Capture a snapshot, 3 — Diff two snapshots, 4 — Add a golden config, 5 — Run compliance, 6 — Browse everything, 7 — Build a testbed programmatically, Multi-vendor support (+4 more)

### Community 30 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 31 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 32 - "Contributing to netbox-pyats"
Cohesion: 0.18
Nodes (11): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+3 more)

### Community 33 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.18
Nodes (11): Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites, Remote agent wiring (Senior Dev Engineer), Secret rotation (+3 more)

### Community 34 - "Dev environment bring-up"
Cohesion: 0.18
Nodes (11): Bring-up, Dev environment bring-up, Image overrides (compatibility sweeps), Prerequisites, Remote access, Resource limits, Teardown, `test_netbox` already exists / `EOFError` / "terminating connection due to administrator command" (ATW-85) (+3 more)

### Community 35 - "PyatsCredentialModelTest"
Cohesion: 0.18
Nodes (3): TestCase, PyatsCredentialModelTest, Field-level encryption and validation behavior of PyatsCredential.

### Community 36 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 37 - "ADR-0004: Compliance golden-config comparison shape"
Cohesion: 0.20
Nodes (10): Acceptance, ADR-0004: Compliance golden-config comparison shape, Capture change, Consequences, Considered options, Context, Decision, DoesNotExist error-row persistence (blocker #3, same PR) (+2 more)

### Community 38 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 40 - "test_testbed.py"
Cohesion: 0.22
Nodes (4): FakeDeviceType, FakeIPAddress, FakeManufacturer, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS

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

### Community 47 - "dev-worktree.sh"
Cohesion: 0.61
Nodes (7): cmd_add(), cmd_remove(), cmd_up(), die(), next_free_port(), dev-worktree.sh script, usage()

### Community 48 - "[0.1.0] - Unreleased"
Cohesion: 0.29
Nodes (7): [0.1.0] - Unreleased, Added, Added, Changelog, Compatibility, Dev, Fixed

### Community 49 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 50 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 51 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 52 - "Graphify MCP"
Cohesion: 0.29
Nodes (7): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, remote / HTTP config (multi-host, opt-in), stdio config (single-host, default), Switching from stdio to HTTP, Tools exposed (both transports), When to use which transport

### Community 53 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 54 - "SupportedPlatformsReportViewTest"
Cohesion: 0.29
Nodes (3): TestCase, Report contents: the static map renders with per-slug device counts., SupportedPlatformsReportViewTest

### Community 56 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 57 - "PyatsCredentialForm"
Cohesion: 0.33
Nodes (3): PyatsCredentialForm, Create/edit form for a PyATS Credential.      Plaintext password/enable_secret a, NetBoxModelForm

### Community 58 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 59 - "netbox-pyats"
Cohesion: 0.33
Nodes (6): Compatibility matrix, Documentation, License, netbox-pyats, Quick install, What it does

### Community 60 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 61 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 62 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 63 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 64 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 65 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **209 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-entrypoint.sh script`, `pyats-worker-entrypoint.sh script`, `Migration` (+204 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PyatsCredential` connect `PyatsCredential` to `PyatsSnapshot`, `views.py`, `PyatsCredentialModelTest`, `DiffStatusChoices`, `build_testbed`, `models.py`, `PyatsSnapshotDiff`, `SnapshotKindChoices`, `.get_enable_secret`, `PyatsGoldenConfig`, `PyatsCredentialAPITest`, `DeviceBulkCaptureView`, `urls.py`, `SnapshotStatusChoices`, `testbed.py`, `PyatsCredentialViewTest`, `PyatsCredentialForm`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `CaptureResult`, `views.py`, `DiffStatusChoices`, `jobs.py`, `PyatsJobModelTest`, `PyatsSnapshotDiffModelTest`, `models.py`, `PyatsSnapshotDiff`, `SnapshotKindChoices`, `PyatsComplianceRunModelTest`, `PyatsGoldenConfig`, `.get_status_color`, `DeviceBulkCaptureView`, `SnapshotStatusChoices`, `PyatsCredential`, `PyatsGoldenConfigAPITest`, `PyatsCredentialForm`, `template_content.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `PyatsJob` connect `PyatsSnapshot` to `CaptureResult`, `views.py`, `DiffStatusChoices`, `jobs.py`, `PyatsJobModelTest`, `models.py`, `PyatsSnapshotDiff`, `SnapshotKindChoices`, `PyatsGoldenConfig`, `.get_status_color`, `DeviceBulkCaptureView`, `urls.py`, `SnapshotStatusChoices`, `PyatsCredential`, `PyatsCredentialForm`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 108 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshot` has 108 INFERRED edges - model-reasoned connections that need verification._
- **Are the 102 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 102 INFERRED edges - model-reasoned connections that need verification._
- **Are the 98 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsJob` has 98 INFERRED edges - model-reasoned connections that need verification._
- **Are the 97 inferred relationships involving `PyatsCredential` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsCredential` has 97 INFERRED edges - model-reasoned connections that need verification._