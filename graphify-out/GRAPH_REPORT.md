# Graph Report - .  (2026-07-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1435 nodes · 3608 edges · 103 communities (78 shown, 25 thin omitted)
- Extraction: 65% EXTRACTED · 35% INFERRED · 0% AMBIGUOUS · INFERRED: 1264 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a65dcbd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CaptureResult
- PyatsSnapshotDiff
- views.py
- template_content.py
- diff_snapshots
- jobs.py
- run_compliance
- DiffStatusChoices
- refresh_parser_catalog_for_os
- PyatsCredential
- _flagged
- test_graphify_scrub_guard.py
- SnapshotTriggerChoices
- What You Must Do When Invoked
- SnapshotKindChoices
- PyatsSnapshot
- choices.py
- build_testbed
- DeviceParseViewTest
- PyatsGoldenConfig
- PyatsJob
- EncryptDecryptTest
- DeviceDiffFormKindFilterTest
- test_pr_body_scrub_guard.py
- crypto.py
- Troubleshooting
- testbed.py
- PyatsComplianceRunViewTest
- PyatsGoldenConfigAPITest
- platform_to_pyats_os
- ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts
- Contributing to netbox-pyats
- Remote access to the dev NetBox UI over Tailscale
- test_testbed.py
- netbox-pyats
- dev-worktree.sh
- Dev environment bring-up
- Usage guide
- PyatsComplianceRunModelTest
- _extract_snapshot_raw
- PyatsSnapshotDiffModelTest
- TestSupportedPlatformsMap
- ADR-0002: Multi-vendor graceful degradation pattern
- Graphify MCP HTTP server — multi-host / shared-service runbook
- PyatsCredentialForm
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0004: Compliance golden-config comparison shape
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- PyatsCredentialModelTest
- PyatsJobModelTest
- PyatsSnapshotModelTest
- ._render
- contributing.md
- TestbedBuildReport
- PyatsCredentialAPITest
- PyatsGoldenConfigModelTest
- graphify reference: extra exports and benchmark
- Graphify
- Compliance engine
- Upgrade guide
- PyATS worker deployment
- [0.1.0] - Unreleased
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Graphify MCP
- Installation
- PULL_REQUEST_TEMPLATE.md
- PyatsParserCatalogModelTest
- TestCase
- Architecture Decision Records
- test_supported_platforms.py
- SupportedPlatformsReportViewTest
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
- pr-body-scrub-guard.sh
- AGENTS.md
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- 0004_reconcile_netboxmodel_fields.py
- 0006_compliance_run_nullable_fks.py
- 0007_snapshot_parsed_os.py
- 0008_pyatssnapshotdiff_nullable_fks.py
- extraction-spec.md
- gitleaks-fixture-regression.sh
- netbox-pyats

## God Nodes (most connected - your core abstractions)
1. `PyatsSnapshot` - 164 edges
2. `PyatsJob` - 156 edges
3. `PyatsSnapshotDiff` - 146 edges
4. `PyatsComplianceRun` - 135 edges
5. `PyatsCredential` - 131 edges
6. `PyatsGoldenConfig` - 129 edges
7. `SnapshotKindChoices` - 109 edges
8. `PyatsParserCatalog` - 95 edges
9. `SnapshotTriggerChoices` - 87 edges
10. `SnapshotStatusChoices` - 75 edges

## Surprising Connections (you probably didn't know these)
- `PyatsCredentialSerializer` --uses--> `PyatsComplianceRun`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsCredential`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsGoldenConfig`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsJob`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsParserCatalog`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py

## Import Cycles
- None detected.

## Communities (103 total, 25 thin omitted)

### Community 0 - "CaptureResult"
Cohesion: 0.06
Nodes (26): Exception, capture_snapshot(), CaptureResult, Capture a snapshot from a single, already-connected pyATS Device.      This is t, Outcome of a single :func:`capture_snapshot` call.      The :class:`~netbox_pyat, Length of the JSON-serialized ``data`` payload, in bytes., FakePyatsDevice, ParserNotFound (+18 more)

### Community 1 - "PyatsSnapshotDiff"
Cohesion: 0.07
Nodes (53): PyatsComplianceRun, PyatsParserCatalog, PyatsSnapshotDiff, One structured diff between two :class:`PyatsSnapshot` rows of a device.      Po, Map status to a NetBox color label for table badges., True if the diff found any added/removed/changed leaves., True if this diff row carries warnings / error context., One compliance check result: golden config vs. captured snapshot (Phase 4, ATW-1 (+45 more)

### Community 2 - "views.py"
Cohesion: 0.12
Nodes (47): Meta, PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsParserCatalogSerializer, PyatsSnapshotDiffSerializer, PyatsSnapshotSerializer (+39 more)

### Community 3 - "template_content.py"
Cohesion: 0.07
Nodes (30): Platform-support decision for the device-page PyATS panel (ATW-184).  Pure-Pytho, Return ``(platform_supported, os_value)`` for the device-page panel.      Combin, resolve_panel_platform_support(), _capture_url_for_device(), _compliance_url_for_device(), DevicePyATSPanel, _diff_url_for_device(), _group_snapshots_by_kind() (+22 more)

### Community 4 - "diff_snapshots"
Cohesion: 0.06
Nodes (28): Any, _diff_dict(), _diff_list(), diff_snapshots(), _diff_value(), DiffResult, _leaf_type(), _node_status() (+20 more)

### Community 5 - "jobs.py"
Cohesion: 0.07
Nodes (47): BaseException, _capture_config(), _capture_parse(), capture_snapshot_for_netbox_device(), _capture_state(), Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u, Run parser-based state capture on a connected pyATS Device.      Runs a small, O (+39 more)

### Community 6 - "run_compliance"
Cohesion: 0.07
Nodes (17): ComplianceResult, _normalize_lines(), Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift)., Normalize a running-config text into a list of comparable lines.      Drops blan, Compare a golden config text against a snapshot's raw config text and classify., Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_ (+9 more)

### Community 7 - "DiffStatusChoices"
Cohesion: 0.17
Nodes (41): ComplianceResultChoices, CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices, How a :class:`PyatsGoldenConfig` row was authored (Phase 4, ATW-15).      ``manu (+33 more)

### Community 8 - "refresh_parser_catalog_for_os"
Cohesion: 0.10
Nodes (20): CatalogRefreshResult, Parser-catalog refresh core — the Genie work, isolated from NetBox/RQ.  :func:`r, Return the deduplicated set of Genie-supported pyATS os strings.      Derived fr, Outcome of a single :func:`refresh_parser_catalog_for_os` call.      The :func:`, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a minimal ``pyats.topology.Device`` with only ``.os`` set.      ``genie.li, Discover the parseable command list for one pyATS os.      Worker-only: lazily i, refresh_parser_catalog_for_os() (+12 more)

### Community 9 - "PyatsCredential"
Cohesion: 0.08
Nodes (22): PyatsCredential, Encrypt and store the device password (ciphertext only)., Decrypt and return the device password (plaintext)., Encrypt and store the enable/privileged password (ciphertext only)., Decrypt and return the enable/privileged password (plaintext)., A plugin-local, encrypted credential for connecting to a device via pyATS., DeviceBulkCaptureView, DeviceCaptureView (+14 more)

### Community 10 - "_flagged"
Cohesion: 0.10
Nodes (9): _flagged(), Regression test for the ATW-116 secret/PII detection allowlist/regex.  Validates, ATW-167 root-cause regression: a real-shaped value placed in the     fixture fil, Return list of (rule_id, matched_segment) the gitleaks rules would flag., Concrete leaks that MUST be flagged (the ATW-114 regression set)., Placeholder / RFC1918 / loopback forms that MUST NOT be flagged., SecretDetectionATW167Regression, SecretDetectionNegativeCases (+1 more)

### Community 11 - "test_graphify_scrub_guard.py"
Cohesion: 0.13
Nodes (31): extended_repo(), _make_extended_tree(), _make_tree(), CompletedProcess, Tests for scripts/graphify-scrub-guard.sh.  The scrub guard is the structural ba, Build a tree with cache/, a dated backup dir, and .graphify_* state., A tree with clean cache/dated/state files must pass the guard., A leak in cache/stat-index.json must be caught (ATW-307 regression class). (+23 more)

### Community 12 - "SnapshotTriggerChoices"
Cohesion: 0.11
Nodes (14): Who/what triggered a snapshot capture.      ``user`` captures are initiated from, Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotStatusChoices, SnapshotTriggerChoices, BatchCaptureJobTest, DeviceBulkCaptureViewTest, DiffJobPyatsJobPlumbingTest, Tests for the PyatsJob model + job-callable side effects + batch summary (Phase (+6 more)

### Community 13 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 14 - "SnapshotKindChoices"
Cohesion: 0.13
Nodes (13): What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, SnapshotKindChoices, _AppendOnlyListViewsBase, PyatsComplianceRunListViewRenderTest, PyatsJobListViewRenderTest, PyatsSnapshotDiffListViewRenderTest, PyatsSnapshotListViewRenderTest, Regression tests for the four append-only plugin list views (ATW-183).  The list (+5 more)

### Community 15 - "PyatsSnapshot"
Cohesion: 0.12
Nodes (17): Meta, PyatsCredentialType, PyatsJobType, PyatsParserCatalogType, PyatsSnapshotDiffType, PyatsSnapshotType, Query, GraphQL type for the PyatsParserCatalog model (ATW-241 child 1).      Exposes th (+9 more)

### Community 16 - "choices.py"
Cohesion: 0.09
Nodes (12): Choice sets for the netbox-pyats plugin., Migration, Migration, Migration, Migration, Migration, Migration, ATW-241 child 1 (ATW-249): add PyatsParserCatalog + the `kind='parse'` choice. (+4 more)

### Community 17 - "build_testbed"
Cohesion: 0.23
Nodes (8): build_testbed(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, _cred_resolver_factory(), FakeCredential, FakeDevice, Return a credential_resolver that always returns ``cred`` (or None)., Duck-typed PyatsCredential (avoids DB/NetBox in unit tests)., TestBuildTestbed

### Community 18 - "DeviceParseViewTest"
Cohesion: 0.09
Nodes (7): DeviceParseFormTest, DeviceParseViewTest, DeviceRefreshCatalogViewTest, TestCase, View tests for :class:`views.DeviceRefreshCatalogView` (ATW-250)., Pure-form validation for :class:`forms.DeviceParseForm`., View tests for :class:`views.DeviceParseView` (ATW-250).

### Community 19 - "PyatsGoldenConfig"
Cohesion: 0.15
Nodes (17): PyatsGoldenConfig, A golden / reference running-config for a NetBox Device (Phase 4, ATW-15)., True if this golden config was promoted from a snapshot row., Meta, PyatsComplianceRunTable, PyatsCredentialTable, PyatsGoldenConfigTable, PyatsJobTable (+9 more)

### Community 20 - "PyatsJob"
Cohesion: 0.15
Nodes (16): PyatsJob, One plugin job-tracking row across capture / diff / compliance / batch (Phase 5,, Map status to a NetBox color label for table badges.          ``success`` / ``er, The result row this job produced, regardless of type, or None.          Convenie, PyatsComplianceRunIndex, PyatsCredentialIndex, PyatsGoldenConfigIndex, PyatsJobIndex (+8 more)

### Community 21 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 22 - "DeviceDiffFormKindFilterTest"
Cohesion: 0.19
Nodes (7): DeviceDiffFormKindFilterTest, DeviceDiffViewKindFilterTest, _make_snapshot(), TestCase, The ``device_diff`` view surfaces the kind filter as a redirect+flash., Create a minimal PyatsSnapshot row of the given kind for ``device``., Form-level kind-filter enforcement (ATW-241 child 4).

### Community 23 - "test_pr_body_scrub_guard.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, Tests for scripts/pr-body-scrub-guard.sh.  The PR body scrub guard is the struct, Role words in normal prose (not on a reviewer/merger line) are fine., An 8-char commit short-SHA must NOT trip the agent-prefix pattern., PR #44/#45 form: `[@CTO](agent://<uuid>)`., A bare RFC-4122 UUID anywhere in the body is caught., PR #47 form: `reviewer: @CTO (agent <prefix>)`., The exact PR #47 leaked line — prefix + role, caught by the prefix. (+9 more)

### Community 24 - "crypto.py"
Cohesion: 0.14
Nodes (15): decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), is_encrypted_token(), Encryption helpers for the plugin-local PyATS credential store.  Field-level enc, Decrypt a Fernet token produced by :func:`encrypt`.      Empty input round-trips (+7 more)

### Community 25 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 26 - "testbed.py"
Cohesion: 0.15
Nodes (15): _build_device_entry(), _iter_devices(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), _pyats_testbed_cls(), NetBox → pyATS testbed bridge.  :func:`build_testbed` constructs a :class:`pyats, Return the management IP for a NetBox Device, preferring primary_ip4.      Retur (+7 more)

### Community 27 - "PyatsComplianceRunViewTest"
Cohesion: 0.13
Nodes (4): TestCase, PyatsComplianceRunViewTest, PyatsGoldenConfigViewTest, View tests for the Phase 4 compliance views (ATW-15).  Requires a running NetBox

### Community 28 - "PyatsGoldenConfigAPITest"
Cohesion: 0.14
Nodes (4): APITestCase, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest, REST API tests for the Phase 4 models (PyatsGoldenConfig, PyatsComplianceRun).

### Community 29 - "platform_to_pyats_os"
Cohesion: 0.31
Nodes (4): platform_to_pyats_os(), Map a NetBox ``Platform`` to a pyATS ``os`` string.      Returns the :data:`UNSU, FakePlatform, TestPlatformToOs

### Community 31 - "ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts"
Cohesion: 0.14
Nodes (13): 1. PR bodies use role-only labels — no identifiers (hard rule), 2. `[@Agent](agent://<id>)` is internal-only, 3. Boundary rule: public artifact vs internal comment, 4. Merger verifies before merge, 5. Retroactive redaction is harm-reduction, not elimination, ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts, Alternatives considered, Blast radius (+5 more)

### Community 32 - "Contributing to netbox-pyats"
Cohesion: 0.15
Nodes (13): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+5 more)

### Community 33 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 34 - "test_testbed.py"
Cohesion: 0.21
Nodes (6): is_supported_os(), True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)., FakeDeviceType, FakeIPAddress, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS, TestIsSupportedOs

### Community 35 - "netbox-pyats"
Cohesion: 0.15
Nodes (13): At a glance, Capture, Compare, Compatibility matrix, Compliance & Jobs, Device-page UI, Documentation, Getting help (+5 more)

### Community 36 - "dev-worktree.sh"
Cohesion: 0.31
Nodes (9): cmd_add(), cmd_audit(), cmd_cleanup(), cmd_remove(), cmd_up(), die(), next_free_port(), dev-worktree.sh script (+1 more)

### Community 37 - "Dev environment bring-up"
Cohesion: 0.17
Nodes (12): Base branch policy (ATW-208), Bring-up, Dev environment bring-up, Image overrides (compatibility sweeps), Prerequisites, Remote access, Resource limits, Teardown (+4 more)

### Community 38 - "Usage guide"
Cohesion: 0.17
Nodes (12): 1 — Add a credential, 2 — Capture a snapshot, 3 — Diff two snapshots, 4 — Add a golden config, 5 — Run compliance, 6 — Browse everything, 7 — Build a testbed programmatically, Multi-vendor support (+4 more)

### Community 40 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 41 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.24
Nodes (3): PyatsSnapshotDiffModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Regression for ATW-68: a diff error row with before/after NULL must         roun

### Community 42 - "TestSupportedPlatformsMap"
Cohesion: 0.17
Nodes (3): The static map the report renders (Phase 5, ATW-16, Option A)., TestSupportedPlatformsMap, FakeManufacturer

### Community 43 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 44 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.18
Nodes (11): Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites, Remote agent wiring (Senior Dev Engineer), Secret rotation (+3 more)

### Community 45 - "PyatsCredentialForm"
Cohesion: 0.18
Nodes (5): PyatsCredentialForm, Create/edit form for a PyATS Credential.      Plaintext password/enable_secret a, Initialize the form, optionally pinning the ``commands`` choices.          Args:, Require at least one of ``commands`` or ``manual_command``.          The parse j, NetBoxModelForm

### Community 46 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 47 - "ADR-0004: Compliance golden-config comparison shape"
Cohesion: 0.20
Nodes (10): Acceptance, ADR-0004: Compliance golden-config comparison shape, Capture change, Consequences, Considered options, Context, Decision, DoesNotExist error-row persistence (blocker #3, same PR) (+2 more)

### Community 48 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 52 - "._render"
Cohesion: 0.24
Nodes (4): Resolve the pyATS os + catalog row + command choices for a device.      Web-proc, Return the POST URL for the device-page "Refresh parser list" button., _refresh_parser_catalog_url_for_device(), _resolve_parse_context()

### Community 54 - "TestbedBuildReport"
Cohesion: 0.22
Nodes (3): Summary of a :func:`build_testbed` run.      Keeps track of which devices were i, True if at least one device was supported AND none errored.          ``build_tes, TestbedBuildReport

### Community 56 - "PyatsGoldenConfigModelTest"
Cohesion: 0.22
Nodes (3): PyatsGoldenConfigModelTest, Tests for :class:`netbox_pyats.models.PyatsGoldenConfig` and :class:`netbox_pyat, Persistence and helper behavior of PyatsGoldenConfig.

### Community 57 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 58 - "Graphify"
Cohesion: 0.25
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 59 - "Compliance engine"
Cohesion: 0.25
Nodes (8): Classification, Compliance engine, Engine layer, Related, The diff tree, v1 is line-oriented text diff, not Genie-structured diff, What it does, What the snapshot needs

### Community 60 - "Upgrade guide"
Cohesion: 0.25
Nodes (8): Before you begin, Both at once (NetBox + plugin upgrade), NetBox upgrade (plugin release unchanged), Next steps, Plugin upgrade (NetBox release unchanged), Troubleshooting an upgrade, Upgrade guide, What stays in sync with what

### Community 61 - "PyATS worker deployment"
Cohesion: 0.25
Nodes (8): Option A — install pyats into your own worker, Option B — the shipped worker image (reference / dev), PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, What runs on the `pyats` queue, Why a separate queue

### Community 62 - "[0.1.0] - Unreleased"
Cohesion: 0.29
Nodes (7): [0.1.0] - Unreleased, Added, Added, Changelog, Compatibility, Dev, Fixed

### Community 63 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 64 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 65 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 66 - "Graphify MCP"
Cohesion: 0.29
Nodes (7): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, remote / HTTP config (multi-host, opt-in), stdio config (single-host, default), Switching from stdio to HTTP, Tools exposed (both transports), When to use which transport

### Community 67 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 68 - "PULL_REQUEST_TEMPLATE.md"
Cohesion: 0.29
Nodes (6): Changes, Closing checklist, Linked issue, Notes for reviewers, Summary, Verification

### Community 71 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 72 - "test_supported_platforms.py"
Cohesion: 0.33
Nodes (3): Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, ADR-0001 §6: the data path the report view reads must not import Genie.      The, TestSupportedPlatformsReportWebProcessSafety

### Community 74 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 75 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 76 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 77 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 78 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 79 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 80 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **243 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-entrypoint.sh script`, `pyats-worker-entrypoint.sh script`, `Migration` (+238 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SnapshotKindChoices` connect `SnapshotKindChoices` to `CaptureResult`, `PyatsSnapshotDiff`, `template_content.py`, `jobs.py`, `DiffStatusChoices`, `PyatsCredential`, `SnapshotTriggerChoices`, `PyatsSnapshot`, `choices.py`, `PyatsGoldenConfig`, `PyatsJob`, `DeviceDiffFormKindFilterTest`, `PyatsComplianceRunViewTest`, `PyatsGoldenConfigAPITest`, `PyatsComplianceRunModelTest`, `PyatsSnapshotDiffModelTest`, `PyatsCredentialForm`, `PyatsJobModelTest`, `PyatsSnapshotModelTest`, `PyatsGoldenConfigModelTest`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `CaptureResult`, `PyatsSnapshotDiff`, `views.py`, `template_content.py`, `jobs.py`, `DiffStatusChoices`, `PyatsCredential`, `SnapshotTriggerChoices`, `SnapshotKindChoices`, `choices.py`, `PyatsGoldenConfig`, `PyatsJob`, `DeviceDiffFormKindFilterTest`, `PyatsComplianceRunViewTest`, `PyatsGoldenConfigAPITest`, `PyatsComplianceRunModelTest`, `PyatsSnapshotDiffModelTest`, `PyatsCredentialForm`, `PyatsJobModelTest`, `PyatsSnapshotModelTest`, `PyatsGoldenConfigModelTest`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `PyatsCredential` connect `PyatsCredential` to `PyatsSnapshotDiff`, `views.py`, `TestCase`, `DiffStatusChoices`, `SnapshotTriggerChoices`, `PyatsCredentialForm`, `SnapshotKindChoices`, `PyatsSnapshot`, `choices.py`, `PyatsCredentialModelTest`, `PyatsGoldenConfig`, `PyatsJob`, `TestbedBuildReport`, `PyatsCredentialAPITest`, `crypto.py`, `testbed.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 123 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshot` has 123 INFERRED edges - model-reasoned connections that need verification._
- **Are the 113 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsJob` has 113 INFERRED edges - model-reasoned connections that need verification._
- **Are the 115 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 115 INFERRED edges - model-reasoned connections that need verification._
- **Are the 105 inferred relationships involving `PyatsComplianceRun` (e.g. with `Meta` and `PyatsComplianceRunSerializer`) actually correct?**
  _`PyatsComplianceRun` has 105 INFERRED edges - model-reasoned connections that need verification._