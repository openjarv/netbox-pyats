# Graph Report - .  (2026-08-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1635 nodes · 4238 edges · 122 communities (84 shown, 38 thin omitted)
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 1596 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `55c2abf5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- capture_snapshot
- PyatsSnapshot
- jobs.py
- views.py
- test_graphify_scrub_guard.py
- DiffStatusChoices
- diff_snapshots
- refresh_parser_catalog_for_os
- choices.py
- _flagged
- resolve_panel_platform_support
- PyatsCredential
- PyatsComplianceRun
- test_navmenu_uniqueness_guard.py
- PyatsSnapshotDiff
- What You Must Do When Invoked
- SnapshotStatusChoices
- PyatsJob
- PyatsGoldenConfigAPITest
- build_testbed
- DeviceDiffFormKindFilterTest
- SnapshotKindChoices
- EncryptDecryptTest
- test_pr_body_scrub_guard.py
- TestSupportedPlatformsMap
- Dev environment bring-up
- Troubleshooting
- run_compliance
- dev-worktree.sh
- group_snapshots_by_kind
- testbed.py
- ADR-0004: Compliance golden-config comparison shape
- Contributing to netbox-pyats
- platform_to_pyats_os
- PyatsComplianceRunViewTest
- ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts
- Remote access to the dev NetBox UI over Tailscale
- test_testbed.py
- test_compliance.py
- contributing.md
- Usage guide
- capture.py
- PyatsComplianceRunModelTest
- _extract_snapshot_raw
- PyatsSnapshotDiffModelTest
- netbox-pyats
- ADR-0002: Multi-vendor graceful degradation pattern
- Graphify MCP HTTP server — multi-host / shared-service runbook
- .get
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- compliance.py
- DeviceParseViewTest
- PyatsCredentialModelTest
- PyatsJobModelTest
- PyatsSnapshotModelTest
- Scheduled captures
- TestbedBuildReport
- DeviceParseFormTest
- graphify reference: extra exports and benchmark
- [0.1.0] - Unreleased
- ADR-0008: Scheduling surface for recurring snapshot capture
- Graphify
- Compliance engine
- Upgrade guide
- PyATS worker deployment
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Graphify MCP
- Installation
- PULL_REQUEST_TEMPLATE.md
- PyatsGoldenConfigModelTest
- TestOrderedModeReorderDrift
- TestEndToEndCompliancePath
- ADR-0007: Device-page tab via `register_model_view` + `ObjectView`
- Architecture Decision Records
- ComplianceResult
- .__init__
- SupportedPlatformsReportViewTest
- PyatsCredentialViewTest
- graphify reference: query, path, explain
- graphify-mcp-key.sh
- netbox-pyats documentation
- __init__.py
- TestSetMode
- TestCase
- pyats-test-entrypoint.sh
- .clean
- TestComplianceResultSizeBytes
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- entrypoint.sh
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify-scrub-guard.sh
- pr-body-scrub-guard.sh
- AGENTS.md
- .clean_device_filter
- 0004_reconcile_netboxmodel_fields.py
- 0006_compliance_run_nullable_fks.py
- 0007_snapshot_parsed_os.py
- 0008_pyatssnapshotdiff_nullable_fks.py
- 0012_compliance_run_mode.py
- .is_from_snapshot
- .get_status_color
- .has_warnings
- extraction-spec.md
- gitleaks-fixture-regression.sh
- test-unit.sh
- netbox-pyats

## God Nodes (most connected - your core abstractions)
1. `PyatsSnapshot` - 179 edges
2. `PyatsJob` - 173 edges
3. `PyatsSnapshotDiff` - 161 edges
4. `PyatsComplianceRun` - 149 edges
5. `PyatsCredential` - 146 edges
6. `PyatsGoldenConfig` - 143 edges
7. `PyatsCaptureSchedule` - 141 edges
8. `SnapshotKindChoices` - 122 edges
9. `PyatsParserCatalog` - 108 edges
10. `SnapshotTriggerChoices` - 98 edges

## Surprising Connections (you probably didn't know these)
- `PyatsCredentialSerializer` --uses--> `PyatsCaptureSchedule`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsComplianceRun`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsCredential`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsGoldenConfig`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsJob`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py

## Import Cycles
- None detected.

## Communities (122 total, 38 thin omitted)

### Community 0 - "capture_snapshot"
Cohesion: 0.05
Nodes (28): Exception, capture_snapshot(), CaptureResult, Capture a snapshot from a single, already-connected pyATS Device.      This is t, Outcome of a single :func:`capture_snapshot` call.      The :class:`~netbox_pyat, Length of the JSON-serialized ``data`` payload, in bytes., FakePyatsDevice, ParserNotFound (+20 more)

### Community 1 - "PyatsSnapshot"
Cohesion: 0.08
Nodes (69): JobRunner, Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotTriggerChoices, Meta, Recurring dispatcher for capture schedules (ATW-433, ADR-0008).      A registere, RunCaptureSchedulesJob, PyatsCaptureSchedule, PyatsGoldenConfig (+61 more)

### Community 2 - "jobs.py"
Cohesion: 0.05
Nodes (50): BaseException, batch_capture_job(), capture_snapshot_job(), _create_pyats_job(), enqueue_batch_capture(), enqueue_capture(), enqueue_compliance(), enqueue_diff() (+42 more)

### Community 3 - "views.py"
Cohesion: 0.12
Nodes (53): Meta, PyatsCaptureScheduleSerializer, PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsParserCatalogSerializer, PyatsSnapshotDiffSerializer (+45 more)

### Community 4 - "test_graphify_scrub_guard.py"
Cohesion: 0.06
Nodes (51): Module, extended_repo(), _make_extended_tree(), _make_tree(), Tests for scripts/graphify-scrub-guard.sh.  The scrub guard is the structural ba, Build a tree with cache/, a dated backup dir, and .graphify_* state., A tree with clean cache/dated/state files must pass the guard., A leak in cache/stat-index.json must be caught (ATW-307 regression class). (+43 more)

### Community 5 - "DiffStatusChoices"
Cohesion: 0.15
Nodes (50): ComplianceModeChoices, ComplianceResultChoices, CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices (+42 more)

### Community 6 - "diff_snapshots"
Cohesion: 0.06
Nodes (28): Any, _diff_dict(), _diff_list(), diff_snapshots(), _diff_value(), DiffResult, _leaf_type(), _node_status() (+20 more)

### Community 7 - "refresh_parser_catalog_for_os"
Cohesion: 0.08
Nodes (23): CatalogRefreshResult, Parser-catalog refresh core — the Genie work, isolated from NetBox/RQ.  :func:`r, Return the deduplicated set of Genie-supported pyATS os strings.      Derived fr, Outcome of a single :func:`refresh_parser_catalog_for_os` call.      The :func:`, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a minimal ``pyats.topology.Device`` with only ``.os`` set.      ``genie.li, Discover the parseable command list for one pyATS os.      Worker-only: lazily i, refresh_parser_catalog_for_os() (+15 more)

### Community 8 - "choices.py"
Cohesion: 0.06
Nodes (29): Choice sets for the netbox-pyats plugin., decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), is_encrypted_token(), Encryption helpers for the plugin-local PyATS credential store.  Field-level enc (+21 more)

### Community 9 - "_flagged"
Cohesion: 0.10
Nodes (9): _flagged(), Regression test for the ATW-116 secret/PII detection allowlist/regex.  Validates, ATW-167 root-cause regression: a real-shaped value placed in the     fixture fil, Return list of (rule_id, matched_segment) the gitleaks rules would flag., Concrete leaks that MUST be flagged (the ATW-114 regression set)., Placeholder / RFC1918 / loopback forms that MUST NOT be flagged., SecretDetectionATW167Regression, SecretDetectionNegativeCases (+1 more)

### Community 10 - "resolve_panel_platform_support"
Cohesion: 0.12
Nodes (18): Platform-support decision for the device-page PyATS panel (ATW-184).  Pure-Pytho, Return ``(platform_supported, os_value)`` for the device-page panel.      Combin, resolve_panel_platform_support(), FakeDevice, FakePlatform, FakeSnapshot, Tests for the device-page panel platform-support decision (ATW-184).  Pure-Pytho, TestResolvePanelPlatformSupport (+10 more)

### Community 11 - "PyatsCredential"
Cohesion: 0.08
Nodes (20): PyatsCredential, Encrypt and store the device password (ciphertext only)., Decrypt and return the device password (plaintext)., Encrypt and store the enable/privileged password (ciphertext only)., Decrypt and return the enable/privileged password (plaintext)., A plugin-local, encrypted credential for connecting to a device via pyATS., DeviceBulkCaptureView, DeviceCaptureView (+12 more)

### Community 12 - "PyatsComplianceRun"
Cohesion: 0.11
Nodes (21): PyatsComplianceRun, One compliance check result: golden config vs. captured snapshot (Phase 4, ATW-1, Map result to a NetBox color label for table badges., True if the diff found any added/removed/changed leaves (drift)., True if this compliance run row carries warnings / error context., Meta, PyatsCaptureScheduleTable, PyatsComplianceRunTable (+13 more)

### Community 13 - "test_navmenu_uniqueness_guard.py"
Cohesion: 0.10
Nodes (18): _extract_menu_item_kwargs(), _extract_menu_links(), _extract_model_classes(), _extract_schema_type_models(), GraphQLSchemaCompletenessGuard, NavMenuUniquenessGuard, Hardening guard for the navigation menu and GraphQL schema surface.  These tests, Return ``{model_name: type_class_name}`` parsed from ``schema.py``.      Each `` (+10 more)

### Community 14 - "PyatsSnapshotDiff"
Cohesion: 0.12
Nodes (19): PyatsSnapshotDiff, One structured diff between two :class:`PyatsSnapshot` rows of a device.      Po, Map status to a NetBox color label for table badges., True if the diff found any added/removed/changed leaves., True if this diff row carries warnings / error context., PyatsCaptureScheduleIndex, PyatsComplianceRunIndex, PyatsCredentialIndex (+11 more)

### Community 15 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 16 - "SnapshotStatusChoices"
Cohesion: 0.13
Nodes (13): Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotStatusChoices, _AppendOnlyListViewsBase, PyatsComplianceRunListViewRenderTest, PyatsJobListViewRenderTest, PyatsSnapshotDiffListViewRenderTest, PyatsSnapshotListViewRenderTest, Regression tests for the four append-only plugin list views (ATW-183).  The list (+5 more)

### Community 17 - "PyatsJob"
Cohesion: 0.13
Nodes (19): Meta, PyatsCaptureScheduleType, PyatsCredentialType, PyatsJobType, PyatsParserCatalogType, PyatsSnapshotDiffType, PyatsSnapshotType, Query (+11 more)

### Community 18 - "PyatsGoldenConfigAPITest"
Cohesion: 0.10
Nodes (5): APITestCase, PyatsCredentialAPITest, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest, REST API tests for the Phase 4 models (PyatsGoldenConfig, PyatsComplianceRun).

### Community 19 - "build_testbed"
Cohesion: 0.23
Nodes (8): build_testbed(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, _cred_resolver_factory(), FakeCredential, FakeDevice, Return a credential_resolver that always returns ``cred`` (or None)., Duck-typed PyatsCredential (avoids DB/NetBox in unit tests)., TestBuildTestbed

### Community 20 - "DeviceDiffFormKindFilterTest"
Cohesion: 0.17
Nodes (7): DeviceDiffFormKindFilterTest, DeviceDiffViewKindFilterTest, _make_snapshot(), TestCase, The ``device_diff`` view surfaces the kind filter as a redirect+flash., Create a minimal PyatsSnapshot row of the given kind for ``device``., Form-level kind-filter enforcement (ATW-241 child 4).

### Community 21 - "SnapshotKindChoices"
Cohesion: 0.12
Nodes (10): What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, SnapshotKindChoices, Pure-Python helpers for the device-page PyATS tab (ATW-393, ADR-0007).  This mod, DeviceBulkCaptureViewTest, DiffJobPyatsJobPlumbingTest, Tests for the PyatsJob model + job-callable side effects + batch summary (Phase, ADR-0005 §3 plumbing for ``run_diff_job`` (Phase 5, ATW-16)., The device-list bulk "PyATS capture" view renders its confirmation     form (Pha (+2 more)

### Community 22 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 23 - "test_pr_body_scrub_guard.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, Tests for scripts/pr-body-scrub-guard.sh.  The PR body scrub guard is the struct, Role words in normal prose (not on a reviewer/merger line) are fine., An 8-char commit short-SHA must NOT trip the agent-prefix pattern., PR #44/#45 form: `[@CTO](agent://<uuid>)`., A bare RFC-4122 UUID anywhere in the body is caught., PR #47 form: `reviewer: @CTO (agent <prefix>)`., The exact PR #47 leaked line — prefix + role, caught by the prefix. (+9 more)

### Community 24 - "TestSupportedPlatformsMap"
Cohesion: 0.11
Nodes (6): Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, The static map the report renders (Phase 5, ATW-16, Option A)., ADR-0001 §6: the data path the report view reads must not import Genie.      The, TestSupportedPlatformsMap, TestSupportedPlatformsReportWebProcessSafety, FakeManufacturer

### Community 25 - "Dev environment bring-up"
Cohesion: 0.12
Nodes (17): Base branch policy (ATW-208), Bring-up, Dev environment bring-up, Image overrides (compatibility sweeps), Integration lane (Docker + NetBox), Keeping the split clean, Prerequisites, Remote access (+9 more)

### Community 26 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 27 - "run_compliance"
Cohesion: 0.20
Nodes (4): Compare a golden config text against a snapshot's raw config text and classify., run_compliance(), TestDrift, TestErrorInputs

### Community 28 - "dev-worktree.sh"
Cohesion: 0.24
Nodes (12): cmd_add(), cmd_audit(), cmd_cleanup(), cmd_remove(), cmd_test(), cmd_up(), die(), enforce_concurrency_cap() (+4 more)

### Community 29 - "group_snapshots_by_kind"
Cohesion: 0.21
Nodes (8): group_snapshots_by_kind(), Group snapshots by ``kind`` for the diff picker (ATW-241 child 4).      Returns, FakeSnapshot, QA-independent verification for the ATW-252 diff picker kind filter.  Written by, Render the device-tab diff-picker partial and assert the ATW-252     contract: o, Minimal stand-in: only ``kind`` and ``pk`` are read by the helper., TestDeviceTabTemplateOptgroup, TestGroupSnapshotsByKind

### Community 30 - "testbed.py"
Cohesion: 0.15
Nodes (15): _build_device_entry(), _iter_devices(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), _pyats_testbed_cls(), NetBox → pyATS testbed bridge.  :func:`build_testbed` constructs a :class:`pyats, Return the management IP for a NetBox Device, preferring primary_ip4.      Retur (+7 more)

### Community 32 - "ADR-0004: Compliance golden-config comparison shape"
Cohesion: 0.13
Nodes (15): Acceptance, ADR-0004: Compliance golden-config comparison shape, Capture change, Consequences, Consequences, Considered options, Considered options for v2, Context (+7 more)

### Community 33 - "Contributing to netbox-pyats"
Cohesion: 0.13
Nodes (15): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+7 more)

### Community 34 - "platform_to_pyats_os"
Cohesion: 0.31
Nodes (4): platform_to_pyats_os(), Map a NetBox ``Platform`` to a pyATS ``os`` string.      Returns the :data:`UNSU, FakePlatform, TestPlatformToOs

### Community 35 - "PyatsComplianceRunViewTest"
Cohesion: 0.13
Nodes (3): PyatsComplianceRunViewTest, PyatsGoldenConfigViewTest, View tests for the Phase 4 compliance views (ATW-15).  Requires a running NetBox

### Community 36 - "ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts"
Cohesion: 0.15
Nodes (13): 1. PR bodies use role-only labels — no identifiers (hard rule), 2. `[@Agent](agent://<id>)` is internal-only, 3. Boundary rule: public artifact vs internal comment, 4. Merger verifies before merge, 5. Retroactive redaction is harm-reduction, not elimination, ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts, Alternatives considered, Blast radius (+5 more)

### Community 37 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 38 - "test_testbed.py"
Cohesion: 0.21
Nodes (6): is_supported_os(), True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)., FakeDeviceType, FakeIPAddress, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS, TestIsSupportedOs

### Community 39 - "test_compliance.py"
Cohesion: 0.15
Nodes (6): Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15; v2 ATW-434).  Pure-Py, The ordered diff can emit the same line text at multiple positions     (e.g. two, TestCompliant, TestDuplicateLines, TestJsonSerializable, TestUnknownModeDegradesToOrdered

### Community 41 - "Usage guide"
Cohesion: 0.17
Nodes (12): 1 — Add a credential, 2 — Capture a snapshot, 3 — Diff two snapshots, 4 — Add a golden config, 5 — Run compliance, 6 — Browse everything, 7 — Build a testbed programmatically, Multi-vendor support (+4 more)

### Community 42 - "capture.py"
Cohesion: 0.18
Nodes (11): _capture_config(), _capture_parse(), capture_snapshot_for_netbox_device(), _capture_state(), Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u, Run parser-based state capture on a connected pyATS Device.      Runs a small, O, Run on-demand parser capture for an explicit, user-supplied command list.      T (+3 more)

### Community 44 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 45 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.24
Nodes (3): PyatsSnapshotDiffModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Regression for ATW-68: a diff error row with before/after NULL must         roun

### Community 46 - "netbox-pyats"
Cohesion: 0.17
Nodes (12): At a glance, Capture, Compare, Compatibility matrix, Compliance & Jobs, Device-page UI, Documentation, Getting help (+4 more)

### Community 47 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 48 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.18
Nodes (11): Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites, Remote agent wiring (Senior Dev Engineer), Secret rotation (+3 more)

### Community 49 - ".get"
Cohesion: 0.22
Nodes (4): Resolve the pyATS os + catalog row + command choices for a device.      Web-proc, Return the POST URL for the device-page "Refresh parser list" button., _refresh_parser_catalog_url_for_device(), _resolve_parse_context()

### Community 50 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 51 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 52 - "compliance.py"
Cohesion: 0.24
Nodes (9): _build_tree(), _normalize_lines(), _ordered_diff(), Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Normalize a running-config text into a list of comparable lines.      Drops blan, Build the JSON-serializable diff tree and summary from leaf lists.      The tree, v2 ordered (sequence-aware) diff via :mod:`difflib`.      Walks :func:`difflib.S, v1 set (order-independent) diff.      Compares the two line lists as sets and re (+1 more)

### Community 57 - "Scheduled captures"
Cohesion: 0.22
Nodes (9): Creating a schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled captures, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 58 - "TestbedBuildReport"
Cohesion: 0.22
Nodes (3): Summary of a :func:`build_testbed` run.      Keeps track of which devices were i, True if at least one device was supported AND none errored.          ``build_tes, TestbedBuildReport

### Community 59 - "DeviceParseFormTest"
Cohesion: 0.22
Nodes (3): DeviceParseFormTest, Tests for the device-page Parse sub-tab (ATW-241 child 2, ATW-250).  Requires a, Pure-form validation for :class:`forms.DeviceParseForm`.

### Community 60 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 61 - "[0.1.0] - Unreleased"
Cohesion: 0.25
Nodes (8): [0.1.0] - Unreleased, Added, Added, Changelog, Compatibility, Dev, Docs, Fixed

### Community 62 - "ADR-0008: Scheduling surface for recurring snapshot capture"
Cohesion: 0.25
Nodes (8): ADR-0008: Scheduling surface for recurring snapshot capture, Alternatives considered, Consequences, Context, Decision, References, Structural shape, Why this fits the locked architecture

### Community 63 - "Graphify"
Cohesion: 0.25
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 64 - "Compliance engine"
Cohesion: 0.25
Nodes (8): Both modes are line-oriented text diff, not Genie-structured diff, Classification, Compliance engine, Engine layer, Related, The diff tree, What it does, What the snapshot needs

### Community 65 - "Upgrade guide"
Cohesion: 0.25
Nodes (8): Before you begin, Both at once (NetBox + plugin upgrade), NetBox upgrade (plugin release unchanged), Next steps, Plugin upgrade (NetBox release unchanged), Troubleshooting an upgrade, Upgrade guide, What stays in sync with what

### Community 66 - "PyATS worker deployment"
Cohesion: 0.25
Nodes (8): Option A — install pyats into your own worker, Option B — the shipped worker image (reference / dev), PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, What runs on the `pyats` queue, Why a separate queue

### Community 67 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 68 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 69 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 70 - "Graphify MCP"
Cohesion: 0.29
Nodes (7): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, remote / HTTP config (multi-host, opt-in), stdio config (single-host, default), Switching from stdio to HTTP, Tools exposed (both transports), When to use which transport

### Community 71 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 72 - "PULL_REQUEST_TEMPLATE.md"
Cohesion: 0.29
Nodes (6): Changes, Closing checklist, Linked issue, Notes for reviewers, Summary, Verification

### Community 76 - "ADR-0007: Device-page tab via `register_model_view` + `ObjectView`"
Cohesion: 0.33
Nodes (6): ADR-0007: Device-page tab via `register_model_view` + `ObjectView`, Alternatives considered, Consequences, Context, Decision, References

### Community 77 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 78 - "ComplianceResult"
Cohesion: 0.33
Nodes (4): ComplianceResult, Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift).

### Community 82 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 83 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 84 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 85 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 87 - "TestCase"
Cohesion: 0.40
Nodes (3): DeviceRefreshCatalogViewTest, View tests for :class:`views.DeviceRefreshCatalogView` (ATW-250)., TestCase

### Community 91 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 92 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 93 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **274 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-test-entrypoint.sh script`, `DJANGO_SETTINGS_MODULE`, `Migration` (+269 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **38 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SnapshotKindChoices` connect `SnapshotKindChoices` to `capture_snapshot`, `PyatsSnapshot`, `jobs.py`, `DiffStatusChoices`, `choices.py`, `PyatsCredential`, `PyatsComplianceRun`, `PyatsSnapshotDiff`, `SnapshotStatusChoices`, `PyatsJob`, `PyatsGoldenConfigAPITest`, `DeviceDiffFormKindFilterTest`, `group_snapshots_by_kind`, `PyatsComplianceRunViewTest`, `capture.py`, `PyatsComplianceRunModelTest`, `PyatsSnapshotDiffModelTest`, `PyatsJobModelTest`, `PyatsSnapshotModelTest`, `PyatsGoldenConfigModelTest`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `PyatsCredential` connect `PyatsCredential` to `PyatsSnapshot`, `views.py`, `DiffStatusChoices`, `choices.py`, `PyatsComplianceRun`, `PyatsSnapshotDiff`, `SnapshotStatusChoices`, `PyatsJob`, `PyatsGoldenConfigAPITest`, `PyatsCredentialViewTest`, `SnapshotKindChoices`, `PyatsCredentialModelTest`, `TestbedBuildReport`, `testbed.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `capture_snapshot`, `jobs.py`, `views.py`, `DiffStatusChoices`, `choices.py`, `PyatsCredential`, `PyatsComplianceRun`, `PyatsSnapshotDiff`, `SnapshotStatusChoices`, `PyatsJob`, `PyatsGoldenConfigAPITest`, `DeviceDiffFormKindFilterTest`, `SnapshotKindChoices`, `PyatsComplianceRunViewTest`, `PyatsComplianceRunModelTest`, `PyatsSnapshotDiffModelTest`, `PyatsJobModelTest`, `PyatsSnapshotModelTest`, `PyatsGoldenConfigModelTest`, `.get_status_color`, `.has_warnings`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 139 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshot` has 139 INFERRED edges - model-reasoned connections that need verification._
- **Are the 130 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsJob` has 130 INFERRED edges - model-reasoned connections that need verification._
- **Are the 131 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 131 INFERRED edges - model-reasoned connections that need verification._
- **Are the 120 inferred relationships involving `PyatsComplianceRun` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsComplianceRun` has 120 INFERRED edges - model-reasoned connections that need verification._