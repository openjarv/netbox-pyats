# Graph Report - .  (2026-08-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2030 nodes · 5363 edges · 167 communities (103 shown, 64 thin omitted)
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 2015 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d589a8ef`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PyatsSnapshotDiff
- SnapshotStatusChoices
- views.py
- resolve_panel_platform_support
- PyatsParserCatalogRefreshSchedule
- run_capture_schedules_job
- capture_snapshot
- PyatsSnapshot
- crypto.py
- _flagged
- test_graphify_scrub_guard.py
- diff_snapshots
- CaptureResult
- build_testbed
- flatten_diff_tree
- PyatsGoldenConfig
- test_capture_learn.py
- test_navmenu_uniqueness_guard.py
- testbed.py
- CatalogRefreshResult
- capture.py
- What You Must Do When Invoked
- test_template_extension.py
- PyatsJob
- test_testbed.py
- DeviceDiffFormKindFilterTest
- jobs.py
- PyatsGoldenConfigAPITest
- refresh_parser_catalog_for_os
- dev-worktree.sh
- diff.py
- Dev environment bring-up
- test_capture.py
- platform_to_pyats_os
- run_diff_job
- Troubleshooting
- run_compliance
- test_pr_body_scrub_guard.py
- extract_snapshot_raw_config
- run_parser_catalog_refresh_schedules_job
- WorkerStatusBadgeViewTest
- ADR-0004: Compliance golden-config comparison shape
- Contributing to netbox-pyats
- Usage guide
- TestCase
- TestSupportedPlatformsMap
- dev-seed.sh
- ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts
- Remote access to the dev NetBox UI over Tailscale
- test_compliance.py
- GenieDiffViewTest
- PyatsSnapshotDiffModelTest
- contributing.md
- PyatsComplianceRunModelTest
- GenieParseViewTest
- _extract_snapshot_raw
- PyatsCredentialModelTest
- get_worker_status
- _resolve_parse_context
- netbox-pyats
- ADR-0002: Multi-vendor graceful degradation pattern
- Graphify MCP HTTP server — multi-host / shared-service runbook
- test_search_index_guard.py
- .get
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- compliance.py
- _mark_running
- DeviceParseViewTest
- TestStateCommandsInvariant
- [0.1.0] - Unreleased
- Scheduled captures
- Scheduled parser-catalog refresh
- GenieLearnViewTest
- TestWorkerStatusFallback
- graphify reference: extra exports and benchmark
- ADR-0008: Scheduling surface for recurring snapshot capture
- Graphify
- Compliance engine
- Upgrade guide
- PyATS worker deployment
- PyatsComplianceRunViewTest
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Graphify MCP
- Installation
- PULL_REQUEST_TEMPLATE.md
- supported_os_values
- FakeOpsClassModule
- TestStateCapture
- TestOrderedModeReorderDrift
- TestEndToEndCompliancePath
- DiffTableRenderTest
- ADR-0007: Device-page tab via `register_model_view` + `ObjectView`
- Architecture Decision Records
- ComplianceResult
- DiffResult
- .__init__
- PyatsGoldenConfigViewTest
- SupportedPlatformsReportViewTest
- PyatsCredentialViewTest
- graphify reference: query, path, explain
- graphify-mcp-key.sh
- netbox-pyats documentation
- RunCaptureSchedulesJob
- __init__.py
- TestSetMode
- pyats-test-entrypoint.sh
- .clean
- TestComplianceResultSizeBytes
- TestFlattenLists
- PyatsParserCatalogRefreshScheduleModelTest
- RunDiffJobDoesNotExistTest
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
- .clean_device_filter
- 0001_initial.py
- 0002_pyatssnapshot.py
- 0003_pyatssnapshotdiff.py
- 0004_reconcile_netboxmodel_fields.py
- 0005_compliance_engine.py
- 0006_compliance_run_nullable_fks.py
- 0007_snapshot_parsed_os.py
- 0008_pyatssnapshotdiff_nullable_fks.py
- 0009_pyatsjob.py
- 0011_pyatscaptureschedule.py
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
- .test_list_view_queryset_uses_select_related_for_result_fks
- extraction-spec.md
- gitleaks-fixture-regression.sh
- test-unit.sh
- netbox-pyats

## God Nodes (most connected - your core abstractions)
1. `PyatsSnapshot` - 206 edges
2. `PyatsJob` - 191 edges
3. `PyatsSnapshotDiff` - 183 edges
4. `PyatsComplianceRun` - 166 edges
5. `PyatsCredential` - 163 edges
6. `PyatsCaptureSchedule` - 161 edges
7. `PyatsGoldenConfig` - 160 edges
8. `SnapshotKindChoices` - 151 edges
9. `PyatsParserCatalogRefreshSchedule` - 145 edges
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

## Communities (167 total, 64 thin omitted)

### Community 0 - "PyatsSnapshotDiff"
Cohesion: 0.07
Nodes (101): Meta, What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotKindChoices, SnapshotTriggerChoices, Meta, PyatsCaptureSchedule, PyatsComplianceRun (+93 more)

### Community 1 - "SnapshotStatusChoices"
Cohesion: 0.09
Nodes (72): ComplianceModeChoices, ComplianceResultChoices, CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices (+64 more)

### Community 2 - "views.py"
Cohesion: 0.11
Nodes (61): PyatsCaptureScheduleSerializer, PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsParserCatalogRefreshScheduleSerializer, PyatsParserCatalogSerializer, PyatsSnapshotDiffSerializer (+53 more)

### Community 3 - "resolve_panel_platform_support"
Cohesion: 0.07
Nodes (27): Platform-support decision for the device-page PyATS panel (ATW-184).  Pure-Pytho, Return ``(platform_supported, os_value)`` for the device-page panel.      Combin, resolve_panel_platform_support(), group_snapshots_by_kind(), Pure-Python helpers for the device-page PyATS tab (ATW-393, ADR-0007).  This mod, Group snapshots by ``kind`` for the diff picker (ATW-241 child 4).      Returns, FakeSnapshot, QA-independent verification for the ATW-252 diff picker kind filter.  Written by (+19 more)

### Community 4 - "PyatsParserCatalogRefreshSchedule"
Cohesion: 0.09
Nodes (36): Meta, PyatsCaptureScheduleType, PyatsCredentialType, PyatsJobType, PyatsParserCatalogRefreshScheduleType, PyatsParserCatalogType, PyatsSnapshotDiffType, PyatsSnapshotType (+28 more)

### Community 5 - "run_capture_schedules_job"
Cohesion: 0.08
Nodes (16): RQ worker entry point — dispatch captures for all enabled schedules.      Thin m, Dispatch captures for all enabled schedules (delegates to the wrapper)., run_capture_schedules_job(), Re-resolve :attr:`device_filter` to a Device queryset (run-time).          Thin, Re-resolve a ``device_filter`` JSON spec to a Device queryset at run time., _resolve_device_filter(), TestCase, PyatsCaptureScheduleCleanTest (+8 more)

### Community 6 - "capture_snapshot"
Cohesion: 0.12
Nodes (11): capture_snapshot(), Capture a snapshot from a single, already-connected pyATS Device.      This is t, FakePyatsDevice, kind='parse' runs device.parse() per user-supplied command and writes     the sa, Duck-typed pyATS Device for capture tests.      Only the attributes/methods :fun, ATW-432: capture_snapshot with kind='state' uses the per-OS command     set when, TestBadKind, TestConfigCapture (+3 more)

### Community 7 - "PyatsSnapshot"
Cohesion: 0.09
Nodes (23): PyatsSnapshot, One captured config/state/full snapshot for a NetBox Device.      Populated by t, PyatsCaptureScheduleIndex, PyatsComplianceRunIndex, PyatsCredentialIndex, PyatsGoldenConfigIndex, PyatsJobIndex, PyatsParserCatalogIndex (+15 more)

### Community 8 - "crypto.py"
Cohesion: 0.08
Nodes (22): CredentialDecryptError, decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), is_encrypted_token(), Exception (+14 more)

### Community 9 - "_flagged"
Cohesion: 0.10
Nodes (9): _flagged(), Regression test for the ATW-116 secret/PII detection allowlist/regex.  Validates, ATW-167 root-cause regression: a real-shaped value placed in the     fixture fil, Return list of (rule_id, matched_segment) the gitleaks rules would flag., Concrete leaks that MUST be flagged (the ATW-114 regression set)., Placeholder / RFC1918 / loopback forms that MUST NOT be flagged., SecretDetectionATW167Regression, SecretDetectionNegativeCases (+1 more)

### Community 10 - "test_graphify_scrub_guard.py"
Cohesion: 0.13
Nodes (31): CompletedProcess, extended_repo(), _make_extended_tree(), _make_tree(), Tests for scripts/graphify-scrub-guard.sh.  The scrub guard is the structural ba, Build a tree with cache/, a dated backup dir, and .graphify_* state., A tree with clean cache/dated/state files must pass the guard., A leak in cache/stat-index.json must be caught (ATW-307 regression class). (+23 more)

### Community 11 - "diff_snapshots"
Cohesion: 0.10
Nodes (12): diff_snapshots(), Diff two serialized snapshot payloads and return a structured result.      Args:, Tests for :mod:`netbox_pyats.diff`.  Pure-Python: exercises the structured diff, The whole diff tree must round-trip through json.dumps (it's JSONB)., Diff two Genie-parser-shaped snapshot payloads end-to-end., TestAddedRemovedChanged, TestDiffResultSizeBytes, TestEmptyAndError (+4 more)

### Community 12 - "CaptureResult"
Cohesion: 0.11
Nodes (10): CaptureResult, Outcome of a single :func:`capture_snapshot` call.      The :class:`~netbox_pyat, Length of the JSON-serialized ``data`` payload, in bytes., TestCaptureResultSizeBytes, BatchCaptureJobTest, CaptureJobPyatsJobPlumbingTest, ParseJobPyatsJobPlumbingTest, ADR-0005 §3 plumbing for ``capture_snapshot_job`` (Phase 5, ATW-16). (+2 more)

### Community 13 - "build_testbed"
Cohesion: 0.17
Nodes (12): build_testbed(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, _cred_resolver_factory(), _fake_testbed_factory(), FakeCredential, FakeDevice, Return a credential_resolver that always returns ``cred`` (or None)., Return a ``_pyats_testbed_cls`` callable: a function returning a raising class. (+4 more)

### Community 14 - "flatten_diff_tree"
Cohesion: 0.13
Nodes (10): DiffLine, flatten_diff_tree(), One flat row in a side-by-side diff table (ATW-524/ATW-525).      A flattened vi, Flatten a structured diff tree into a list of side-by-side table rows.      Walk, Unit tests for :func:`netbox_pyats.diff.flatten_diff_tree` (ATW-524/ATW-525).  P, TestFlattenEmptyAndError, TestFlattenLeaves, TestFlattenNestedContainerLeafValues (+2 more)

### Community 15 - "PyatsGoldenConfig"
Cohesion: 0.09
Nodes (13): PyatsGoldenConfig, A golden / reference running-config for a NetBox Device (Phase 4, ATW-15)., _AppendOnlyListViewsBase, PyatsComplianceRunListViewRenderTest, PyatsSnapshotDiffListViewRenderTest, PyatsSnapshotListViewRenderTest, ``/plugins/pyats/diffs/`` must render 200 (ATW-183 regression)., ``/plugins/pyats/compliance-runs/`` must render 200 (ATW-183 regression). (+5 more)

### Community 16 - "test_capture_learn.py"
Cohesion: 0.15
Nodes (15): FakeLookup, _FakeModuleInfo, FakeOpsFactory, FakeOpsNamespace, FakePyatsDevice, _patch_genie_ops(), Tests for the Genie Ops Learn capture (ATW-730).  Pure-Python: exercises :func:`, Duck-typed ``pkgutil.ModuleInfo`` for ``pkgutil.iter_modules``. (+7 more)

### Community 17 - "test_navmenu_uniqueness_guard.py"
Cohesion: 0.10
Nodes (19): _extract_menu_item_kwargs(), _extract_menu_links(), _extract_model_classes(), _extract_schema_type_models(), GraphQLSchemaCompletenessGuard, _is_menu_var(), NavMenuUniquenessGuard, Hardening guard for the navigation menu and GraphQL schema surface.  These tests (+11 more)

### Community 18 - "testbed.py"
Cohesion: 0.09
Nodes (20): _build_device_entry(), _device_display_name(), _iter_devices(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), _pyats_testbed_cls(), NetBox → pyATS testbed bridge.  :func:`build_testbed` constructs a :class:`pyats (+12 more)

### Community 19 - "CatalogRefreshResult"
Cohesion: 0.13
Nodes (12): CatalogRefreshResult, Parser-catalog refresh core — the Genie work, isolated from NetBox/RQ.  :func:`r, Outcome of a single :func:`refresh_parser_catalog_for_os` call.      The :func:`, TestCase, PyatsParserCatalogModelTest, PyatsParserCatalogSearchIndexTest, Tests for :class:`netbox_pyats.models.PyatsParserCatalog` (ATW-241 child 1, ATW-, Patch the pure-Python helper to return canned results per os.          ``results (+4 more)

### Community 20 - "capture.py"
Cohesion: 0.09
Nodes (20): _capture_config(), _capture_learn(), _capture_parse(), capture_snapshot_for_netbox_device(), _capture_state(), _discover_ops_features(), _get_plugin_config(), Any (+12 more)

### Community 21 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 22 - "test_template_extension.py"
Cohesion: 0.09
Nodes (21): Module, Structural guard for the device-page PyATS tab registration (ATW-393 / ADR-0007), ATW-409 regression guard: DevicePyATSTabView.get_extra_context must     include, ADR-0007: the PluginTemplateExtension module is deleted., DevicePyATSTabView must be decorated with register_model_view(Device, 'pyats')., DevicePyATSTabView must subclass generic.ObjectView., DevicePyATSTabView must declare a ViewTab with label='PyATS'., ADR-0007: __init__.py must not register template_extensions. (+13 more)

### Community 23 - "PyatsJob"
Cohesion: 0.12
Nodes (8): PyatsJob, One plugin job-tracking row across capture / diff / compliance / batch (Phase 5,, PyatsJobListViewRenderTest, ``/plugins/pyats/jobs/`` must render 200 (ATW-183 regression)., DiffJobPyatsJobPlumbingTest, PyatsJobModelTest, ADR-0005 §3 plumbing for ``run_diff_job`` (Phase 5, ATW-16)., Persistence + helpers for PyatsJob (Phase 5, ATW-16).

### Community 24 - "test_testbed.py"
Cohesion: 0.10
Nodes (13): is_supported_os(), True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)., DuplicateDeviceError, FakeDeviceType, FakeIPAddress, Exception, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS, A FakeCredential whose get_password/get_enable_secret raise InvalidToken.      S (+5 more)

### Community 25 - "DeviceDiffFormKindFilterTest"
Cohesion: 0.16
Nodes (7): DeviceDiffFormKindFilterTest, DeviceDiffViewKindFilterTest, _make_snapshot(), Tests for the ``DeviceDiffForm`` kind filter (ATW-241 child 4 / ATW-252).  NetBo, The ``device_diff`` view surfaces the kind filter as a redirect+flash., Create a minimal PyatsSnapshot row of the given kind for ``device``., Form-level kind-filter enforcement (ATW-241 child 4).

### Community 26 - "jobs.py"
Cohesion: 0.13
Nodes (21): batch_capture_job(), capture_snapshot_job(), _create_pyats_job(), enqueue_batch_capture(), enqueue_capture(), enqueue_compliance(), enqueue_diff(), _finish_partial() (+13 more)

### Community 27 - "PyatsGoldenConfigAPITest"
Cohesion: 0.10
Nodes (4): APITestCase, PyatsCredentialAPITest, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest

### Community 28 - "refresh_parser_catalog_for_os"
Cohesion: 0.17
Nodes (10): Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a minimal ``pyats.topology.Device`` with only ``.os`` set.      ``genie.li, Discover the parseable command list for one pyATS os.      Worker-only: lazily i, refresh_parser_catalog_for_os(), _stub_pyats_device(), _worker_versions(), Tests for :mod:`netbox_pyats.parser_catalog` (ATW-241 child 1, ATW-249).  Pure-P, Exercise :func:`refresh_parser_catalog_for_os` with a stubbed genie import. (+2 more)

### Community 29 - "dev-worktree.sh"
Cohesion: 0.19
Nodes (12): cmd_add(), cmd_audit(), cmd_cleanup(), cmd_remove(), cmd_test(), cmd_up(), die(), enforce_concurrency_cap() (+4 more)

### Community 30 - "diff.py"
Cohesion: 0.18
Nodes (18): Any, _diff_dict(), _diff_list(), _diff_value(), _flatten_node(), _join_path(), _leaf_type(), _node_status() (+10 more)

### Community 31 - "Dev environment bring-up"
Cohesion: 0.11
Nodes (19): Base branch policy (ATW-208), Bring-up, Cost model — per-worktree dev time, Dev environment bring-up, Image overrides (compatibility sweeps), Integration lane (Docker + NetBox), Keeping the split clean, Prerequisites (+11 more)

### Community 32 - "test_capture.py"
Cohesion: 0.13
Nodes (10): Exception, Return the state-capture command list for a given pyATS ``os``.      Resolution, resolve_state_commands(), ParserNotFound, Tests for :mod:`netbox_pyats.capture`.  Pure-Python: exercises the snapshot capt, Duck-type stand-in for ``genie.libs.parser.utils.common.ParserNotFound``.      T, ATW-432: resolve_state_commands picks per-OS command sets from     PLUGINS_CONFI, TestCaptureError (+2 more)

### Community 33 - "platform_to_pyats_os"
Cohesion: 0.22
Nodes (5): platform_to_pyats_os(), Map a NetBox ``Platform`` to a pyATS ``os`` string.      Returns the :data:`UNSU, FakeManufacturer, FakePlatform, TestPlatformToOs

### Community 34 - "run_diff_job"
Cohesion: 0.17
Nodes (17): BaseException, enqueue_learn(), _finish_success(), learn_snapshot_job(), _persist_error_row(), _persist_input_error_row(), Enqueue a Genie Ops Learn job on the dedicated ``pyats`` RQ queue (ATW-730)., Set a :class:`PyatsJob` to ``success`` with the result-row FK and ``finished_at= (+9 more)

### Community 35 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 36 - "run_compliance"
Cohesion: 0.20
Nodes (4): Compare a golden config text against a snapshot's raw config text and classify., run_compliance(), TestDrift, TestErrorInputs

### Community 37 - "test_pr_body_scrub_guard.py"
Cohesion: 0.18
Nodes (16): Tests for scripts/pr-body-scrub-guard.sh.  The PR body scrub guard is the struct, Role words in normal prose (not on a reviewer/merger line) are fine., An 8-char commit short-SHA must NOT trip the agent-prefix pattern., PR #44/#45 form: `[@CTO](agent://<uuid>)`., A bare RFC-4122 UUID anywhere in the body is caught., PR #47 form: `reviewer: @CTO (agent <prefix>)`., The exact PR #47 leaked line — prefix + role, caught by the prefix., _run() (+8 more)

### Community 39 - "extract_snapshot_raw_config"
Cohesion: 0.21
Nodes (5): extract_snapshot_raw_config(), Extract the snapshot's raw running-config text (the compliance "actual").      v, Regression test for the compliance job's legacy ``config[raw]`` fallback (ATW-43, Pin the contract of :func:`extract_snapshot_raw_config` (ATW-437)., TestExtractSnapshotRawConfig

### Community 40 - "run_parser_catalog_refresh_schedules_job"
Cohesion: 0.20
Nodes (8): RQ worker entry point — refresh the parser catalog when the schedule is enabled., Dispatch a parser catalog refresh when the schedule is enabled.          ``JobRu, run_parser_catalog_refresh_schedules_job(), Tests for the PyatsParserCatalogRefreshSchedule model + dispatcher (ATW-581).  R, Recurring enabled run → next_run_at = last_run_at + interval (ATW-610)., Recurring disabled-skip → next_run_at still set from interval (ATW-610)., run_parser_catalog_refresh_schedules_job dispatch logic (ATW-581)., RunParserCatalogRefreshSchedulesJobTest

### Community 41 - "WorkerStatusBadgeViewTest"
Cohesion: 0.12
Nodes (3): TestCase, The six worker-using views must render the worker status badge (ATW-804).      `, WorkerStatusBadgeViewTest

### Community 42 - "ADR-0004: Compliance golden-config comparison shape"
Cohesion: 0.13
Nodes (15): Acceptance, ADR-0004: Compliance golden-config comparison shape, Capture change, Consequences, Consequences, Considered options, Considered options for v2, Context (+7 more)

### Community 43 - "Contributing to netbox-pyats"
Cohesion: 0.13
Nodes (15): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+7 more)

### Community 44 - "Usage guide"
Cohesion: 0.14
Nodes (14): 1 — Add a credential, 2 — Capture a snapshot, 3 — Run an on-demand Parse, 4 — Run a Genie Learn capture, 5 — Diff two snapshots, 6 — Add a golden config, 7 — Run compliance, 8 — Browse everything (+6 more)

### Community 45 - "TestCase"
Cohesion: 0.15
Nodes (6): DeviceParseFormTest, DeviceRefreshCatalogViewTest, Tests for the device-page Parse sub-tab (ATW-241 child 2, ATW-250).  Requires a, View tests for :class:`views.DeviceRefreshCatalogView` (ATW-250)., Pure-form validation for :class:`forms.DeviceParseForm`., TestCase

### Community 46 - "TestSupportedPlatformsMap"
Cohesion: 0.14
Nodes (5): Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, The static map the report renders (Phase 5, ATW-16, Option A)., ADR-0001 §6: the data path the report view reads must not import Genie.      The, TestSupportedPlatformsMap, TestSupportedPlatformsReportWebProcessSafety

### Community 47 - "dev-seed.sh"
Cohesion: 0.27
Nodes (10): cmd_build(), cmd_force_restore(), cmd_info(), cmd_remove(), cmd_restore(), die(), _restore(), dev-seed.sh script (+2 more)

### Community 48 - "ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts"
Cohesion: 0.15
Nodes (13): 1. PR bodies use role-only labels — no identifiers (hard rule), 2. `[@Agent](agent://<id>)` is internal-only, 3. Boundary rule: public artifact vs internal comment, 4. Merger verifies before merge, 5. Retroactive redaction is harm-reduction, not elimination, ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts, Alternatives considered, Blast radius (+5 more)

### Community 49 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 50 - "test_compliance.py"
Cohesion: 0.15
Nodes (6): Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15; v2 ATW-434).  Pure-Py, The ordered diff can emit the same line text at multiple positions     (e.g. two, TestCompliant, TestDuplicateLines, TestJsonSerializable, TestUnknownModeDegradesToOrdered

### Community 51 - "GenieDiffViewTest"
Cohesion: 0.15
Nodes (3): GenieDiffViewTest, TestCase, View tests for :class:`views.GenieDiffView` (ATW-731).

### Community 52 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.22
Nodes (3): PyatsSnapshotDiffModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Regression for ATW-68: a diff error row with before/after NULL must         roun

### Community 56 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 57 - "PyatsCredentialModelTest"
Cohesion: 0.17
Nodes (3): TestCase, PyatsCredentialModelTest, Field-level encryption and validation behavior of PyatsCredential.

### Community 58 - "get_worker_status"
Cohesion: 0.21
Nodes (8): Tests for the worker status indicator (ATW-804).  Two lanes, matching the repo's, _check_worker_status(), _get_cache(), get_worker_status(), Worker status helper for the pyATS RQ queue (ATW-804).  A pure-Python, resilient, Return the Django cache backend or ``None`` when unavailable.      Pure-Python m, Return ``(online, reason)`` for the dedicated ``pyats`` RQ queue.      ``online=, Run the actual RQ/Redis worker check (uncached).      Kept separate from :func:`

### Community 59 - "_resolve_parse_context"
Cohesion: 0.21
Nodes (4): Resolve the pyATS os + catalog row + command choices for a device.      Web-proc, Return the POST URL for the device-page "Refresh parser list" button., _refresh_parser_catalog_url_for_device(), _resolve_parse_context()

### Community 60 - "netbox-pyats"
Cohesion: 0.17
Nodes (12): At a glance, Capture, Compare, Compatibility matrix, Compliance & Jobs, Device-page UI, Documentation, Getting help (+4 more)

### Community 61 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 62 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.18
Nodes (11): Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites, Remote agent wiring (Senior Dev Engineer), Secret rotation (+3 more)

### Community 63 - "test_search_index_guard.py"
Cohesion: 0.24
Nodes (8): _extract_netbox_model_subclasses(), _extract_search_index_models(), Search-index completeness guard (ATW-816).  AST-only guard asserting every NetBo, Return NetBoxModel subclass names from models.py (AST)., Return model names registered in search.py (AST).      Collects ``model = <Name>, Every NetBoxModel subclass must have a SearchIndex unless excluded., Excluded models must still exist in models.py (no stale exclusion)., SearchIndexCompletenessGuard

### Community 64 - ".get"
Cohesion: 0.18
Nodes (5): _diff_list_url(), _genie_diff_post_url(), Return the most recent snapshots for a device (or empty list)., Return the POST URL for the Genie Diff page diff form., Return the full diff history list URL (pyatssnapshotdiff_list).

### Community 65 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 66 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 67 - "compliance.py"
Cohesion: 0.24
Nodes (9): _build_tree(), _normalize_lines(), _ordered_diff(), Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Normalize a running-config text into a list of comparable lines.      Drops blan, Build the JSON-serializable diff tree and summary from leaf lists.      The tree, v2 ordered (sequence-aware) diff via :mod:`difflib`.      Walks :func:`difflib.S, v1 set (order-independent) diff.      Compares the two line lists as sets and re (+1 more)

### Community 68 - "_mark_running"
Cohesion: 0.20
Nodes (10): enqueue_parse(), enqueue_refresh_parser_catalog(), _mark_running(), parse_commands_job(), Enqueue an on-demand parse job on the dedicated ``pyats`` RQ queue.      This is, Set a :class:`PyatsJob` to ``running`` with ``started_at=now()``.      Called at, Enqueue a parser-catalog refresh job on the dedicated ``pyats`` RQ queue.      T, RQ worker entry point — run on-demand parses and persist the snapshot.      NetB (+2 more)

### Community 70 - "TestStateCommandsInvariant"
Cohesion: 0.20
Nodes (3): Hardening invariant guard for :data:`netbox_pyats.capture.STATE_COMMANDS` (ATW-4, Structural invariants for :data:`STATE_COMMANDS` (ATW-436)., TestStateCommandsInvariant

### Community 71 - "[0.1.0] - Unreleased"
Cohesion: 0.22
Nodes (9): [0.1.0] - Unreleased, Added, Added, Changed, Changelog, Compatibility, Dev, Docs (+1 more)

### Community 72 - "Scheduled captures"
Cohesion: 0.22
Nodes (9): Creating a schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled captures, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 73 - "Scheduled parser-catalog refresh"
Cohesion: 0.22
Nodes (9): Enabling the schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled parser-catalog refresh, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 76 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 77 - "ADR-0008: Scheduling surface for recurring snapshot capture"
Cohesion: 0.25
Nodes (8): ADR-0008: Scheduling surface for recurring snapshot capture, Alternatives considered, Consequences, Context, Decision, References, Structural shape, Why this fits the locked architecture

### Community 78 - "Graphify"
Cohesion: 0.25
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 79 - "Compliance engine"
Cohesion: 0.25
Nodes (8): Both modes are line-oriented text diff, not Genie-structured diff, Classification, Compliance engine, Engine layer, Related, The diff view, What it does, What the snapshot needs

### Community 80 - "Upgrade guide"
Cohesion: 0.25
Nodes (8): Before you begin, Both at once (NetBox + plugin upgrade), NetBox upgrade (plugin release unchanged), Next steps, Plugin upgrade (NetBox release unchanged), Troubleshooting an upgrade, Upgrade guide, What stays in sync with what

### Community 81 - "PyATS worker deployment"
Cohesion: 0.25
Nodes (8): Option A — install pyats into your own worker, Option B — the shipped worker image (reference / dev), PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, What runs on the `pyats` queue, Why a separate queue

### Community 83 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 84 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 85 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 86 - "Graphify MCP"
Cohesion: 0.29
Nodes (7): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, remote / HTTP config (multi-host, opt-in), stdio config (single-host, default), Switching from stdio to HTTP, Tools exposed (both transports), When to use which transport

### Community 87 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 88 - "PULL_REQUEST_TEMPLATE.md"
Cohesion: 0.29
Nodes (6): Changes, Closing checklist, Linked issue, Notes for reviewers, Summary, Verification

### Community 89 - "supported_os_values"
Cohesion: 0.38
Nodes (4): Return the deduplicated set of Genie-supported pyATS os strings.      Derived fr, supported_os_values(), Exercise :func:`supported_os_values` — the deduplicated supported os set., TestSupportedOsValues

### Community 90 - "FakeOpsClassModule"
Cohesion: 0.29
Nodes (4): FakeOpsClassModule, FakeOpsFeatureModule, Duck-typed 2nd-level ``lookup.ops.<feature>.<feature>`` module.      Exposes the, Duck-typed 1st-level ``lookup.ops.<feature>`` AbstractedModule.      Exposes the

### Community 91 - "TestStateCapture"
Cohesion: 0.29
Nodes (4): kind=state runs device.parse() for each command in STATE_COMMANDS., Per-command ParserNotFound is recorded as a warning, not a failure., CR-3: a non-ParserNotFound parse exception is a real failure, not a         beni, TestStateCapture

### Community 95 - "ADR-0007: Device-page tab via `register_model_view` + `ObjectView`"
Cohesion: 0.33
Nodes (6): ADR-0007: Device-page tab via `register_model_view` + `ObjectView`, Alternatives considered, Consequences, Context, Decision, References

### Community 96 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 97 - "ComplianceResult"
Cohesion: 0.33
Nodes (4): ComplianceResult, Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift).

### Community 98 - "DiffResult"
Cohesion: 0.33
Nodes (4): DiffResult, Outcome of a single :func:`diff_snapshots` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves.

### Community 103 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 104 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 105 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 106 - "RunCaptureSchedulesJob"
Cohesion: 0.40
Nodes (5): JobRunner, Recurring dispatcher for capture schedules (ATW-433, ADR-0008).      A registere, Recurring dispatcher for the parser catalog refresh (ATW-581).      A registered, RunCaptureSchedulesJob, RunParserCatalogRefreshSchedulesJob

### Community 107 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 115 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 116 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 117 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **286 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-test-entrypoint.sh script`, `DJANGO_SETTINGS_MODULE`, `Migration` (+281 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **64 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SnapshotKindChoices` connect `PyatsSnapshotDiff` to `SnapshotStatusChoices`, `resolve_panel_platform_support`, `PyatsParserCatalogRefreshSchedule`, `run_capture_schedules_job`, `capture_snapshot`, `PyatsSnapshot`, `CaptureResult`, `PyatsGoldenConfig`, `test_capture_learn.py`, `capture.py`, `PyatsJob`, `DeviceDiffFormKindFilterTest`, `jobs.py`, `PyatsGoldenConfigAPITest`, `test_capture.py`, `PyatsSnapshotDiffModelTest`, `PyatsComplianceRunModelTest`, `PyatsComplianceRunViewTest`, `FakeOpsClassModule`, `TestStateCapture`, `DiffTableRenderTest`, `PyatsGoldenConfigViewTest`, `RunCaptureSchedulesJob`, `RunDiffJobDoesNotExistTest`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `PyatsParserCatalog` connect `PyatsSnapshotDiff` to `SnapshotStatusChoices`, `views.py`, `PyatsParserCatalogRefreshSchedule`, `DeviceParseViewTest`, `get_worker_status`, `PyatsSnapshot`, `WorkerStatusBadgeViewTest`, `RunCaptureSchedulesJob`, `GenieLearnViewTest`, `TestWorkerStatusFallback`, `TestCase`, `CatalogRefreshResult`, `GenieParseViewTest`, `jobs.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `PyatsSnapshotDiff`, `SnapshotStatusChoices`, `views.py`, `PyatsParserCatalogRefreshSchedule`, `CaptureResult`, `PyatsGoldenConfig`, `PyatsJob`, `.get_status_color`, `.has_warnings`, `DeviceDiffFormKindFilterTest`, `jobs.py`, `PyatsGoldenConfigAPITest`, `run_diff_job`, `GenieDiffViewTest`, `PyatsSnapshotDiffModelTest`, `PyatsComplianceRunModelTest`, `GenieParseViewTest`, `_mark_running`, `GenieLearnViewTest`, `PyatsComplianceRunViewTest`, `DiffTableRenderTest`, `PyatsGoldenConfigViewTest`, `RunCaptureSchedulesJob`, `RunDiffJobDoesNotExistTest`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 160 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshot` has 160 INFERRED edges - model-reasoned connections that need verification._
- **Are the 148 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsJob` has 148 INFERRED edges - model-reasoned connections that need verification._
- **Are the 150 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 150 INFERRED edges - model-reasoned connections that need verification._
- **Are the 137 inferred relationships involving `PyatsComplianceRun` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsComplianceRun` has 137 INFERRED edges - model-reasoned connections that need verification._