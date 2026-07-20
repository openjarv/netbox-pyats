# Graph Report - .  (2026-07-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 639 nodes · 1260 edges · 51 communities (40 shown, 11 thin omitted)
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 323 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `598d997d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- build_testbed
- SnapshotStatusChoices
- diff_snapshots
- capture_snapshot
- views.py
- What You Must Do When Invoked
- SnapshotKindChoices
- PyatsCredential
- PyatsSnapshotDiff
- PyatsSnapshot
- EncryptDecryptTest
- template_content.py
- Contributing to netbox-pyats
- ADR-0002: Multi-vendor graceful degradation pattern
- netbox-pyats
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- Dev environment bring-up
- PyATS worker deployment
- Graphify
- tables.py
- graphify reference: extra exports and benchmark
- PyatsCredentialAPITest
- DeviceCaptureView
- dev-worktree.sh
- [0.1.0] - Unreleased
- conftest.py
- ADR-0001: Plugin package layout
- search.py
- PyatsCredentialViewTest
- Architecture Decision Records
- jobs.py
- graphify reference: query, path, explain
- __init__.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- 0004_reconcile_netboxmodel_fields.py
- extraction-spec.md
- netbox-pyats

## God Nodes (most connected - your core abstractions)
1. `PyatsCredential` - 82 edges
2. `PyatsSnapshot` - 82 edges
3. `PyatsSnapshotDiff` - 81 edges
4. `SnapshotKindChoices` - 49 edges
5. `SnapshotTriggerChoices` - 35 edges
6. `SnapshotStatusChoices` - 30 edges
7. `CredentialProtocolChoices` - 29 edges
8. `DiffStatusChoices` - 28 edges
9. `diff_snapshots()` - 27 edges
10. `build_testbed()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `PyatsCredentialSerializer` --uses--> `PyatsCredential`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsSnapshot`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `PyatsCredentialSerializer` --uses--> `PyatsSnapshotDiff`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `Meta` --uses--> `PyatsCredential`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py
- `Meta` --uses--> `PyatsSnapshot`  [INFERRED]
  netbox_pyats/api/serializers.py → netbox_pyats/models.py

## Import Cycles
- None detected.

## Communities (51 total, 11 thin omitted)

### Community 0 - "build_testbed"
Cohesion: 0.05
Nodes (37): _build_device_entry(), build_testbed(), is_supported_os(), _iter_devices(), _mgmt_address(), platform_to_pyats_os(), _protocol_for(), _pyats_device_cls() (+29 more)

### Community 1 - "SnapshotStatusChoices"
Cohesion: 0.05
Nodes (49): CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, Choice sets for the netbox-pyats plugin., How a credential is assigned.      ``device`` credentials attach to a single Net, Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, Connection protocol for a PyATS credential., Outcome of a snapshot diff (Phase 3, ATW-14).      ``success`` means a structure (+41 more)

### Community 2 - "diff_snapshots"
Cohesion: 0.06
Nodes (32): Any, _diff_dict(), _diff_list(), diff_snapshots(), _diff_value(), DiffResult, _leaf_type(), _node_status() (+24 more)

### Community 3 - "capture_snapshot"
Cohesion: 0.08
Nodes (29): Exception, _capture_config(), capture_snapshot(), capture_snapshot_for_netbox_device(), _capture_state(), CaptureResult, Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u (+21 more)

### Community 4 - "views.py"
Cohesion: 0.13
Nodes (23): Meta, PyatsCredentialSerializer, PyatsSnapshotDiffSerializer, PyatsSnapshotSerializer, Serializer for the PyatsSnapshotDiff model.      Diffs are read-only via the RES, Serializer for the PyatsCredential model.      The ``password`` and ``enable_sec, Serializer for the PyatsSnapshot model.      Snapshots are read-only via the RES, PyatsCredentialViewSet (+15 more)

### Community 5 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 6 - "SnapshotKindChoices"
Cohesion: 0.18
Nodes (22): What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotKindChoices, SnapshotTriggerChoices, PyatsCredentialBulkDeleteView, PyatsCredentialDeleteView, PyatsCredentialEditView, PyatsCredentialListView (+14 more)

### Community 7 - "PyatsCredential"
Cohesion: 0.11
Nodes (16): Meta, PyatsCredentialType, PyatsSnapshotDiffType, PyatsSnapshotType, Query, GraphQL type for the PyatsSnapshot model.      Exposes the full JSONB ``data`` p, GraphQL type for the PyatsSnapshotDiff model (Phase 3, ATW-14).      Exposes the, GraphQL type for the PyatsCredential model.      ``password`` and ``enable_secre (+8 more)

### Community 8 - "PyatsSnapshotDiff"
Cohesion: 0.15
Nodes (7): PyatsSnapshotDiff, One structured diff between two :class:`PyatsSnapshot` rows of a device.      Po, Map status to a NetBox color label for table badges., True if the diff found any added/removed/changed leaves., True if this diff row carries warnings / error context., PyatsSnapshotDiffModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14).

### Community 9 - "PyatsSnapshot"
Cohesion: 0.15
Nodes (7): PyatsSnapshot, One captured config/state/full snapshot for a NetBox Device.      Populated by t, Map status to a NetBox color label for table badges., True if this snapshot row carries parser warnings / error context., TestCase, PyatsSnapshotModelTest, Persistence and helper behavior of PyatsSnapshot.

### Community 10 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 11 - "template_content.py"
Cohesion: 0.21
Nodes (10): _capture_url_for_device(), DevicePyATSPanel, _diff_url_for_device(), Template extensions injecting the PyATS tab into the NetBox Device page.  Phase, Inject the PyATS capture/diff panel + recent snapshots/diffs into the Device pag, Return the POST URL for the device-page capture form., Return the POST URL for the device-page diff form (Phase 3, ATW-14)., Return the filtered snapshot-list URL for this device. (+2 more)

### Community 12 - "Contributing to netbox-pyats"
Cohesion: 0.18
Nodes (11): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, CI, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format (+3 more)

### Community 13 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 14 - "netbox-pyats"
Cohesion: 0.18
Nodes (11): CI, Compatibility matrix, Credential encryption, Development, Installation, Installing pyATS on the worker (required for snapshots), License, Multi-vendor support (+3 more)

### Community 15 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 16 - "Dev environment bring-up"
Cohesion: 0.20
Nodes (9): Bring-up, Dev environment bring-up, Prerequisites, Remote access, Resource limits, Teardown, Troubleshooting, Working in parallel (+1 more)

### Community 17 - "PyATS worker deployment"
Cohesion: 0.22
Nodes (8): Capturing a snapshot, Option A: the shipped worker image (dev / reference), Option B: install pyats into your own worker, PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, Why a separate queue

### Community 18 - "Graphify"
Cohesion: 0.22
Nodes (8): Graphify, How the graph stays current, How to query the graph, How to refresh manually, Notes, Setup (already done — for reference), What is committed, What is NOT committed (gitignored)

### Community 19 - "tables.py"
Cohesion: 0.28
Nodes (8): Meta, PyatsCredentialTable, PyatsSnapshotDiffTable, PyatsSnapshotTable, Table configuration for the PyatsSnapshot list view.      Renders the snapshot's, Table configuration for the PyatsCredential list view., Table configuration for the PyatsSnapshotDiff list view.      Renders the diff's, NetBoxTable

### Community 20 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 22 - "DeviceCaptureView"
Cohesion: 0.29
Nodes (6): DeviceCaptureView, DeviceDiffView, Endpoint the device-page PyATS panel POSTs to.      Accepts a ``kind`` (config /, Endpoint the device-page PyATS panel POSTs to.      Accepts ``before_id`` and ``, PermissionRequiredMixin, View

### Community 23 - "dev-worktree.sh"
Cohesion: 0.61
Nodes (7): cmd_add(), cmd_remove(), cmd_up(), die(), next_free_port(), dev-worktree.sh script, usage()

### Community 24 - "[0.1.0] - Unreleased"
Cohesion: 0.29
Nodes (6): [0.1.0] - Unreleased, Added, Changelog, Compatibility, Dev, Fixed

### Community 25 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 26 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 27 - "search.py"
Cohesion: 0.38
Nodes (6): PyatsCredentialIndex, PyatsSnapshotDiffIndex, PyatsSnapshotIndex, Search index for PyatsSnapshot.      Indexes the device (FK stringified to its `, Search index for PyatsSnapshotDiff (Phase 3, ATW-14).      Indexes the device (F, SearchIndex

### Community 30 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 31 - "jobs.py"
Cohesion: 0.40
Nodes (5): capture_snapshot_job(), enqueue_capture(), NetBox background jobs for the netbox-pyats plugin.  Phase 2 (ATW-13) ships the, Enqueue a snapshot capture job on the dedicated ``pyats`` RQ queue.      This is, RQ worker entry point — capture a snapshot and persist it.      NetBox's :class:

### Community 32 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 33 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 34 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 35 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 36 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **118 isolated node(s):** `pyats-entrypoint.sh script`, `pyats-worker-entrypoint.sh script`, `Migration`, `Migration`, `Migration` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PyatsCredential` connect `PyatsCredential` to `build_testbed`, `SnapshotStatusChoices`, `views.py`, `SnapshotKindChoices`, `tables.py`, `PyatsCredentialAPITest`, `DeviceCaptureView`, `search.py`, `PyatsCredentialViewTest`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `PyatsSnapshotDiff` connect `PyatsSnapshotDiff` to `SnapshotStatusChoices`, `diff_snapshots`, `views.py`, `SnapshotKindChoices`, `PyatsCredential`, `PyatsSnapshot`, `template_content.py`, `tables.py`, `DeviceCaptureView`, `search.py`, `jobs.py`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `SnapshotStatusChoices`, `views.py`, `SnapshotKindChoices`, `PyatsCredential`, `PyatsSnapshotDiff`, `template_content.py`, `tables.py`, `DeviceCaptureView`, `search.py`, `jobs.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `PyatsCredential` (e.g. with `Meta` and `PyatsCredentialSerializer`) actually correct?**
  _`PyatsCredential` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsCredentialSerializer`) actually correct?**
  _`PyatsSnapshot` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsCredentialSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `SnapshotKindChoices` (e.g. with `CaptureResult` and `DeviceCaptureForm`) actually correct?**
  _`SnapshotKindChoices` has 39 INFERRED edges - model-reasoned connections that need verification._