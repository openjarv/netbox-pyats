# Graph Report - .  (2026-08-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2083 nodes · 5486 edges · 150 communities (113 shown, 37 thin omitted)
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 2072 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8ccdd133`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PyatsJob
- SnapshotKindChoices
- views.py
- refresh_parser_catalog_for_os
- DiffStatusChoices
- run_compliance
- resolve_panel_platform_support
- capture_snapshot
- PyatsCaptureScheduleCleanTest
- _flagged
- diff_snapshots
- test_graphify_scrub_guard.py
- CaptureResult
- PyatsCredential
- flatten_diff_tree
- PyatsSnapshotDiff
- test_navmenu_uniqueness_guard.py
- PyatsSnapshot
- PyatsSnapshotDiffModelTest
- What You Must Do When Invoked
- run_diff_job
- test_template_extension.py
- test_append_only_list_views.py
- DeviceParseViewTest
- FakePyatsDevice
- _EditableListViewsBase
- DeviceDiffFormKindFilterTest
- run_parser_catalog_refresh_schedules_job
- build_testbed
- PyatsComplianceRunModelTest
- dev-worktree.sh
- Dev environment bring-up
- diff.py
- EncryptDecryptTest
- jobs.py
- run_capture_schedules_job
- test_pr_body_scrub_guard.py
- Troubleshooting
- ComplianceResultChoices
- extract_snapshot_raw_config
- PyatsJobModelTest
- test_testbed.py
- WorkerStatusBadgeViewTest
- ADR-0004: Compliance golden-config comparison shape
- Contributing to netbox-pyats
- platform_to_pyats_os
- PyatsComplianceRunViewTest
- GenieDiffViewTest
- GenieParseViewTest
- Usage guide
- dev-seed.sh
- ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts
- Remote access to the dev NetBox UI over Tailscale
- PyatsGoldenConfigAPITest
- test_supported_platforms.py
- contributing.md
- PyATS worker deployment
- GenieLearnViewTest
- _extract_snapshot_raw
- PyatsCredentialModelTest
- TestSupportedPlatformsMap
- get_worker_status
- _resolve_parse_context
- netbox-pyats
- ADR-0002: Multi-vendor graceful degradation pattern
- Graphify MCP HTTP server — multi-host / shared-service runbook
- FakeOpsInstance
- resolve_state_commands
- _build_device_entry
- PyatsComplianceRun
- TestbedBuildReport
- test_search_index_guard.py
- .get
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- capture_snapshot_for_netbox_device
- get_fernet_key
- test_capture.py
- TestStateCommandsInvariant
- [0.1.0] - Unreleased
- Scheduled captures
- Scheduled parser-catalog refresh
- FakeCredential
- TestWorkerStatusFallback
- graphify reference: extra exports and benchmark
- ADR-0008: Scheduling surface for recurring snapshot capture
- Graphify
- Compliance engine
- Upgrade guide
- PyatsCredentialAPITest
- DiffTableRenderTest
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Graphify MCP
- Installation
- PULL_REQUEST_TEMPLATE.md
- _validate_device_filter
- TestStateCapture
- PyatsCredentialViewTest
- ADR-0007: Device-page tab via `register_model_view` + `ObjectView`
- Architecture Decision Records
- DiffResult
- .__init__
- graphify reference: query, path, explain
- graphify-mcp-key.sh
- netbox-pyats documentation
- __init__.py
- pyats-test-entrypoint.sh
- .clean
- TestFlattenLists
- DeviceBulkCaptureViewTest
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- entrypoint.sh
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- 0010_parser_catalog_and_parse_kind.py
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify-scrub-guard.sh
- pr-body-scrub-guard.sh
- AGENTS.md
- _capture_parse
- .clean_device_filter
- 0004_reconcile_netboxmodel_fields.py
- 0006_compliance_run_nullable_fks.py
- 0007_snapshot_parsed_os.py
- 0008_pyatssnapshotdiff_nullable_fks.py
- 0012_compliance_run_mode.py
- 0013_pyatsparsercatalogrefreshschedule.py
- .is_from_snapshot
- .get_status_color
- .related_result
- _iter_devices
- _pyats_testbed_cls
- FakeIPAddress
- extraction-spec.md
- gitleaks-fixture-regression.sh
- test-unit.sh
- netbox-pyats

## God Nodes (most connected - your core abstractions)
1. `PyatsSnapshot` - 213 edges
2. `PyatsJob` - 191 edges
3. `PyatsSnapshotDiff` - 183 edges
4. `PyatsCaptureSchedule` - 172 edges
5. `PyatsCredential` - 170 edges
6. `PyatsGoldenConfig` - 167 edges
7. `PyatsComplianceRun` - 166 edges
8. `SnapshotKindChoices` - 158 edges
9. `PyatsParserCatalogRefreshSchedule` - 152 edges
10. `PyatsParserCatalog` - 137 edges

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

## Communities (150 total, 37 thin omitted)

### Community 0 - "PyatsJob"
Cohesion: 0.06
Nodes (103): JobRunner, Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotTriggerChoices, Meta, Recurring dispatcher for capture schedules (ATW-433, ADR-0008).      A registere, Recurring dispatcher for the parser catalog refresh (ATW-581).      A registered, RunCaptureSchedulesJob, RunParserCatalogRefreshSchedulesJob (+95 more)

### Community 1 - "SnapshotKindChoices"
Cohesion: 0.05
Nodes (42): Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Choice sets for the netbox-pyats plugin., What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotKindChoices, SnapshotStatusChoices, is_encrypted_token(), Encryption helpers for the plugin-local PyATS credential store.  Field-level enc (+34 more)

### Community 2 - "views.py"
Cohesion: 0.12
Nodes (59): Meta, PyatsCaptureScheduleSerializer, PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsParserCatalogRefreshScheduleSerializer, PyatsParserCatalogSerializer (+51 more)

### Community 3 - "refresh_parser_catalog_for_os"
Cohesion: 0.06
Nodes (28): CatalogRefreshResult, Parser-catalog refresh core — the Genie work, isolated from NetBox/RQ.  :func:`r, Return the deduplicated set of Genie-supported pyATS os strings.      Derived fr, Outcome of a single :func:`refresh_parser_catalog_for_os` call.      The :func:`, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a minimal ``pyats.topology.Device`` with only ``.os`` set.      ``genie.li, Discover the parseable command list for one pyATS os.      Worker-only: lazily i, refresh_parser_catalog_for_os() (+20 more)

### Community 4 - "DiffStatusChoices"
Cohesion: 0.13
Nodes (54): ComplianceModeChoices, CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices, Outcome of a snapshot diff (Phase 3, ATW-14).      ``success`` means a structure (+46 more)

### Community 5 - "run_compliance"
Cohesion: 0.06
Nodes (20): _build_tree(), _normalize_lines(), _ordered_diff(), Normalize a running-config text into a list of comparable lines.      Drops blan, Build the JSON-serializable diff tree and summary from leaf lists.      The tree, v2 ordered (sequence-aware) diff via :mod:`difflib`.      Walks :func:`difflib.S, v1 set (order-independent) diff.      Compares the two line lists as sets and re, Compare a golden config text against a snapshot's raw config text and classify. (+12 more)

### Community 6 - "resolve_panel_platform_support"
Cohesion: 0.08
Nodes (24): Return ``(platform_supported, os_value)`` for the device-page panel.      Combin, resolve_panel_platform_support(), group_snapshots_by_kind(), Group snapshots by ``kind`` for the diff picker (ATW-241 child 4).      Returns, FakeSnapshot, QA-independent verification for the ATW-252 diff picker kind filter.  Written by, Render the device-tab diff-picker partial and assert the ATW-252     contract: o, Minimal stand-in: only ``kind`` and ``pk`` are read by the helper. (+16 more)

### Community 7 - "capture_snapshot"
Cohesion: 0.10
Nodes (15): _capture_config(), capture_snapshot(), _capture_state(), Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u, Run parser-based state capture on a connected pyATS Device.      Runs the given, Capture a snapshot from a single, already-connected pyATS Device.      This is t, FakePyatsDevice, kind='parse' runs device.parse() per user-supplied command and writes     the sa (+7 more)

### Community 8 - "PyatsCaptureScheduleCleanTest"
Cohesion: 0.08
Nodes (14): Re-resolve :attr:`device_filter` to a Device queryset (run-time).          Thin, Re-resolve a ``device_filter`` JSON spec to a Device queryset at run time., _resolve_device_filter(), TestCase, PyatsCaptureScheduleCleanTest, PyatsCaptureScheduleModelTest, _PyatsCaptureScheduleModelTestHD2, Model-level ``device_filter`` validation (ATW-814 CR-1).      ``PyatsCaptureSche (+6 more)

### Community 9 - "_flagged"
Cohesion: 0.10
Nodes (9): _flagged(), Regression test for the ATW-116 secret/PII detection allowlist/regex.  Validates, ATW-167 root-cause regression: a real-shaped value placed in the     fixture fil, Return list of (rule_id, matched_segment) the gitleaks rules would flag., Concrete leaks that MUST be flagged (the ATW-114 regression set)., Placeholder / RFC1918 / loopback forms that MUST NOT be flagged., SecretDetectionATW167Regression, SecretDetectionNegativeCases (+1 more)

### Community 10 - "diff_snapshots"
Cohesion: 0.10
Nodes (12): diff_snapshots(), Diff two serialized snapshot payloads and return a structured result.      Args:, Tests for :mod:`netbox_pyats.diff`.  Pure-Python: exercises the structured diff, The whole diff tree must round-trip through json.dumps (it's JSONB)., Diff two Genie-parser-shaped snapshot payloads end-to-end., TestAddedRemovedChanged, TestDiffResultSizeBytes, TestEmptyAndError (+4 more)

### Community 11 - "test_graphify_scrub_guard.py"
Cohesion: 0.13
Nodes (31): extended_repo(), _make_extended_tree(), _make_tree(), CompletedProcess, Path, Tests for scripts/graphify-scrub-guard.sh.  The scrub guard is the structural ba, Build a tree with cache/, a dated backup dir, and .graphify_* state., A tree with clean cache/dated/state files must pass the guard. (+23 more)

### Community 12 - "CaptureResult"
Cohesion: 0.11
Nodes (10): CaptureResult, Outcome of a single :func:`capture_snapshot` call.      The :class:`~netbox_pyat, Length of the JSON-serialized ``data`` payload, in bytes., TestCaptureResultSizeBytes, BatchCaptureJobTest, CaptureJobPyatsJobPlumbingTest, ParseJobPyatsJobPlumbingTest, ADR-0005 §3 plumbing for ``capture_snapshot_job`` (Phase 5, ATW-16). (+2 more)

### Community 13 - "PyatsCredential"
Cohesion: 0.10
Nodes (24): PyatsCredential, A plugin-local, encrypted credential for connecting to a device via pyATS., Encrypt and store the device password (ciphertext only)., Decrypt and return the device password (plaintext)., Encrypt and store the enable/privileged password (ciphertext only)., Decrypt and return the enable/privileged password (plaintext)., Meta, PyatsCaptureScheduleTable (+16 more)

### Community 14 - "flatten_diff_tree"
Cohesion: 0.13
Nodes (10): DiffLine, flatten_diff_tree(), One flat row in a side-by-side diff table (ATW-524/ATW-525).      A flattened vi, Flatten a structured diff tree into a list of side-by-side table rows.      Walk, Unit tests for :func:`netbox_pyats.diff.flatten_diff_tree` (ATW-524/ATW-525).  P, TestFlattenEmptyAndError, TestFlattenLeaves, TestFlattenNestedContainerLeafValues (+2 more)

### Community 15 - "PyatsSnapshotDiff"
Cohesion: 0.11
Nodes (21): Meta, PyatsCaptureScheduleType, PyatsCredentialType, PyatsJobType, PyatsParserCatalogRefreshScheduleType, PyatsParserCatalogType, PyatsSnapshotDiffType, PyatsSnapshotType (+13 more)

### Community 16 - "test_navmenu_uniqueness_guard.py"
Cohesion: 0.10
Nodes (19): _extract_menu_item_kwargs(), _extract_menu_links(), _extract_model_classes(), _extract_schema_type_models(), GraphQLSchemaCompletenessGuard, _is_menu_var(), NavMenuUniquenessGuard, Hardening guard for the navigation menu and GraphQL schema surface.  These tests (+11 more)

### Community 17 - "PyatsSnapshot"
Cohesion: 0.12
Nodes (20): PyatsSnapshot, One captured config/state/full snapshot for a NetBox Device.      Populated by t, Map status to a NetBox color label for table badges., True if this snapshot row carries parser warnings / error context., PyatsCaptureScheduleIndex, PyatsComplianceRunIndex, PyatsCredentialIndex, PyatsGoldenConfigIndex (+12 more)

### Community 18 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.09
Nodes (8): TestCase, PyatsSnapshotDiffModelTest, PyatsSnapshotModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Persistence and helper behavior of PyatsSnapshot., Regression for ATW-68: a diff error row with before/after NULL must         roun, Regression for ATW-68: ``run_diff_job``'s ``DoesNotExist`` branch must     write, RunDiffJobDoesNotExistTest

### Community 19 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 20 - "run_diff_job"
Cohesion: 0.14
Nodes (23): BaseException, capture_snapshot_job(), _finish_success(), learn_snapshot_job(), _mark_running(), parse_commands_job(), _persist_error_row(), _persist_input_error_row() (+15 more)

### Community 21 - "test_template_extension.py"
Cohesion: 0.09
Nodes (22): Module, Path, Structural guard for the device-page PyATS tab registration (ATW-393 / ADR-0007), ATW-409 regression guard: DevicePyATSTabView.get_extra_context must     include, ADR-0007: the PluginTemplateExtension module is deleted., DevicePyATSTabView must be decorated with register_model_view(Device, 'pyats')., DevicePyATSTabView must subclass generic.ObjectView., DevicePyATSTabView must declare a ViewTab with label='PyATS'. (+14 more)

### Community 22 - "test_append_only_list_views.py"
Cohesion: 0.11
Nodes (13): _AppendOnlyListViewsBase, TestCase, PyatsComplianceRunListViewRenderTest, PyatsJobListViewRenderTest, PyatsSnapshotDiffListViewRenderTest, PyatsSnapshotListViewRenderTest, Regression tests for the four append-only plugin list views (ATW-183).  The list, ``/plugins/pyats/diffs/`` must render 200 (ATW-183 regression). (+5 more)

### Community 23 - "DeviceParseViewTest"
Cohesion: 0.09
Nodes (8): DeviceParseFormTest, DeviceParseViewTest, DeviceRefreshCatalogViewTest, TestCase, Tests for the device-page Parse sub-tab (ATW-241 child 2, ATW-250).  Requires a, View tests for :class:`views.DeviceRefreshCatalogView` (ATW-250)., Pure-form validation for :class:`forms.DeviceParseForm`., View tests for :class:`views.DeviceParseView` (ATW-250).

### Community 24 - "FakePyatsDevice"
Cohesion: 0.19
Nodes (11): FakeLookup, FakeOpsFactory, FakeOpsNamespace, FakePyatsDevice, _patch_genie_ops(), Inject a fake ``genie.ops.utils.Lookup`` + ``genie.libs.ops`` into ``sys.modules, Minimal duck-typed pyATS Device for Learn tests.      The Learn path only reads, Callable that returns a :class:`FakeOpsInstance` when called with a device. (+3 more)

### Community 25 - "_EditableListViewsBase"
Cohesion: 0.10
Nodes (12): _EditableListViewsBase, TestCase, PyatsCaptureScheduleListViewRenderTest, PyatsCredentialListViewRenderTest, PyatsGoldenConfigListViewRenderTest, PyatsParserCatalogRefreshScheduleListViewRenderTest, Regression tests for the four editable plugin list views (ATW-817).  The list vi, ``/plugins/pyats/golden-configs/`` must render 200 (ATW-817 regression). (+4 more)

### Community 26 - "DeviceDiffFormKindFilterTest"
Cohesion: 0.17
Nodes (7): DeviceDiffFormKindFilterTest, DeviceDiffViewKindFilterTest, _make_snapshot(), TestCase, The ``device_diff`` view surfaces the kind filter as a redirect+flash., Create a minimal PyatsSnapshot row of the given kind for ``device``., Form-level kind-filter enforcement (ATW-241 child 4).

### Community 27 - "run_parser_catalog_refresh_schedules_job"
Cohesion: 0.14
Nodes (11): RQ worker entry point — refresh the parser catalog when the schedule is enabled., Dispatch a parser catalog refresh when the schedule is enabled.          ``JobRu, run_parser_catalog_refresh_schedules_job(), TestCase, PyatsParserCatalogRefreshScheduleModelTest, Tests for the PyatsParserCatalogRefreshSchedule model + dispatcher (ATW-581).  R, Recurring enabled run → next_run_at = last_run_at + interval (ATW-610)., Recurring disabled-skip → next_run_at still set from interval (ATW-610). (+3 more)

### Community 28 - "build_testbed"
Cohesion: 0.28
Nodes (6): build_testbed(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, _cred_resolver_factory(), FakeDevice, Return a credential_resolver that always returns ``cred`` (or None)., TestBuildTestbed

### Community 29 - "PyatsComplianceRunModelTest"
Cohesion: 0.16
Nodes (5): TestCase, PyatsComplianceRunModelTest, PyatsGoldenConfigModelTest, Persistence and helper behavior of PyatsComplianceRun (Phase 4, ATW-15)., Persistence and helper behavior of PyatsGoldenConfig.

### Community 30 - "dev-worktree.sh"
Cohesion: 0.19
Nodes (12): cmd_add(), cmd_audit(), cmd_cleanup(), cmd_remove(), cmd_test(), cmd_up(), die(), enforce_concurrency_cap() (+4 more)

### Community 31 - "Dev environment bring-up"
Cohesion: 0.11
Nodes (19): Base branch policy (ATW-208), Bring-up, Cost model — per-worktree dev time, Dev environment bring-up, Image overrides (compatibility sweeps), Integration lane (Docker + NetBox), Keeping the split clean, Prerequisites (+11 more)

### Community 32 - "diff.py"
Cohesion: 0.18
Nodes (18): _diff_dict(), _diff_list(), _diff_value(), _flatten_node(), _join_path(), _leaf_type(), _node_status(), Any (+10 more)

### Community 33 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 34 - "jobs.py"
Cohesion: 0.16
Nodes (17): _create_pyats_job(), enqueue_batch_capture(), enqueue_capture(), enqueue_compliance(), enqueue_diff(), enqueue_learn(), enqueue_parse(), enqueue_refresh_parser_catalog() (+9 more)

### Community 35 - "run_capture_schedules_job"
Cohesion: 0.18
Nodes (9): _next_run_at(), Compute the ``next_run_at`` timestamp for a recurring schedule (ATW-610).      T, RQ worker entry point — dispatch captures for all enabled schedules.      Thin m, Dispatch captures for all enabled schedules (delegates to the wrapper)., run_capture_schedules_job(), run_capture_schedules_job dispatch logic (ATW-433)., Recurring run (Job.interval set) → next_run_at = last_run_at + interval (ATW-610, Zero-device skip still sets next_run_at when Job.interval is set (ATW-610). (+1 more)

### Community 36 - "test_pr_body_scrub_guard.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, Tests for scripts/pr-body-scrub-guard.sh.  The PR body scrub guard is the struct, Role words in normal prose (not on a reviewer/merger line) are fine., An 8-char commit short-SHA must NOT trip the agent-prefix pattern., PR #44/#45 form: `[@CTO](agent://<uuid>)`., A bare RFC-4122 UUID anywhere in the body is caught., PR #47 form: `reviewer: @CTO (agent <prefix>)`., The exact PR #47 leaked line — prefix + role, caught by the prefix. (+9 more)

### Community 37 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 38 - "ComplianceResultChoices"
Cohesion: 0.15
Nodes (12): ComplianceResultChoices, Outcome of a compliance run (Phase 4, ATW-15).      ``compliant`` means the devi, ComplianceResult, Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift)., Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15; v2 ATW-434).  Pure-Py (+4 more)

### Community 40 - "extract_snapshot_raw_config"
Cohesion: 0.21
Nodes (5): extract_snapshot_raw_config(), Extract the snapshot's raw running-config text (the compliance "actual").      v, Regression test for the compliance job's legacy ``config[raw]`` fallback (ATW-43, Pin the contract of :func:`extract_snapshot_raw_config` (ATW-437)., TestExtractSnapshotRawConfig

### Community 41 - "PyatsJobModelTest"
Cohesion: 0.13
Nodes (5): DiffJobPyatsJobPlumbingTest, TestCase, PyatsJobModelTest, ADR-0005 §3 plumbing for ``run_diff_job`` (Phase 5, ATW-16)., Persistence + helpers for PyatsJob (Phase 5, ATW-16).

### Community 42 - "test_testbed.py"
Cohesion: 0.14
Nodes (11): DuplicateDeviceError, _fake_testbed_factory(), FakeDeviceType, Exception, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS, CR-2 (ATW-815): a wrong/tampered Fernet key must surface as a     ``CredentialDe, Duck-type stand-in for ``pyats.topology.testbed.DuplicateDeviceError``.      The, Return a ``_pyats_testbed_cls`` callable: a function returning a raising class. (+3 more)

### Community 43 - "WorkerStatusBadgeViewTest"
Cohesion: 0.12
Nodes (3): TestCase, The six worker-using views must render the worker status badge (ATW-804).      `, WorkerStatusBadgeViewTest

### Community 44 - "ADR-0004: Compliance golden-config comparison shape"
Cohesion: 0.13
Nodes (15): Acceptance, ADR-0004: Compliance golden-config comparison shape, Capture change, Consequences, Consequences, Considered options, Considered options for v2, Context (+7 more)

### Community 45 - "Contributing to netbox-pyats"
Cohesion: 0.13
Nodes (15): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+7 more)

### Community 46 - "platform_to_pyats_os"
Cohesion: 0.31
Nodes (4): platform_to_pyats_os(), Map a NetBox ``Platform`` to a pyATS ``os`` string.      Returns the :data:`UNSU, FakePlatform, TestPlatformToOs

### Community 47 - "PyatsComplianceRunViewTest"
Cohesion: 0.13
Nodes (3): TestCase, PyatsComplianceRunViewTest, PyatsGoldenConfigViewTest

### Community 48 - "GenieDiffViewTest"
Cohesion: 0.13
Nodes (4): GenieDiffViewTest, TestCase, Tests for the dedicated Genie Diff page (ATW-731).  Requires a running NetBox/Dj, View tests for :class:`views.GenieDiffView` (ATW-731).

### Community 49 - "GenieParseViewTest"
Cohesion: 0.13
Nodes (4): GenieParseViewTest, TestCase, Tests for the dedicated Genie Parse page (ATW-729).  Requires a running NetBox/D, View tests for :class:`views.GenieParseView` (ATW-729).

### Community 50 - "Usage guide"
Cohesion: 0.14
Nodes (14): 1 — Add a credential, 2 — Capture a snapshot, 3 — Run an on-demand Parse, 4 — Run a Genie Learn capture, 5 — Diff two snapshots, 6 — Add a golden config, 7 — Run compliance, 8 — Browse everything (+6 more)

### Community 51 - "dev-seed.sh"
Cohesion: 0.27
Nodes (10): cmd_build(), cmd_force_restore(), cmd_info(), cmd_remove(), cmd_restore(), die(), _restore(), dev-seed.sh script (+2 more)

### Community 52 - "ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts"
Cohesion: 0.15
Nodes (13): 1. PR bodies use role-only labels — no identifiers (hard rule), 2. `[@Agent](agent://<id>)` is internal-only, 3. Boundary rule: public artifact vs internal comment, 4. Merger verifies before merge, 5. Retroactive redaction is harm-reduction, not elimination, ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts, Alternatives considered, Blast radius (+5 more)

### Community 53 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 54 - "PyatsGoldenConfigAPITest"
Cohesion: 0.15
Nodes (3): APITestCase, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest

### Community 55 - "test_supported_platforms.py"
Cohesion: 0.15
Nodes (6): TestCase, Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, Report contents: the static map renders with per-slug device counts., ADR-0001 §6: the data path the report view reads must not import Genie.      The, SupportedPlatformsReportViewTest, TestSupportedPlatformsReportWebProcessSafety

### Community 57 - "PyATS worker deployment"
Cohesion: 0.17
Nodes (12): Option A — install pyats into your own worker, Option B — the shipped worker image (reference / dev), PyATS worker deployment, Running the worker, The ~15-second cache, The badge is informational only, Troubleshooting, Verifying the queue and worker (+4 more)

### Community 58 - "GenieLearnViewTest"
Cohesion: 0.17
Nodes (4): GenieLearnViewTest, TestCase, Tests for the dedicated Genie Learn page (ATW-730).  Requires a running NetBox/D, View tests for :class:`views.GenieLearnView` (ATW-730).

### Community 59 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 60 - "PyatsCredentialModelTest"
Cohesion: 0.17
Nodes (3): TestCase, PyatsCredentialModelTest, Field-level encryption and validation behavior of PyatsCredential.

### Community 61 - "TestSupportedPlatformsMap"
Cohesion: 0.17
Nodes (3): The static map the report renders (Phase 5, ATW-16, Option A)., TestSupportedPlatformsMap, FakeManufacturer

### Community 62 - "get_worker_status"
Cohesion: 0.21
Nodes (8): Tests for the worker status indicator (ATW-804).  Two lanes, matching the repo's, _check_worker_status(), _get_cache(), get_worker_status(), Worker status helper for the pyATS RQ queue (ATW-804).  A pure-Python, resilient, Return the Django cache backend or ``None`` when unavailable.      Pure-Python m, Return ``(online, reason)`` for the dedicated ``pyats`` RQ queue.      ``online=, Run the actual RQ/Redis worker check (uncached).      Kept separate from :func:`

### Community 63 - "_resolve_parse_context"
Cohesion: 0.21
Nodes (4): Resolve the pyATS os + catalog row + command choices for a device.      Web-proc, Return the POST URL for the device-page "Refresh parser list" button., _refresh_parser_catalog_url_for_device(), _resolve_parse_context()

### Community 64 - "netbox-pyats"
Cohesion: 0.17
Nodes (12): At a glance, Capture, Compare, Compatibility matrix, Compliance & Jobs, Device-page UI, Documentation, Getting help (+4 more)

### Community 65 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 66 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.18
Nodes (11): Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites, Remote agent wiring (Senior Dev Engineer), Secret rotation (+3 more)

### Community 67 - "FakeOpsInstance"
Cohesion: 0.20
Nodes (7): _capture_learn(), _discover_ops_features(), Any, Run the Genie Ops Learn capture on a connected pyATS Device (ATW-730).      Geni, Return ``[(feature_name, ops_factory), ...]`` from a Genie Ops Lookup.      Feat, FakeOpsInstance, Duck-typed Genie Ops instance returned by an Ops class factory.      ``_capture_

### Community 68 - "resolve_state_commands"
Cohesion: 0.25
Nodes (6): _get_plugin_config(), Return the plugin's PLUGINS_CONFIG block (empty dict if unset).      Mirrors :fu, Return the state-capture command list for a given pyATS ``os``.      Resolution, resolve_state_commands(), ATW-432: resolve_state_commands picks per-OS command sets from     PLUGINS_CONFI, TestResolveStateCommands

### Community 69 - "_build_device_entry"
Cohesion: 0.18
Nodes (11): CredentialDecryptError, Exception, Raised when a stored Fernet token cannot be decrypted (ATW-815, CR-2).      Wrap, _build_device_entry(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), Return the management IP for a NetBox Device, preferring primary_ip4.      Retur (+3 more)

### Community 70 - "PyatsComplianceRun"
Cohesion: 0.18
Nodes (5): PyatsComplianceRun, One compliance check result: golden config vs. captured snapshot (Phase 4, ATW-1, Map result to a NetBox color label for table badges., True if the diff found any added/removed/changed leaves (drift)., True if this compliance run row carries warnings / error context.

### Community 71 - "TestbedBuildReport"
Cohesion: 0.20
Nodes (5): _device_display_name(), Return a human-readable name for a NetBox Device.      NetBox permits ``Device.n, Summary of a :func:`build_testbed` run.      Keeps track of which devices were i, True if at least one device was supported AND none errored.          ``build_tes, TestbedBuildReport

### Community 72 - "test_search_index_guard.py"
Cohesion: 0.24
Nodes (8): _extract_netbox_model_subclasses(), _extract_search_index_models(), Search-index completeness guard (ATW-816).  AST-only guard asserting every NetBo, Return NetBoxModel subclass names from models.py (AST)., Return model names registered in search.py (AST).      Collects ``model = <Name>, Every NetBoxModel subclass must have a SearchIndex unless excluded., Excluded models must still exist in models.py (no stale exclusion)., SearchIndexCompletenessGuard

### Community 73 - ".get"
Cohesion: 0.18
Nodes (5): _diff_list_url(), _genie_diff_post_url(), Return the most recent snapshots for a device (or empty list)., Return the POST URL for the Genie Diff page diff form., Return the full diff history list URL (pyatssnapshotdiff_list).

### Community 74 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 75 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 76 - "capture_snapshot_for_netbox_device"
Cohesion: 0.20
Nodes (10): capture_snapshot_for_netbox_device(), Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a single-device testbed, connect, capture, disconnect.      Convenience wr, _worker_versions(), batch_capture_job(), _finish_partial(), _persist_snapshot(), RQ worker entry point — capture snapshots for a batch of devices.      NetBox's (+2 more)

### Community 77 - "get_fernet_key"
Cohesion: 0.20
Nodes (10): decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), Decrypt a Fernet token produced by :func:`encrypt`.      Empty input round-trips, Return the plugin's PLUGINS_CONFIG block (empty dict if unset)., Derive a 32-byte url-safe base64 Fernet key from a slice of SECRET_KEY.      SHA (+2 more)

### Community 78 - "test_capture.py"
Cohesion: 0.20
Nodes (6): ParserNotFound, Exception, Tests for :mod:`netbox_pyats.capture`.  Pure-Python: exercises the snapshot capt, Duck-type stand-in for ``genie.libs.parser.utils.common.ParserNotFound``.      T, TestCaptureError, TestFullCapture

### Community 79 - "TestStateCommandsInvariant"
Cohesion: 0.20
Nodes (3): Hardening invariant guard for :data:`netbox_pyats.capture.STATE_COMMANDS` (ATW-4, Structural invariants for :data:`STATE_COMMANDS` (ATW-436)., TestStateCommandsInvariant

### Community 80 - "[0.1.0] - Unreleased"
Cohesion: 0.22
Nodes (9): [0.1.0] - Unreleased, Added, Added, Changed, Changelog, Compatibility, Dev, Docs (+1 more)

### Community 81 - "Scheduled captures"
Cohesion: 0.22
Nodes (9): Creating a schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled captures, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 82 - "Scheduled parser-catalog refresh"
Cohesion: 0.22
Nodes (9): Enabling the schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled parser-catalog refresh, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 83 - "FakeCredential"
Cohesion: 0.22
Nodes (4): FakeCredential, A FakeCredential whose get_password/get_enable_secret raise InvalidToken.      S, Duck-typed PyatsCredential (avoids DB/NetBox in unit tests)., _UndecryptableCredential

### Community 85 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 86 - "ADR-0008: Scheduling surface for recurring snapshot capture"
Cohesion: 0.25
Nodes (8): ADR-0008: Scheduling surface for recurring snapshot capture, Alternatives considered, Consequences, Context, Decision, References, Structural shape, Why this fits the locked architecture

### Community 87 - "Graphify"
Cohesion: 0.25
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 88 - "Compliance engine"
Cohesion: 0.25
Nodes (8): Both modes are line-oriented text diff, not Genie-structured diff, Classification, Compliance engine, Engine layer, Related, The diff view, What it does, What the snapshot needs

### Community 89 - "Upgrade guide"
Cohesion: 0.25
Nodes (8): Before you begin, Both at once (NetBox + plugin upgrade), NetBox upgrade (plugin release unchanged), Next steps, Plugin upgrade (NetBox release unchanged), Troubleshooting an upgrade, Upgrade guide, What stays in sync with what

### Community 91 - "DiffTableRenderTest"
Cohesion: 0.36
Nodes (3): DiffTableRenderTest, TestCase, Render ``inc/diff_table.html`` via the snapshot-diff detail view and     assert

### Community 92 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 93 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 94 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 95 - "Graphify MCP"
Cohesion: 0.29
Nodes (7): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, remote / HTTP config (multi-host, opt-in), stdio config (single-host, default), Switching from stdio to HTTP, Tools exposed (both transports), When to use which transport

### Community 96 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 97 - "PULL_REQUEST_TEMPLATE.md"
Cohesion: 0.29
Nodes (6): Changes, Closing checklist, Linked issue, Notes for reviewers, Summary, Verification

### Community 98 - "_validate_device_filter"
Cohesion: 0.29
Nodes (4): Validate ORM keys at save time (ATW-814).          Mirrors the model-level ``cle, Validate ``device_filter`` ORM keys at save time (ATW-814).          Raises ``Va, Validate a ``device_filter`` ORM spec by dry-running it against Device.      Res, _validate_device_filter()

### Community 99 - "TestStateCapture"
Cohesion: 0.29
Nodes (4): kind=state runs device.parse() for each command in STATE_COMMANDS., Per-command ParserNotFound is recorded as a warning, not a failure., CR-3: a non-ParserNotFound parse exception is a real failure, not a         beni, TestStateCapture

### Community 101 - "ADR-0007: Device-page tab via `register_model_view` + `ObjectView`"
Cohesion: 0.33
Nodes (6): ADR-0007: Device-page tab via `register_model_view` + `ObjectView`, Alternatives considered, Consequences, Context, Decision, References

### Community 102 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 103 - "DiffResult"
Cohesion: 0.33
Nodes (4): DiffResult, Outcome of a single :func:`diff_snapshots` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves.

### Community 105 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 106 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 107 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 108 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 113 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 114 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 115 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **289 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-test-entrypoint.sh script`, `DJANGO_SETTINGS_MODULE`, `Migration` (+284 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SnapshotKindChoices` connect `SnapshotKindChoices` to `PyatsJob`, `DiffStatusChoices`, `resolve_panel_platform_support`, `capture_snapshot`, `PyatsCaptureScheduleCleanTest`, `CaptureResult`, `PyatsCredential`, `PyatsSnapshotDiff`, `PyatsSnapshot`, `PyatsSnapshotDiffModelTest`, `test_append_only_list_views.py`, `FakePyatsDevice`, `_EditableListViewsBase`, `DeviceDiffFormKindFilterTest`, `PyatsComplianceRunModelTest`, `jobs.py`, `run_capture_schedules_job`, `PyatsJobModelTest`, `PyatsComplianceRunViewTest`, `PyatsGoldenConfigAPITest`, `FakeOpsInstance`, `resolve_state_commands`, `PyatsComplianceRun`, `test_capture.py`, `DiffTableRenderTest`, `TestStateCapture`, `DeviceBulkCaptureViewTest`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `PyatsParserCatalog` connect `PyatsJob` to `SnapshotKindChoices`, `views.py`, `jobs.py`, `DiffStatusChoices`, `refresh_parser_catalog_for_os`, `ComplianceResultChoices`, `WorkerStatusBadgeViewTest`, `PyatsSnapshotDiff`, `PyatsSnapshot`, `GenieParseViewTest`, `TestWorkerStatusFallback`, `DeviceParseViewTest`, `GenieLearnViewTest`, `get_worker_status`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `PyatsJob`, `SnapshotKindChoices`, `views.py`, `DiffStatusChoices`, `CaptureResult`, `PyatsCredential`, `PyatsSnapshotDiff`, `PyatsSnapshotDiffModelTest`, `run_diff_job`, `test_append_only_list_views.py`, `_EditableListViewsBase`, `DeviceDiffFormKindFilterTest`, `PyatsComplianceRunModelTest`, `jobs.py`, `ComplianceResultChoices`, `PyatsJobModelTest`, `PyatsComplianceRunViewTest`, `GenieDiffViewTest`, `GenieParseViewTest`, `PyatsGoldenConfigAPITest`, `GenieLearnViewTest`, `capture_snapshot_for_netbox_device`, `DiffTableRenderTest`, `DeviceBulkCaptureViewTest`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 165 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshot` has 165 INFERRED edges - model-reasoned connections that need verification._
- **Are the 148 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsJob` has 148 INFERRED edges - model-reasoned connections that need verification._
- **Are the 150 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 150 INFERRED edges - model-reasoned connections that need verification._
- **Are the 143 inferred relationships involving `PyatsCaptureSchedule` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsCaptureSchedule` has 143 INFERRED edges - model-reasoned connections that need verification._