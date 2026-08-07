# Graph Report - .  (2026-08-07)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1828 nodes · 4914 edges · 157 communities (102 shown, 55 thin omitted)
- Extraction: 61% EXTRACTED · 39% INFERRED · 0% AMBIGUOUS · INFERRED: 1912 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `542dc68a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PyatsSnapshot
- views.py
- ComplianceResultChoices
- refresh_parser_catalog_for_os
- PyatsJob
- _flagged
- test_graphify_scrub_guard.py
- capture_snapshot
- resolve_panel_platform_support
- CaptureResult
- run_capture_schedules_job
- DiffStatusChoices
- build_testbed
- SnapshotKindChoices
- test_navmenu_uniqueness_guard.py
- diff_snapshots
- flatten_diff_tree
- PyatsCredential
- What You Must Do When Invoked
- PyatsGoldenConfigAPITest
- PyatsCaptureSchedule
- test_template_extension.py
- DeviceDiffFormKindFilterTest
- dev-worktree.sh
- diff.py
- Dev environment bring-up
- EncryptDecryptTest
- crypto.py
- jobs.py
- run_parser_catalog_refresh_schedules_job
- group_snapshots_by_kind
- run_diff_job
- Troubleshooting
- choices.py
- run_compliance
- DeviceDiffForm
- test_pr_body_scrub_guard.py
- extract_snapshot_raw_config
- testbed.py
- test_testbed.py
- PyatsComplianceRunViewTest
- ADR-0004: Compliance golden-config comparison shape
- Contributing to netbox-pyats
- platform_to_pyats_os
- dev-seed.sh
- ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts
- Remote access to the dev NetBox UI over Tailscale
- Usage guide
- test_capture.py
- test_compliance.py
- contributing.md
- PyatsComplianceRunModelTest
- _extract_snapshot_raw
- PyatsSnapshotDiffModelTest
- test_supported_platforms.py
- TestSupportedPlatformsMap
- .get
- netbox-pyats
- ADR-0002: Multi-vendor graceful degradation pattern
- Graphify MCP HTTP server — multi-host / shared-service runbook
- resolve_state_commands
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- compliance.py
- DeviceParseViewTest
- PyatsCredentialModelTest
- PyatsJobModelTest
- PyatsSnapshotModelTest
- TestStateCommandsInvariant
- [0.1.0] - Unreleased
- Scheduled captures
- Scheduled parser-catalog refresh
- DiffLine
- TestbedBuildReport
- graphify reference: extra exports and benchmark
- ADR-0008: Scheduling surface for recurring snapshot capture
- Graphify
- Compliance engine
- Upgrade guide
- PyATS worker deployment
- capture_snapshot_for_netbox_device
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Graphify MCP
- Installation
- PULL_REQUEST_TEMPLATE.md
- TestStateCapture
- PyatsGoldenConfigModelTest
- TestOrderedModeReorderDrift
- TestEndToEndCompliancePath
- DeviceParseFormTest
- DiffTableRenderTest
- ADR-0007: Device-page tab via `register_model_view` + `ObjectView`
- Architecture Decision Records
- ComplianceResult
- DiffResult
- PyatsCredentialViewTest
- graphify reference: query, path, explain
- graphify-mcp-key.sh
- netbox-pyats documentation
- __init__.py
- TestPerOsStateCapture
- TestSetMode
- TestCase
- pyats-test-entrypoint.sh
- TestComplianceResultSizeBytes
- PyatsParserCatalogRefreshScheduleModelTest
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- entrypoint.sh
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- TestRealisticSnapshot
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify-scrub-guard.sh
- pr-body-scrub-guard.sh
- AGENTS.md
- _capture_config
- _capture_state
- .clean_device_filter
- 0004_reconcile_netboxmodel_fields.py
- 0006_compliance_run_nullable_fks.py
- 0007_snapshot_parsed_os.py
- 0008_pyatssnapshotdiff_nullable_fks.py
- 0012_compliance_run_mode.py
- 0013_pyatsparsercatalogrefreshschedule.py
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
- gitleaks-fixture-regression.sh
- test-unit.sh
- netbox-pyats

## God Nodes (most connected - your core abstractions)
1. `PyatsSnapshot` - 195 edges
2. `PyatsJob` - 186 edges
3. `PyatsSnapshotDiff` - 177 edges
4. `PyatsComplianceRun` - 161 edges
5. `PyatsCredential` - 158 edges
6. `PyatsGoldenConfig` - 155 edges
7. `PyatsCaptureSchedule` - 154 edges
8. `PyatsParserCatalogRefreshSchedule` - 142 edges
9. `SnapshotKindChoices` - 135 edges
10. `PyatsParserCatalog` - 118 edges

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

## Communities (157 total, 55 thin omitted)

### Community 0 - "PyatsSnapshot"
Cohesion: 0.08
Nodes (82): JobRunner, Meta, Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotTriggerChoices, Meta, Recurring dispatcher for capture schedules (ATW-433, ADR-0008).      A registere, Recurring dispatcher for the parser catalog refresh (ATW-581).      A registered, RunCaptureSchedulesJob (+74 more)

### Community 1 - "views.py"
Cohesion: 0.14
Nodes (57): PyatsCaptureScheduleSerializer, PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsParserCatalogRefreshScheduleSerializer, PyatsParserCatalogSerializer, PyatsSnapshotDiffSerializer (+49 more)

### Community 2 - "ComplianceResultChoices"
Cohesion: 0.14
Nodes (50): ComplianceModeChoices, ComplianceResultChoices, CredentialProtocolChoices, CredentialScopeChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices, How a :class:`PyatsGoldenConfig` row was authored (Phase 4, ATW-15).      ``manu (+42 more)

### Community 3 - "refresh_parser_catalog_for_os"
Cohesion: 0.08
Nodes (23): CatalogRefreshResult, Parser-catalog refresh core — the Genie work, isolated from NetBox/RQ.  :func:`r, Return the deduplicated set of Genie-supported pyATS os strings.      Derived fr, Outcome of a single :func:`refresh_parser_catalog_for_os` call.      The :func:`, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a minimal ``pyats.topology.Device`` with only ``.os`` set.      ``genie.li, Discover the parseable command list for one pyATS os.      Worker-only: lazily i, refresh_parser_catalog_for_os() (+15 more)

### Community 4 - "PyatsJob"
Cohesion: 0.10
Nodes (35): Meta, PyatsCaptureScheduleType, PyatsCredentialType, PyatsJobType, PyatsParserCatalogRefreshScheduleType, PyatsParserCatalogType, PyatsSnapshotDiffType, PyatsSnapshotType (+27 more)

### Community 5 - "_flagged"
Cohesion: 0.10
Nodes (9): _flagged(), Regression test for the ATW-116 secret/PII detection allowlist/regex.  Validates, ATW-167 root-cause regression: a real-shaped value placed in the     fixture fil, Return list of (rule_id, matched_segment) the gitleaks rules would flag., Concrete leaks that MUST be flagged (the ATW-114 regression set)., Placeholder / RFC1918 / loopback forms that MUST NOT be flagged., SecretDetectionATW167Regression, SecretDetectionNegativeCases (+1 more)

### Community 6 - "test_graphify_scrub_guard.py"
Cohesion: 0.13
Nodes (31): CompletedProcess, extended_repo(), _make_extended_tree(), _make_tree(), Tests for scripts/graphify-scrub-guard.sh.  The scrub guard is the structural ba, Build a tree with cache/, a dated backup dir, and .graphify_* state., A tree with clean cache/dated/state files must pass the guard., A leak in cache/stat-index.json must be caught (ATW-307 regression class). (+23 more)

### Community 7 - "capture_snapshot"
Cohesion: 0.14
Nodes (10): _capture_parse(), capture_snapshot(), Run on-demand parser capture for an explicit, user-supplied command list.      T, Capture a snapshot from a single, already-connected pyATS Device.      This is t, FakePyatsDevice, kind='parse' runs device.parse() per user-supplied command and writes     the sa, Duck-typed pyATS Device for capture tests.      Only the attributes/methods :fun, TestBadKind (+2 more)

### Community 8 - "resolve_panel_platform_support"
Cohesion: 0.12
Nodes (18): Platform-support decision for the device-page PyATS panel (ATW-184).  Pure-Pytho, Return ``(platform_supported, os_value)`` for the device-page panel.      Combin, resolve_panel_platform_support(), FakeDevice, FakePlatform, FakeSnapshot, Tests for the device-page panel platform-support decision (ATW-184).  Pure-Pytho, TestResolvePanelPlatformSupport (+10 more)

### Community 9 - "CaptureResult"
Cohesion: 0.11
Nodes (10): CaptureResult, Outcome of a single :func:`capture_snapshot` call.      The :class:`~netbox_pyat, Length of the JSON-serialized ``data`` payload, in bytes., TestCaptureResultSizeBytes, BatchCaptureJobTest, CaptureJobPyatsJobPlumbingTest, ParseJobPyatsJobPlumbingTest, ADR-0005 §3 plumbing for ``capture_snapshot_job`` (Phase 5, ATW-16). (+2 more)

### Community 10 - "run_capture_schedules_job"
Cohesion: 0.10
Nodes (13): RQ worker entry point — dispatch captures for all enabled schedules.      Thin m, Dispatch captures for all enabled schedules (delegates to the wrapper)., run_capture_schedules_job(), Re-resolve :attr:`device_filter` to a Device queryset (run-time).          Thin, Re-resolve a ``device_filter`` JSON spec to a Device queryset at run time., _resolve_device_filter(), PyatsCaptureScheduleModelTest, Tests for the PyatsCaptureSchedule model + run_capture_schedules_job dispatcher (+5 more)

### Community 11 - "DiffStatusChoices"
Cohesion: 0.10
Nodes (16): DiffStatusChoices, Outcome of a snapshot diff (Phase 3, ATW-14).      ``success`` means a structure, _AppendOnlyListViewsBase, PyatsComplianceRunListViewRenderTest, PyatsJobListViewRenderTest, PyatsSnapshotDiffListViewRenderTest, PyatsSnapshotListViewRenderTest, Regression tests for the four append-only plugin list views (ATW-183).  The list (+8 more)

### Community 12 - "build_testbed"
Cohesion: 0.17
Nodes (12): build_testbed(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, _cred_resolver_factory(), _fake_testbed_factory(), FakeCredential, FakeDevice, Return a credential_resolver that always returns ``cred`` (or None)., Return a ``_pyats_testbed_cls`` callable: a function returning a raising class. (+4 more)

### Community 13 - "SnapshotKindChoices"
Cohesion: 0.11
Nodes (15): Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotKindChoices, SnapshotStatusChoices, Tests for :class:`netbox_pyats.models.PyatsGoldenConfig` and :class:`netbox_pyat, Integration render test for the side-by-side diff table (ATW-524/ATW-525).  Repl, DeviceBulkCaptureViewTest (+7 more)

### Community 14 - "test_navmenu_uniqueness_guard.py"
Cohesion: 0.10
Nodes (18): _extract_menu_item_kwargs(), _extract_menu_links(), _extract_model_classes(), _extract_schema_type_models(), GraphQLSchemaCompletenessGuard, NavMenuUniquenessGuard, Hardening guard for the navigation menu and GraphQL schema surface.  These tests, Return ``{model_name: type_class_name}`` parsed from ``schema.py``.      Each `` (+10 more)

### Community 15 - "diff_snapshots"
Cohesion: 0.11
Nodes (8): diff_snapshots(), Diff two serialized snapshot payloads and return a structured result.      Args:, The whole diff tree must round-trip through json.dumps (it's JSONB)., TestAddedRemovedChanged, TestDiffResultSizeBytes, TestEmptyAndError, TestLists, TestNestedDicts

### Community 16 - "flatten_diff_tree"
Cohesion: 0.13
Nodes (8): flatten_diff_tree(), Flatten a structured diff tree into a list of side-by-side table rows.      Walk, Unit tests for :func:`netbox_pyats.diff.flatten_diff_tree` (ATW-524/ATW-525).  P, TestFlattenEmptyAndError, TestFlattenLists, TestFlattenNestedContainerLeafValues, TestFlattenNestedDicts, TestFlattenRoundTrip

### Community 17 - "PyatsCredential"
Cohesion: 0.13
Nodes (21): Meta, PyatsCredential, A plugin-local, encrypted credential for connecting to a device via pyATS., Meta, PyatsCaptureScheduleTable, PyatsComplianceRunTable, PyatsCredentialTable, PyatsGoldenConfigTable (+13 more)

### Community 18 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 19 - "PyatsGoldenConfigAPITest"
Cohesion: 0.09
Nodes (6): APITestCase, PyatsCredentialAPITest, REST API tests for the PyatsCredential model.  Requires a running NetBox/Django, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest, REST API tests for the Phase 4 models (PyatsGoldenConfig, PyatsComplianceRun).

### Community 20 - "PyatsCaptureSchedule"
Cohesion: 0.12
Nodes (18): PyatsCaptureSchedule, An operator-authored intent to capture snapshots on a recurring schedule (ATW-43, DeviceBulkCaptureView, DeviceCaptureView, DeviceComplianceView, DeviceDiffView, DeviceParseView, DeviceRefreshCatalogView (+10 more)

### Community 21 - "test_template_extension.py"
Cohesion: 0.09
Nodes (21): Module, Structural guard for the device-page PyATS tab registration (ATW-393 / ADR-0007), ATW-409 regression guard: DevicePyATSTabView.get_extra_context must     include, ADR-0007: the PluginTemplateExtension module is deleted., DevicePyATSTabView must be decorated with register_model_view(Device, 'pyats')., DevicePyATSTabView must subclass generic.ObjectView., DevicePyATSTabView must declare a ViewTab with label='PyATS'., ADR-0007: __init__.py must not register template_extensions. (+13 more)

### Community 22 - "DeviceDiffFormKindFilterTest"
Cohesion: 0.18
Nodes (6): DeviceDiffFormKindFilterTest, DeviceDiffViewKindFilterTest, _make_snapshot(), The ``device_diff`` view surfaces the kind filter as a redirect+flash., Create a minimal PyatsSnapshot row of the given kind for ``device``., Form-level kind-filter enforcement (ATW-241 child 4).

### Community 23 - "dev-worktree.sh"
Cohesion: 0.19
Nodes (12): cmd_add(), cmd_audit(), cmd_cleanup(), cmd_remove(), cmd_test(), cmd_up(), die(), enforce_concurrency_cap() (+4 more)

### Community 24 - "diff.py"
Cohesion: 0.18
Nodes (18): Any, _diff_dict(), _diff_list(), _diff_value(), _flatten_node(), _join_path(), _leaf_type(), _node_status() (+10 more)

### Community 25 - "Dev environment bring-up"
Cohesion: 0.11
Nodes (19): Base branch policy (ATW-208), Bring-up, Cost model — per-worktree dev time, Dev environment bring-up, Image overrides (compatibility sweeps), Integration lane (Docker + NetBox), Keeping the split clean, Prerequisites (+11 more)

### Community 26 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 27 - "crypto.py"
Cohesion: 0.14
Nodes (15): decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), is_encrypted_token(), Encryption helpers for the plugin-local PyATS credential store.  Field-level enc, Decrypt a Fernet token produced by :func:`encrypt`.      Empty input round-trips (+7 more)

### Community 28 - "jobs.py"
Cohesion: 0.16
Nodes (17): _create_pyats_job(), enqueue_batch_capture(), enqueue_capture(), enqueue_compliance(), enqueue_diff(), enqueue_parse(), enqueue_refresh_parser_catalog(), NetBox background jobs for the netbox-pyats plugin.  Phase 2 (ATW-13) ships the (+9 more)

### Community 29 - "run_parser_catalog_refresh_schedules_job"
Cohesion: 0.17
Nodes (10): _next_run_at(), Compute the ``next_run_at`` timestamp for a recurring schedule (ATW-610).      T, RQ worker entry point — refresh the parser catalog when the schedule is enabled., Dispatch a parser catalog refresh when the schedule is enabled.          ``JobRu, run_parser_catalog_refresh_schedules_job(), Tests for the PyatsParserCatalogRefreshSchedule model + dispatcher (ATW-581).  R, Recurring enabled run → next_run_at = last_run_at + interval (ATW-610)., Recurring disabled-skip → next_run_at still set from interval (ATW-610). (+2 more)

### Community 30 - "group_snapshots_by_kind"
Cohesion: 0.18
Nodes (9): group_snapshots_by_kind(), Pure-Python helpers for the device-page PyATS tab (ATW-393, ADR-0007).  This mod, Group snapshots by ``kind`` for the diff picker (ATW-241 child 4).      Returns, FakeSnapshot, QA-independent verification for the ATW-252 diff picker kind filter.  Written by, Render the device-tab diff-picker partial and assert the ATW-252     contract: o, Minimal stand-in: only ``kind`` and ``pk`` are read by the helper., TestDeviceTabTemplateOptgroup (+1 more)

### Community 31 - "run_diff_job"
Cohesion: 0.18
Nodes (17): BaseException, capture_snapshot_job(), _finish_success(), _mark_running(), parse_commands_job(), _persist_error_row(), RQ worker entry point — run on-demand parses and persist the snapshot.      NetB, Set a :class:`PyatsJob` to ``running`` with ``started_at=now()``.      Called at (+9 more)

### Community 32 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 33 - "choices.py"
Cohesion: 0.12
Nodes (9): Choice sets for the netbox-pyats plugin., Migration, Migration, Migration, Migration, Migration, Migration, ATW-241 child 1 (ATW-249): add PyatsParserCatalog + the `kind='parse'` choice. (+1 more)

### Community 34 - "run_compliance"
Cohesion: 0.20
Nodes (4): Compare a golden config text against a snapshot's raw config text and classify., run_compliance(), TestDrift, TestErrorInputs

### Community 35 - "DeviceDiffForm"
Cohesion: 0.12
Nodes (8): DeviceDiffForm, PyatsCredentialForm, Form backing the device-page "Diff two snapshots" picker (Phase 3).      Posted, Initialize the form with an optional device scope.          Args:             de, Create/edit form for a PyATS Credential.      Plaintext password/enable_secret a, Initialize the form, optionally pinning the ``commands`` choices.          Args:, Require at least one of ``commands`` or ``manual_command``.          The parse j, Tests for the ``DeviceDiffForm`` kind filter (ATW-241 child 4 / ATW-252).  NetBo

### Community 36 - "test_pr_body_scrub_guard.py"
Cohesion: 0.18
Nodes (16): Tests for scripts/pr-body-scrub-guard.sh.  The PR body scrub guard is the struct, Role words in normal prose (not on a reviewer/merger line) are fine., An 8-char commit short-SHA must NOT trip the agent-prefix pattern., PR #44/#45 form: `[@CTO](agent://<uuid>)`., A bare RFC-4122 UUID anywhere in the body is caught., PR #47 form: `reviewer: @CTO (agent <prefix>)`., The exact PR #47 leaked line — prefix + role, caught by the prefix., _run() (+8 more)

### Community 38 - "extract_snapshot_raw_config"
Cohesion: 0.21
Nodes (5): extract_snapshot_raw_config(), Extract the snapshot's raw running-config text (the compliance "actual").      v, Regression test for the compliance job's legacy ``config[raw]`` fallback (ATW-43, Pin the contract of :func:`extract_snapshot_raw_config` (ATW-437)., TestExtractSnapshotRawConfig

### Community 39 - "testbed.py"
Cohesion: 0.15
Nodes (15): _build_device_entry(), _iter_devices(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), _pyats_testbed_cls(), NetBox → pyATS testbed bridge.  :func:`build_testbed` constructs a :class:`pyats, Return the management IP for a NetBox Device, preferring primary_ip4.      Retur (+7 more)

### Community 40 - "test_testbed.py"
Cohesion: 0.16
Nodes (9): is_supported_os(), True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)., DuplicateDeviceError, FakeDeviceType, FakeIPAddress, Exception, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS, Duck-type stand-in for ``pyats.topology.testbed.DuplicateDeviceError``.      The (+1 more)

### Community 41 - "PyatsComplianceRunViewTest"
Cohesion: 0.12
Nodes (3): PyatsComplianceRunViewTest, PyatsGoldenConfigViewTest, View tests for the Phase 4 compliance views (ATW-15).  Requires a running NetBox

### Community 42 - "ADR-0004: Compliance golden-config comparison shape"
Cohesion: 0.13
Nodes (15): Acceptance, ADR-0004: Compliance golden-config comparison shape, Capture change, Consequences, Consequences, Considered options, Considered options for v2, Context (+7 more)

### Community 43 - "Contributing to netbox-pyats"
Cohesion: 0.13
Nodes (15): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+7 more)

### Community 44 - "platform_to_pyats_os"
Cohesion: 0.31
Nodes (4): platform_to_pyats_os(), Map a NetBox ``Platform`` to a pyATS ``os`` string.      Returns the :data:`UNSU, FakePlatform, TestPlatformToOs

### Community 45 - "dev-seed.sh"
Cohesion: 0.27
Nodes (10): cmd_build(), cmd_force_restore(), cmd_info(), cmd_remove(), cmd_restore(), die(), _restore(), dev-seed.sh script (+2 more)

### Community 46 - "ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts"
Cohesion: 0.15
Nodes (13): 1. PR bodies use role-only labels — no identifiers (hard rule), 2. `[@Agent](agent://<id>)` is internal-only, 3. Boundary rule: public artifact vs internal comment, 4. Merger verifies before merge, 5. Retroactive redaction is harm-reduction, not elimination, ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts, Alternatives considered, Blast radius (+5 more)

### Community 47 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 48 - "Usage guide"
Cohesion: 0.15
Nodes (13): 1 — Add a credential, 2 — Capture a snapshot, 3 — On-demand Parse, 4 — Diff two snapshots, 5 — Add a golden config, 6 — Run compliance, 7 — Browse everything, 8 — Build a testbed programmatically (+5 more)

### Community 49 - "test_capture.py"
Cohesion: 0.15
Nodes (7): Exception, ParserNotFound, Tests for :mod:`netbox_pyats.capture`.  Pure-Python: exercises the snapshot capt, Duck-type stand-in for ``genie.libs.parser.utils.common.ParserNotFound``.      T, TestCaptureError, TestFullCapture, TestUnsupportedPlatform

### Community 50 - "test_compliance.py"
Cohesion: 0.15
Nodes (6): Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15; v2 ATW-434).  Pure-Py, The ordered diff can emit the same line text at multiple positions     (e.g. two, TestCompliant, TestDuplicateLines, TestJsonSerializable, TestUnknownModeDegradesToOrdered

### Community 53 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 54 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.24
Nodes (3): PyatsSnapshotDiffModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Regression for ATW-68: a diff error row with before/after NULL must         roun

### Community 55 - "test_supported_platforms.py"
Cohesion: 0.17
Nodes (5): Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, Report contents: the static map renders with per-slug device counts., ADR-0001 §6: the data path the report view reads must not import Genie.      The, SupportedPlatformsReportViewTest, TestSupportedPlatformsReportWebProcessSafety

### Community 56 - "TestSupportedPlatformsMap"
Cohesion: 0.17
Nodes (3): The static map the report renders (Phase 5, ATW-16, Option A)., TestSupportedPlatformsMap, FakeManufacturer

### Community 57 - ".get"
Cohesion: 0.20
Nodes (4): Resolve the pyATS os + catalog row + command choices for a device.      Web-proc, Return the POST URL for the device-page "Refresh parser list" button., _refresh_parser_catalog_url_for_device(), _resolve_parse_context()

### Community 58 - "netbox-pyats"
Cohesion: 0.17
Nodes (12): At a glance, Capture, Compare, Compatibility matrix, Compliance & Jobs, Device-page UI, Documentation, Getting help (+4 more)

### Community 59 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 60 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.18
Nodes (11): Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites, Remote agent wiring (Senior Dev Engineer), Secret rotation (+3 more)

### Community 61 - "resolve_state_commands"
Cohesion: 0.25
Nodes (6): _get_plugin_config(), Return the plugin's PLUGINS_CONFIG block (empty dict if unset).      Mirrors :fu, Return the state-capture command list for a given pyATS ``os``.      Resolution, resolve_state_commands(), ATW-432: resolve_state_commands picks per-OS command sets from     PLUGINS_CONFI, TestResolveStateCommands

### Community 62 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 63 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 64 - "compliance.py"
Cohesion: 0.24
Nodes (9): _build_tree(), _normalize_lines(), _ordered_diff(), Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Normalize a running-config text into a list of comparable lines.      Drops blan, Build the JSON-serializable diff tree and summary from leaf lists.      The tree, v2 ordered (sequence-aware) diff via :mod:`difflib`.      Walks :func:`difflib.S, v1 set (order-independent) diff.      Compares the two line lists as sets and re (+1 more)

### Community 69 - "TestStateCommandsInvariant"
Cohesion: 0.20
Nodes (3): Hardening invariant guard for :data:`netbox_pyats.capture.STATE_COMMANDS` (ATW-4, Structural invariants for :data:`STATE_COMMANDS` (ATW-436)., TestStateCommandsInvariant

### Community 70 - "[0.1.0] - Unreleased"
Cohesion: 0.22
Nodes (9): [0.1.0] - Unreleased, Added, Added, Changed, Changelog, Compatibility, Dev, Docs (+1 more)

### Community 71 - "Scheduled captures"
Cohesion: 0.22
Nodes (9): Creating a schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled captures, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 72 - "Scheduled parser-catalog refresh"
Cohesion: 0.22
Nodes (9): Enabling the schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled parser-catalog refresh, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 73 - "DiffLine"
Cohesion: 0.36
Nodes (3): DiffLine, One flat row in a side-by-side diff table (ATW-524/ATW-525).      A flattened vi, TestFlattenLeaves

### Community 74 - "TestbedBuildReport"
Cohesion: 0.22
Nodes (3): Summary of a :func:`build_testbed` run.      Keeps track of which devices were i, True if at least one device was supported AND none errored.          ``build_tes, TestbedBuildReport

### Community 75 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 76 - "ADR-0008: Scheduling surface for recurring snapshot capture"
Cohesion: 0.25
Nodes (8): ADR-0008: Scheduling surface for recurring snapshot capture, Alternatives considered, Consequences, Context, Decision, References, Structural shape, Why this fits the locked architecture

### Community 77 - "Graphify"
Cohesion: 0.25
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 78 - "Compliance engine"
Cohesion: 0.25
Nodes (8): Both modes are line-oriented text diff, not Genie-structured diff, Classification, Compliance engine, Engine layer, Related, The diff view, What it does, What the snapshot needs

### Community 79 - "Upgrade guide"
Cohesion: 0.25
Nodes (8): Before you begin, Both at once (NetBox + plugin upgrade), NetBox upgrade (plugin release unchanged), Next steps, Plugin upgrade (NetBox release unchanged), Troubleshooting an upgrade, Upgrade guide, What stays in sync with what

### Community 80 - "PyATS worker deployment"
Cohesion: 0.25
Nodes (8): Option A — install pyats into your own worker, Option B — the shipped worker image (reference / dev), PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, What runs on the `pyats` queue, Why a separate queue

### Community 81 - "capture_snapshot_for_netbox_device"
Cohesion: 0.25
Nodes (8): capture_snapshot_for_netbox_device(), Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a single-device testbed, connect, capture, disconnect.      Convenience wr, _worker_versions(), batch_capture_job(), _finish_partial(), Set a batch :class:`PyatsJob` to ``partial`` with batch counts (ADR-0005 §3 + §2, RQ worker entry point — capture snapshots for a batch of devices.      NetBox's

### Community 82 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 83 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 84 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 85 - "Graphify MCP"
Cohesion: 0.29
Nodes (7): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, remote / HTTP config (multi-host, opt-in), stdio config (single-host, default), Switching from stdio to HTTP, Tools exposed (both transports), When to use which transport

### Community 86 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 87 - "PULL_REQUEST_TEMPLATE.md"
Cohesion: 0.29
Nodes (6): Changes, Closing checklist, Linked issue, Notes for reviewers, Summary, Verification

### Community 88 - "TestStateCapture"
Cohesion: 0.29
Nodes (4): kind=state runs device.parse() for each command in STATE_COMMANDS., Per-command ParserNotFound is recorded as a warning, not a failure., CR-3: a non-ParserNotFound parse exception is a real failure, not a         beni, TestStateCapture

### Community 94 - "ADR-0007: Device-page tab via `register_model_view` + `ObjectView`"
Cohesion: 0.33
Nodes (6): ADR-0007: Device-page tab via `register_model_view` + `ObjectView`, Alternatives considered, Consequences, Context, Decision, References

### Community 95 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 96 - "ComplianceResult"
Cohesion: 0.33
Nodes (4): ComplianceResult, Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift).

### Community 97 - "DiffResult"
Cohesion: 0.33
Nodes (4): DiffResult, Outcome of a single :func:`diff_snapshots` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves.

### Community 99 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 100 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 101 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 102 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 105 - "TestCase"
Cohesion: 0.40
Nodes (3): DeviceRefreshCatalogViewTest, View tests for :class:`views.DeviceRefreshCatalogView` (ATW-250)., TestCase

### Community 109 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 110 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 111 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **285 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-test-entrypoint.sh script`, `DJANGO_SETTINGS_MODULE`, `Migration` (+280 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SnapshotKindChoices` connect `SnapshotKindChoices` to `PyatsSnapshot`, `ComplianceResultChoices`, `PyatsJob`, `capture_snapshot`, `CaptureResult`, `run_capture_schedules_job`, `DiffStatusChoices`, `PyatsCredential`, `PyatsGoldenConfigAPITest`, `PyatsCaptureSchedule`, `DeviceDiffFormKindFilterTest`, `jobs.py`, `group_snapshots_by_kind`, `choices.py`, `DeviceDiffForm`, `PyatsComplianceRunViewTest`, `test_capture.py`, `PyatsComplianceRunModelTest`, `PyatsSnapshotDiffModelTest`, `resolve_state_commands`, `PyatsJobModelTest`, `PyatsSnapshotModelTest`, `TestStateCapture`, `PyatsGoldenConfigModelTest`, `DiffTableRenderTest`, `TestPerOsStateCapture`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `PyatsJob` connect `PyatsJob` to `PyatsSnapshot`, `views.py`, `ComplianceResultChoices`, `DeviceDiffForm`, `refresh_parser_catalog_for_os`, `PyatsJobModelTest`, `CaptureResult`, `DiffStatusChoices`, `.get_status_color`, `SnapshotKindChoices`, `.related_result`, `PyatsCredential`, `PyatsCaptureSchedule`, `jobs.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `CredentialProtocolChoices` connect `ComplianceResultChoices` to `PyatsSnapshot`, `choices.py`, `PyatsCredentialModelTest`, `DeviceDiffForm`, `PyatsJob`, `testbed.py`, `test_testbed.py`, `TestbedBuildReport`, `build_testbed`, `platform_to_pyats_os`, `PyatsCredential`, `PyatsCaptureSchedule`, `TestSupportedPlatformsMap`, `crypto.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 153 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshot` has 153 INFERRED edges - model-reasoned connections that need verification._
- **Are the 143 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsJob` has 143 INFERRED edges - model-reasoned connections that need verification._
- **Are the 145 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 145 INFERRED edges - model-reasoned connections that need verification._
- **Are the 132 inferred relationships involving `PyatsComplianceRun` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsComplianceRun` has 132 INFERRED edges - model-reasoned connections that need verification._