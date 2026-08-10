# Graph Report - .  (2026-08-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1933 nodes · 5132 edges · 143 communities (99 shown, 44 thin omitted)
- Extraction: 62% EXTRACTED · 38% INFERRED · 0% AMBIGUOUS · INFERRED: 1948 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `de211150`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PyatsSnapshotDiff
- SnapshotStatusChoices
- views.py
- ComplianceModeChoices
- refresh_parser_catalog_for_os
- PyatsJob
- resolve_panel_platform_support
- capture_snapshot
- _flagged
- diff_snapshots
- test_graphify_scrub_guard.py
- capture.py
- CaptureResult
- PyatsCredential
- run_capture_schedules_job
- PyatsSnapshot
- flatten_diff_tree
- test_capture_learn.py
- build_testbed
- test_navmenu_uniqueness_guard.py
- testbed.py
- What You Must Do When Invoked
- run_diff_job
- test_template_extension.py
- run_parser_catalog_refresh_schedules_job
- PyatsSnapshotDiffModelTest
- DeviceParseViewTest
- DeviceDiffFormKindFilterTest
- PyatsComplianceRunModelTest
- PyatsJobModelTest
- dev-worktree.sh
- Dev environment bring-up
- diff.py
- EncryptDecryptTest
- Graphify MCP HTTP server — multi-host / shared-service runbook
- crypto.py
- jobs.py
- test_testbed.py
- test_pr_body_scrub_guard.py
- Troubleshooting
- .get
- compliance.py
- extract_snapshot_raw_config
- ADR-0004: Compliance golden-config comparison shape
- Contributing to netbox-pyats
- platform_to_pyats_os
- PyatsComplianceRunViewTest
- GenieParseViewTest
- PyatsCredentialForm
- dev-seed.sh
- ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts
- Remote access to the dev NetBox UI over Tailscale
- Usage guide
- PyatsGoldenConfigAPITest
- test_supported_platforms.py
- contributing.md
- GenieLearnViewTest
- _extract_snapshot_raw
- TestSupportedPlatformsMap
- netbox-pyats
- ADR-0002: Multi-vendor graceful degradation pattern
- FakeOpsInstance
- PyatsCredentialModelTest
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension
- TestStateCommandsInvariant
- [0.1.0] - Unreleased
- Scheduled captures
- Scheduled parser-catalog refresh
- graphify reference: extra exports and benchmark
- ADR-0008: Scheduling surface for recurring snapshot capture
- Graphify
- Compliance engine
- Upgrade guide
- PyATS worker deployment
- PyatsCredentialAPITest
- DiffTableRenderTest
- conftest.py
- ADR-0001: Plugin package layout
- CI
- Installation
- PULL_REQUEST_TEMPLATE.md
- __init__.py
- TestStateCapture
- PyatsCredentialViewTest
- ADR-0007: Device-page tab via `register_model_view` + `ObjectView`
- Architecture Decision Records
- DiffResult
- batch_capture_job
- graphify reference: query, path, explain
- graphify-mcp-key.sh
- netbox-pyats documentation
- pyats-test-entrypoint.sh
- test_panel.py
- TestFlattenLists
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
- .is_from_snapshot
- .get_status_color
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
1. `PyatsSnapshot` - 201 edges
2. `PyatsJob` - 187 edges
3. `PyatsSnapshotDiff` - 178 edges
4. `PyatsComplianceRun` - 163 edges
5. `PyatsCredential` - 159 edges
6. `PyatsGoldenConfig` - 157 edges
7. `PyatsCaptureSchedule` - 155 edges
8. `SnapshotKindChoices` - 145 edges
9. `PyatsParserCatalogRefreshSchedule` - 143 edges
10. `PyatsParserCatalog` - 123 edges

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

## Communities (143 total, 44 thin omitted)

### Community 0 - "PyatsSnapshotDiff"
Cohesion: 0.07
Nodes (103): JobRunner, What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotKindChoices, SnapshotTriggerChoices, Meta, Recurring dispatcher for capture schedules (ATW-433, ADR-0008).      A registere, Recurring dispatcher for the parser catalog refresh (ATW-581).      A registered (+95 more)

### Community 1 - "SnapshotStatusChoices"
Cohesion: 0.10
Nodes (63): ComplianceResultChoices, CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, GoldenConfigSourceChoices, PyatsJobStatusChoices, PyatsJobTypeChoices, Choice sets for the netbox-pyats plugin. (+55 more)

### Community 2 - "views.py"
Cohesion: 0.14
Nodes (57): PyatsCaptureScheduleSerializer, PyatsComplianceRunSerializer, PyatsCredentialSerializer, PyatsGoldenConfigSerializer, PyatsJobSerializer, PyatsParserCatalogRefreshScheduleSerializer, PyatsParserCatalogSerializer, PyatsSnapshotDiffSerializer (+49 more)

### Community 3 - "ComplianceModeChoices"
Cohesion: 0.07
Nodes (19): ComplianceModeChoices, How :func:`netbox_pyats.compliance.run_compliance` compares configs.      ``orde, Compare a golden config text against a snapshot's raw config text and classify., run_compliance(), Tests for :mod:`netbox_pyats.compliance` (Phase 4, ATW-15; v2 ATW-434).  Pure-Py, ATW-434: the v2 ordered (default) diff flags re-ordered lines as drift.      Thi, v1 set (order-independent) diff, retained as an explicit opt-in.      A re-order, The ordered diff can emit the same line text at multiple positions     (e.g. two (+11 more)

### Community 4 - "refresh_parser_catalog_for_os"
Cohesion: 0.08
Nodes (23): CatalogRefreshResult, Parser-catalog refresh core — the Genie work, isolated from NetBox/RQ.  :func:`r, Return the deduplicated set of Genie-supported pyATS os strings.      Derived fr, Outcome of a single :func:`refresh_parser_catalog_for_os` call.      The :func:`, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Build a minimal ``pyats.topology.Device`` with only ``.os`` set.      ``genie.li, Discover the parseable command list for one pyATS os.      Worker-only: lazily i, refresh_parser_catalog_for_os() (+15 more)

### Community 5 - "PyatsJob"
Cohesion: 0.09
Nodes (38): Meta, PyatsGoldenConfig, PyatsJob, A golden / reference running-config for a NetBox Device (Phase 4, ATW-15)., One plugin job-tracking row across capture / diff / compliance / batch (Phase 5,, The result row this job produced, regardless of type, or None.          Convenie, PyatsCaptureScheduleIndex, PyatsComplianceRunIndex (+30 more)

### Community 6 - "resolve_panel_platform_support"
Cohesion: 0.08
Nodes (25): Return ``(platform_supported, os_value)`` for the device-page panel.      Combin, resolve_panel_platform_support(), group_snapshots_by_kind(), Pure-Python helpers for the device-page PyATS tab (ATW-393, ADR-0007).  This mod, Group snapshots by ``kind`` for the diff picker (ATW-241 child 4).      Returns, FakeSnapshot, QA-independent verification for the ATW-252 diff picker kind filter.  Written by, Render the device-tab diff-picker partial and assert the ATW-252     contract: o (+17 more)

### Community 7 - "capture_snapshot"
Cohesion: 0.11
Nodes (12): capture_snapshot(), Capture a snapshot from a single, already-connected pyATS Device.      This is t, FakePyatsDevice, kind='parse' runs device.parse() per user-supplied command and writes     the sa, Duck-typed pyATS Device for capture tests.      Only the attributes/methods :fun, ATW-432: capture_snapshot with kind='state' uses the per-OS command     set when, TestBadKind, TestConfigCapture (+4 more)

### Community 8 - "_flagged"
Cohesion: 0.10
Nodes (9): _flagged(), Regression test for the ATW-116 secret/PII detection allowlist/regex.  Validates, ATW-167 root-cause regression: a real-shaped value placed in the     fixture fil, Return list of (rule_id, matched_segment) the gitleaks rules would flag., Concrete leaks that MUST be flagged (the ATW-114 regression set)., Placeholder / RFC1918 / loopback forms that MUST NOT be flagged., SecretDetectionATW167Regression, SecretDetectionNegativeCases (+1 more)

### Community 9 - "diff_snapshots"
Cohesion: 0.10
Nodes (12): diff_snapshots(), Diff two serialized snapshot payloads and return a structured result.      Args:, Tests for :mod:`netbox_pyats.diff`.  Pure-Python: exercises the structured diff, The whole diff tree must round-trip through json.dumps (it's JSONB)., Diff two Genie-parser-shaped snapshot payloads end-to-end., TestAddedRemovedChanged, TestDiffResultSizeBytes, TestEmptyAndError (+4 more)

### Community 10 - "test_graphify_scrub_guard.py"
Cohesion: 0.13
Nodes (31): extended_repo(), _make_extended_tree(), _make_tree(), CompletedProcess, Path, Tests for scripts/graphify-scrub-guard.sh.  The scrub guard is the structural ba, Build a tree with cache/, a dated backup dir, and .graphify_* state., A tree with clean cache/dated/state files must pass the guard. (+23 more)

### Community 11 - "capture.py"
Cohesion: 0.08
Nodes (22): _capture_config(), _capture_parse(), capture_snapshot_for_netbox_device(), _capture_state(), _get_plugin_config(), Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u (+14 more)

### Community 12 - "CaptureResult"
Cohesion: 0.11
Nodes (10): CaptureResult, Outcome of a single :func:`capture_snapshot` call.      The :class:`~netbox_pyat, Length of the JSON-serialized ``data`` payload, in bytes., TestCaptureResultSizeBytes, BatchCaptureJobTest, CaptureJobPyatsJobPlumbingTest, ParseJobPyatsJobPlumbingTest, ADR-0005 §3 plumbing for ``capture_snapshot_job`` (Phase 5, ATW-16). (+2 more)

### Community 13 - "PyatsCredential"
Cohesion: 0.09
Nodes (23): Meta, Meta, PyatsCaptureScheduleType, PyatsCredentialType, PyatsJobType, PyatsParserCatalogRefreshScheduleType, PyatsParserCatalogType, PyatsSnapshotDiffType (+15 more)

### Community 14 - "run_capture_schedules_job"
Cohesion: 0.10
Nodes (14): RQ worker entry point — dispatch captures for all enabled schedules.      Thin m, Dispatch captures for all enabled schedules (delegates to the wrapper)., run_capture_schedules_job(), Re-resolve :attr:`device_filter` to a Device queryset (run-time).          Thin, Re-resolve a ``device_filter`` JSON spec to a Device queryset at run time., _resolve_device_filter(), TestCase, PyatsCaptureScheduleModelTest (+6 more)

### Community 15 - "PyatsSnapshot"
Cohesion: 0.09
Nodes (16): PyatsSnapshot, One captured config/state/full snapshot for a NetBox Device.      Populated by t, _AppendOnlyListViewsBase, TestCase, PyatsComplianceRunListViewRenderTest, PyatsJobListViewRenderTest, PyatsSnapshotDiffListViewRenderTest, PyatsSnapshotListViewRenderTest (+8 more)

### Community 16 - "flatten_diff_tree"
Cohesion: 0.13
Nodes (10): DiffLine, flatten_diff_tree(), One flat row in a side-by-side diff table (ATW-524/ATW-525).      A flattened vi, Flatten a structured diff tree into a list of side-by-side table rows.      Walk, Unit tests for :func:`netbox_pyats.diff.flatten_diff_tree` (ATW-524/ATW-525).  P, TestFlattenEmptyAndError, TestFlattenLeaves, TestFlattenNestedContainerLeafValues (+2 more)

### Community 17 - "test_capture_learn.py"
Cohesion: 0.15
Nodes (13): FakeLookup, FakeOpsFactory, FakeOpsNamespace, FakePyatsDevice, _patch_genie_ops(), Tests for the Genie Ops Learn capture (ATW-730).  Pure-Python: exercises :func:`, Minimal duck-typed pyATS Device for Learn tests.      The Learn path only reads, Callable that returns a :class:`FakeOpsInstance` when called with a device. (+5 more)

### Community 18 - "build_testbed"
Cohesion: 0.19
Nodes (10): build_testbed(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, _cred_resolver_factory(), _fake_testbed_factory(), FakeCredential, FakeDevice, Return a credential_resolver that always returns ``cred`` (or None)., Return a ``_pyats_testbed_cls`` callable: a function returning a raising class. (+2 more)

### Community 19 - "test_navmenu_uniqueness_guard.py"
Cohesion: 0.10
Nodes (19): _extract_menu_item_kwargs(), _extract_menu_links(), _extract_model_classes(), _extract_schema_type_models(), GraphQLSchemaCompletenessGuard, _is_menu_var(), NavMenuUniquenessGuard, Hardening guard for the navigation menu and GraphQL schema surface.  These tests (+11 more)

### Community 20 - "testbed.py"
Cohesion: 0.09
Nodes (20): _build_device_entry(), _device_display_name(), _iter_devices(), _mgmt_address(), _protocol_for(), _pyats_device_cls(), _pyats_testbed_cls(), NetBox → pyATS testbed bridge.  :func:`build_testbed` constructs a :class:`pyats (+12 more)

### Community 21 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 22 - "run_diff_job"
Cohesion: 0.14
Nodes (23): BaseException, capture_snapshot_job(), _finish_success(), learn_snapshot_job(), _mark_running(), parse_commands_job(), _persist_error_row(), _persist_input_error_row() (+15 more)

### Community 23 - "test_template_extension.py"
Cohesion: 0.09
Nodes (22): Module, Path, Structural guard for the device-page PyATS tab registration (ATW-393 / ADR-0007), ATW-409 regression guard: DevicePyATSTabView.get_extra_context must     include, ADR-0007: the PluginTemplateExtension module is deleted., DevicePyATSTabView must be decorated with register_model_view(Device, 'pyats')., DevicePyATSTabView must subclass generic.ObjectView., DevicePyATSTabView must declare a ViewTab with label='PyATS'. (+14 more)

### Community 24 - "run_parser_catalog_refresh_schedules_job"
Cohesion: 0.13
Nodes (13): _next_run_at(), Compute the ``next_run_at`` timestamp for a recurring schedule (ATW-610).      T, RQ worker entry point — refresh the parser catalog when the schedule is enabled., Dispatch a parser catalog refresh when the schedule is enabled.          ``JobRu, run_parser_catalog_refresh_schedules_job(), TestCase, PyatsParserCatalogRefreshScheduleModelTest, Tests for the PyatsParserCatalogRefreshSchedule model + dispatcher (ATW-581).  R (+5 more)

### Community 25 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.11
Nodes (6): TestCase, PyatsSnapshotDiffModelTest, PyatsSnapshotModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Persistence and helper behavior of PyatsSnapshot., Regression for ATW-68: a diff error row with before/after NULL must         roun

### Community 26 - "DeviceParseViewTest"
Cohesion: 0.09
Nodes (7): DeviceParseFormTest, DeviceParseViewTest, DeviceRefreshCatalogViewTest, TestCase, View tests for :class:`views.DeviceRefreshCatalogView` (ATW-250)., Pure-form validation for :class:`forms.DeviceParseForm`., View tests for :class:`views.DeviceParseView` (ATW-250).

### Community 27 - "DeviceDiffFormKindFilterTest"
Cohesion: 0.17
Nodes (7): DeviceDiffFormKindFilterTest, DeviceDiffViewKindFilterTest, _make_snapshot(), TestCase, The ``device_diff`` view surfaces the kind filter as a redirect+flash., Create a minimal PyatsSnapshot row of the given kind for ``device``., Form-level kind-filter enforcement (ATW-241 child 4).

### Community 28 - "PyatsComplianceRunModelTest"
Cohesion: 0.16
Nodes (5): TestCase, PyatsComplianceRunModelTest, PyatsGoldenConfigModelTest, Persistence and helper behavior of PyatsComplianceRun (Phase 4, ATW-15)., Persistence and helper behavior of PyatsGoldenConfig.

### Community 29 - "PyatsJobModelTest"
Cohesion: 0.11
Nodes (7): DeviceBulkCaptureViewTest, DiffJobPyatsJobPlumbingTest, TestCase, PyatsJobModelTest, ADR-0005 §3 plumbing for ``run_diff_job`` (Phase 5, ATW-16)., Persistence + helpers for PyatsJob (Phase 5, ATW-16)., The device-list bulk "PyATS capture" view renders its confirmation     form (Pha

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

### Community 34 - "Graphify MCP HTTP server — multi-host / shared-service runbook"
Cohesion: 0.10
Nodes (18): End-to-end OpenCode remote wiring — verified 2026-07-21, Graphify MCP, Bring-up (from a worktree), Decisions, Files, Graphify MCP HTTP server — multi-host / shared-service runbook, Hardening summary (audit checklist), Prerequisites (+10 more)

### Community 35 - "crypto.py"
Cohesion: 0.14
Nodes (15): decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), is_encrypted_token(), Encryption helpers for the plugin-local PyATS credential store.  Field-level enc, Decrypt a Fernet token produced by :func:`encrypt`.      Empty input round-trips (+7 more)

### Community 36 - "jobs.py"
Cohesion: 0.16
Nodes (17): _create_pyats_job(), enqueue_batch_capture(), enqueue_capture(), enqueue_compliance(), enqueue_diff(), enqueue_learn(), enqueue_parse(), enqueue_refresh_parser_catalog() (+9 more)

### Community 37 - "test_testbed.py"
Cohesion: 0.14
Nodes (11): is_supported_os(), True if ``os_value`` is a Genie-supported os (not the unsupported sentinel)., DuplicateDeviceError, FakeDeviceType, FakeIPAddress, Exception, Tests for :mod:`netbox_pyats.testbed`.  Pure-Python: exercises the NetBox→pyATS, Duck-type stand-in for ``pyats.topology.testbed.DuplicateDeviceError``.      The (+3 more)

### Community 38 - "test_pr_body_scrub_guard.py"
Cohesion: 0.16
Nodes (17): CompletedProcess, Tests for scripts/pr-body-scrub-guard.sh.  The PR body scrub guard is the struct, Role words in normal prose (not on a reviewer/merger line) are fine., An 8-char commit short-SHA must NOT trip the agent-prefix pattern., PR #44/#45 form: `[@CTO](agent://<uuid>)`., A bare RFC-4122 UUID anywhere in the body is caught., PR #47 form: `reviewer: @CTO (agent <prefix>)`., The exact PR #47 leaked line — prefix + role, caught by the prefix. (+9 more)

### Community 39 - "Troubleshooting"
Cohesion: 0.12
Nodes (17): Compliance results, `compliant` when you expected `drift`, Diff statuses, `drift` when you expected `compliant`, `empty` status, `error` result with "missing golden config" / "snapshot has no config payload", `error` status, `error` status with `connection failed` (+9 more)

### Community 40 - ".get"
Cohesion: 0.15
Nodes (4): Resolve the pyATS os + catalog row + command choices for a device.      Web-proc, Return the POST URL for the device-page "Refresh parser list" button., _refresh_parser_catalog_url_for_device(), _resolve_parse_context()

### Community 42 - "compliance.py"
Cohesion: 0.14
Nodes (13): _build_tree(), ComplianceResult, _normalize_lines(), _ordered_diff(), Compliance engine — golden config vs. snapshot raw config diff (Phase 4, ATW-15), Outcome of a single :func:`run_compliance` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves (drift). (+5 more)

### Community 43 - "extract_snapshot_raw_config"
Cohesion: 0.21
Nodes (5): extract_snapshot_raw_config(), Extract the snapshot's raw running-config text (the compliance "actual").      v, Regression test for the compliance job's legacy ``config[raw]`` fallback (ATW-43, Pin the contract of :func:`extract_snapshot_raw_config` (ATW-437)., TestExtractSnapshotRawConfig

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

### Community 48 - "GenieParseViewTest"
Cohesion: 0.13
Nodes (4): GenieParseViewTest, TestCase, Tests for the dedicated Genie Parse page (ATW-729).  Requires a running NetBox/D, View tests for :class:`views.GenieParseView` (ATW-729).

### Community 49 - "PyatsCredentialForm"
Cohesion: 0.14
Nodes (6): PyatsCredentialForm, Initialize the form with an optional device scope.          Args:             de, Create/edit form for a PyATS Credential.      Plaintext password/enable_secret a, Initialize the form, optionally pinning the ``commands`` choices.          Args:, Require at least one of ``commands`` or ``manual_command``.          The parse j, NetBoxModelForm

### Community 50 - "dev-seed.sh"
Cohesion: 0.27
Nodes (10): cmd_build(), cmd_force_restore(), cmd_info(), cmd_remove(), cmd_restore(), die(), _restore(), dev-seed.sh script (+2 more)

### Community 51 - "ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts"
Cohesion: 0.15
Nodes (13): 1. PR bodies use role-only labels — no identifiers (hard rule), 2. `[@Agent](agent://<id>)` is internal-only, 3. Boundary rule: public artifact vs internal comment, 4. Merger verifies before merge, 5. Retroactive redaction is harm-reduction, not elimination, ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts, Alternatives considered, Blast radius (+5 more)

### Community 52 - "Remote access to the dev NetBox UI over Tailscale"
Cohesion: 0.15
Nodes (12): Fallback path: SSH tunnel over Tailscale, Host facts (fill in your own), Prerequisites, Quick decision table, Recommended path: `tailscale serve` (tailnet-only, auto-HTTPS), Remote access to the dev NetBox UI over Tailscale, Repeatable alias, Repeatable one-liner (recommended alias) (+4 more)

### Community 53 - "Usage guide"
Cohesion: 0.15
Nodes (13): 1 — Add a credential, 2 — Capture a snapshot, 3 — On-demand Parse, 4 — Diff two snapshots, 5 — Add a golden config, 6 — Run compliance, 7 — Browse everything, 8 — Build a testbed programmatically (+5 more)

### Community 54 - "PyatsGoldenConfigAPITest"
Cohesion: 0.15
Nodes (3): APITestCase, PyatsComplianceRunAPITest, PyatsGoldenConfigAPITest

### Community 55 - "test_supported_platforms.py"
Cohesion: 0.15
Nodes (6): TestCase, Tests for the supported-platforms report (Phase 5, ATW-16, Option A).  Two lanes, Report contents: the static map renders with per-slug device counts., ADR-0001 §6: the data path the report view reads must not import Genie.      The, SupportedPlatformsReportViewTest, TestSupportedPlatformsReportWebProcessSafety

### Community 57 - "GenieLearnViewTest"
Cohesion: 0.17
Nodes (4): GenieLearnViewTest, TestCase, Tests for the dedicated Genie Learn page (ATW-730).  Requires a running NetBox/D, View tests for :class:`views.GenieLearnView` (ATW-730).

### Community 58 - "_extract_snapshot_raw"
Cohesion: 0.27
Nodes (4): _extract_snapshot_raw(), Tests for the compliance job's snapshot-raw extraction in :mod:`netbox_pyats.job, Replicate the extraction logic in :func:`run_compliance_job` for unit testing., TestSnapshotRawExtraction

### Community 59 - "TestSupportedPlatformsMap"
Cohesion: 0.17
Nodes (3): The static map the report renders (Phase 5, ATW-16, Option A)., TestSupportedPlatformsMap, FakeManufacturer

### Community 60 - "netbox-pyats"
Cohesion: 0.17
Nodes (12): At a glance, Capture, Compare, Compatibility matrix, Compliance & Jobs, Device-page UI, Documentation, Getting help (+4 more)

### Community 61 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 62 - "FakeOpsInstance"
Cohesion: 0.20
Nodes (7): _capture_learn(), _discover_ops_features(), Any, Run the Genie Ops Learn capture on a connected pyATS Device (ATW-730).      Geni, Return ``[(feature_name, ops_factory), ...]`` from a Genie Ops Lookup.      The, FakeOpsInstance, Duck-typed Genie Ops instance returned by an Ops class factory.      ``_capture_

### Community 63 - "PyatsCredentialModelTest"
Cohesion: 0.18
Nodes (3): TestCase, PyatsCredentialModelTest, Field-level encryption and validation behavior of PyatsCredential.

### Community 64 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 65 - "ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension"
Cohesion: 0.20
Nodes (10): 1. New `PyatsJob` model (single home: `models.py`, per ADR-0001 §2), 2. Status vocabulary extension (extends ADR-0002's table), 3. Plumbing contract (non-breaking), 4. Unified jobs view, ADR-0005: PyatsJob unified job-tracking model + status vocabulary extension, Alternatives considered, Consequences, Context (+2 more)

### Community 66 - "TestStateCommandsInvariant"
Cohesion: 0.20
Nodes (3): Hardening invariant guard for :data:`netbox_pyats.capture.STATE_COMMANDS` (ATW-4, Structural invariants for :data:`STATE_COMMANDS` (ATW-436)., TestStateCommandsInvariant

### Community 67 - "[0.1.0] - Unreleased"
Cohesion: 0.22
Nodes (9): [0.1.0] - Unreleased, Added, Added, Changed, Changelog, Compatibility, Dev, Docs (+1 more)

### Community 68 - "Scheduled captures"
Cohesion: 0.22
Nodes (9): Creating a schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled captures, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 69 - "Scheduled parser-catalog refresh"
Cohesion: 0.22
Nodes (9): Enabling the schedule, External cron fallback, How it works, One-shot dispatch (run now), Scheduled parser-catalog refresh, Scheduling the dispatcher job, See also, Verifying a scheduled run (+1 more)

### Community 70 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 71 - "ADR-0008: Scheduling surface for recurring snapshot capture"
Cohesion: 0.25
Nodes (8): ADR-0008: Scheduling surface for recurring snapshot capture, Alternatives considered, Consequences, Context, Decision, References, Structural shape, Why this fits the locked architecture

### Community 72 - "Graphify"
Cohesion: 0.25
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 73 - "Compliance engine"
Cohesion: 0.25
Nodes (8): Both modes are line-oriented text diff, not Genie-structured diff, Classification, Compliance engine, Engine layer, Related, The diff view, What it does, What the snapshot needs

### Community 74 - "Upgrade guide"
Cohesion: 0.25
Nodes (8): Before you begin, Both at once (NetBox + plugin upgrade), NetBox upgrade (plugin release unchanged), Next steps, Plugin upgrade (NetBox release unchanged), Troubleshooting an upgrade, Upgrade guide, What stays in sync with what

### Community 75 - "PyATS worker deployment"
Cohesion: 0.25
Nodes (8): Option A — install pyats into your own worker, Option B — the shipped worker image (reference / dev), PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, What runs on the `pyats` queue, Why a separate queue

### Community 77 - "DiffTableRenderTest"
Cohesion: 0.36
Nodes (3): DiffTableRenderTest, TestCase, Render ``inc/diff_table.html`` via the snapshot-diff detail view and     assert

### Community 78 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 79 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 80 - "CI"
Cohesion: 0.29
Nodes (7): CI, `integration`, Lanes, `lint`, References, `unit`, What to keep green

### Community 81 - "Installation"
Cohesion: 0.29
Nodes (7): Compatibility, Installation, Next steps, Step 1 — Install the plugin, Step 2 — Configure NetBox, Step 3 — Set up the pyats worker, Step 4 — Verify the install

### Community 82 - "PULL_REQUEST_TEMPLATE.md"
Cohesion: 0.29
Nodes (6): Changes, Closing checklist, Linked issue, Notes for reviewers, Summary, Verification

### Community 83 - "__init__.py"
Cohesion: 0.29
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 84 - "TestStateCapture"
Cohesion: 0.29
Nodes (4): kind=state runs device.parse() for each command in STATE_COMMANDS., Per-command ParserNotFound is recorded as a warning, not a failure., CR-3: a non-ParserNotFound parse exception is a real failure, not a         beni, TestStateCapture

### Community 86 - "ADR-0007: Device-page tab via `register_model_view` + `ObjectView`"
Cohesion: 0.33
Nodes (6): ADR-0007: Device-page tab via `register_model_view` + `ObjectView`, Alternatives considered, Consequences, Context, Decision, References

### Community 87 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 88 - "DiffResult"
Cohesion: 0.33
Nodes (4): DiffResult, Outcome of a single :func:`diff_snapshots` call.      The RQ job (:func:`netbox_, Length of the JSON-serialized ``diff`` payload, in bytes., True if the diff found any added/removed/changed leaves.

### Community 89 - "batch_capture_job"
Cohesion: 0.33
Nodes (6): batch_capture_job(), _finish_partial(), _persist_snapshot(), Set a batch :class:`PyatsJob` to ``partial`` with batch counts (ADR-0005 §3 + §2, Persist a successful-path :class:`PyatsSnapshot` row from a capture result., RQ worker entry point — capture snapshots for a batch of devices.      NetBox's

### Community 90 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 91 - "graphify-mcp-key.sh"
Cohesion: 0.53
Nodes (4): ensure_gitignored(), fingerprint_key(), graphify-mcp-key.sh script, usage()

### Community 92 - "netbox-pyats documentation"
Cohesion: 0.40
Nodes (5): Conventions, For contributors (developing the plugin), For everyone, For operators (running the plugin in NetBox), netbox-pyats documentation

### Community 96 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 97 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 98 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **285 isolated node(s):** `entrypoint.sh script`, `GRAPHIFY_API_KEY`, `pyats-test-entrypoint.sh script`, `DJANGO_SETTINGS_MODULE`, `Migration` (+280 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **44 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SnapshotKindChoices` connect `PyatsSnapshotDiff` to `SnapshotStatusChoices`, `PyatsJob`, `resolve_panel_platform_support`, `capture_snapshot`, `capture.py`, `CaptureResult`, `PyatsCredential`, `run_capture_schedules_job`, `PyatsSnapshot`, `test_capture_learn.py`, `PyatsSnapshotDiffModelTest`, `DeviceDiffFormKindFilterTest`, `PyatsComplianceRunModelTest`, `PyatsJobModelTest`, `jobs.py`, `PyatsComplianceRunViewTest`, `PyatsCredentialForm`, `PyatsGoldenConfigAPITest`, `FakeOpsInstance`, `DiffTableRenderTest`, `TestStateCapture`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `PyatsJob` connect `PyatsJob` to `PyatsSnapshotDiff`, `SnapshotStatusChoices`, `views.py`, `ComplianceModeChoices`, `jobs.py`, `refresh_parser_catalog_for_os`, `CaptureResult`, `PyatsCredential`, `PyatsSnapshot`, `PyatsCredentialForm`, `PyatsJobModelTest`, `.get_status_color`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `PyatsSnapshotDiff` connect `PyatsSnapshotDiff` to `SnapshotStatusChoices`, `views.py`, `ComplianceModeChoices`, `jobs.py`, `PyatsJob`, `.get_status_color`, `.has_changes`, `.has_warnings`, `CaptureResult`, `PyatsCredential`, `DiffTableRenderTest`, `PyatsSnapshot`, `PyatsCredentialForm`, `run_diff_job`, `PyatsSnapshotDiffModelTest`, `PyatsJobModelTest`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 156 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshot` has 156 INFERRED edges - model-reasoned connections that need verification._
- **Are the 144 inferred relationships involving `PyatsJob` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsJob` has 144 INFERRED edges - model-reasoned connections that need verification._
- **Are the 146 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 146 INFERRED edges - model-reasoned connections that need verification._
- **Are the 134 inferred relationships involving `PyatsComplianceRun` (e.g. with `Meta` and `PyatsCaptureScheduleSerializer`) actually correct?**
  _`PyatsComplianceRun` has 134 INFERRED edges - model-reasoned connections that need verification._