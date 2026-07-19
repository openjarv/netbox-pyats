# Graph Report - netbox-pyats  (2026-07-19)

## Corpus Check
- 61 files · ~37,303 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 607 nodes · 1221 edges · 55 communities (41 shown, 14 thin omitted)
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 323 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6931cf9d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PyatsSnapshotDiff
- SnapshotStatusChoices
- diff_snapshots
- PyatsSnapshot
- PyatsCredential
- testbed.py
- capture_snapshot
- build_testbed
- EncryptDecryptTest
- PyatsCredentialAPITest
- conftest.py
- PyatsCredentialViewTest
- __init__.py
- pyats-entrypoint.sh
- pyats-worker-entrypoint.sh
- 0004_reconcile_netboxmodel_fields.py
- netbox-pyats
- SnapshotKindChoices
- PyatsSnapshotDiffModelTest
- PyatsSnapshot
- ADR-0002: Multi-vendor graceful degradation pattern
- PyatsCredentialModelTest
- Contributing to netbox-pyats
- ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain
- get_fernet_key
- jobs.py
- netbox-pyats
- PyATS worker deployment
- graphify reference: extra exports and benchmark
- DeviceCaptureView
- [0.1.0] - Unreleased
- ADR-0001: Plugin package layout
- search.py
- Architecture Decision Records
- PyatsCredentialForm
- graphify reference: query, path, explain
- capture_snapshot_for_netbox_device
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- is_encrypted_token
- 0001_initial.py
- 0002_pyatssnapshot.py
- 0003_pyatssnapshotdiff.py
- extraction-spec.md

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

## Communities (55 total, 14 thin omitted)

### Community 0 - "PyatsSnapshotDiff"
Cohesion: 0.11
Nodes (25): Who/what triggered a snapshot capture.      ``user`` captures are initiated from, SnapshotTriggerChoices, PyatsSnapshotDiff, One structured diff between two :class:`PyatsSnapshot` rows of a device.      Po, Map status to a NetBox color label for table badges., True if the diff found any added/removed/changed leaves., True if this diff row carries warnings / error context., PyatsCredentialBulkDeleteView (+17 more)

### Community 1 - "SnapshotStatusChoices"
Cohesion: 0.13
Nodes (26): CredentialProtocolChoices, CredentialScopeChoices, DiffStatusChoices, Choice sets for the netbox-pyats plugin., How a credential is assigned.      ``device`` credentials attach to a single Net, Connection protocol for a PyATS credential., Outcome of a snapshot diff (Phase 3, ATW-14).      ``success`` means a structure, Encryption helpers for the plugin-local PyATS credential store.  Field-level enc (+18 more)

### Community 2 - "diff_snapshots"
Cohesion: 0.06
Nodes (28): Any, _diff_dict(), _diff_list(), diff_snapshots(), _diff_value(), DiffResult, _leaf_type(), _node_status() (+20 more)

### Community 3 - "PyatsSnapshot"
Cohesion: 0.14
Nodes (23): Meta, PyatsCredentialSerializer, PyatsSnapshotDiffSerializer, PyatsSnapshotSerializer, Serializer for the PyatsSnapshotDiff model.      Diffs are read-only via the RES, Serializer for the PyatsSnapshot model.      Snapshots are read-only via the RES, Serializer for the PyatsCredential model.      The ``password`` and ``enable_sec, PyatsCredentialViewSet (+15 more)

### Community 4 - "PyatsCredential"
Cohesion: 0.12
Nodes (14): PyatsCredential, Encrypt and store the device password (ciphertext only)., Decrypt and return the device password (plaintext)., Encrypt and store the enable/privileged password (ciphertext only)., Decrypt and return the enable/privileged password (plaintext)., A plugin-local, encrypted credential for connecting to a device via pyATS., Meta, PyatsCredentialTable (+6 more)

### Community 5 - "testbed.py"
Cohesion: 0.07
Nodes (31): _capture_url_for_device(), DevicePyATSPanel, _diff_url_for_device(), Template extensions injecting the PyATS tab into the NetBox Device page.  Phase, Inject the PyATS capture/diff panel + recent snapshots/diffs into the Device pag, Return the POST URL for the device-page capture form., Return the POST URL for the device-page diff form (Phase 3, ATW-14)., Return the filtered snapshot-list URL for this device. (+23 more)

### Community 6 - "capture_snapshot"
Cohesion: 0.13
Nodes (11): _capture_config(), capture_snapshot(), _capture_state(), Run parser-based config capture on a connected pyATS Device.      Uses ``pyats.u, Run parser-based state capture on a connected pyATS Device.      Runs a small, O, Capture a snapshot from a single, already-connected pyATS Device.      This is t, FakePyatsDevice, kind=state runs device.parse() for each command in STATE_COMMANDS. (+3 more)

### Community 7 - "build_testbed"
Cohesion: 0.10
Nodes (16): build_testbed(), _iter_devices(), Build a pyATS :class:`Testbed` from a NetBox Device queryset.      This is the c, Yield devices from a queryset or plain iterable.      Accepts either a Django qu, Summary of a :func:`build_testbed` run.      Keeps track of which devices were i, True if at least one device was supported AND none errored.          ``build_tes, TestbedBuildReport, _cred_resolver_factory() (+8 more)

### Community 8 - "EncryptDecryptTest"
Cohesion: 0.17
Nodes (6): EncryptDecryptTest, GetFernetKeyTest, KeyRotationSensitivityTest, Tests for :mod:`netbox_pyats.crypto`.  Pure-Python: exercises key resolution (co, Document the v1 key-rotation contract: a new key cannot decrypt old tokens., SimpleTestCase

### Community 10 - "conftest.py"
Cohesion: 0.29
Nodes (5): _configure_minimal(), _configure_netbox(), pytest configuration for netbox_pyats tests.  Two modes, matching the netbox-atw, Minimal Django config for pure-Python tests (no NetBox installed).      ``netbox, Use NetBox's own settings when running inside a NetBox environment.

### Community 12 - "__init__.py"
Cohesion: 0.40
Nodes (3): NetBoxPyATSConfig, Version information for netbox-pyats., PluginConfig

### Community 15 - "0004_reconcile_netboxmodel_fields.py"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 22 - "SnapshotKindChoices"
Cohesion: 0.18
Nodes (18): Exception, CaptureResult, Snapshot capture logic — the pyATS/Genie work, isolated from NetBox/RQ.  :func:`, Outcome of a single :func:`capture_snapshot` call.      The :class:`~netbox_pyat, Length of the JSON-serialized ``data`` payload, in bytes., What a :class:`PyatsSnapshot` captures from a device.      ``config`` runs parse, Outcome of a snapshot capture attempt.      ``success`` means a JSONB ``data`` p, SnapshotKindChoices (+10 more)

### Community 23 - "PyatsSnapshotDiffModelTest"
Cohesion: 0.12
Nodes (5): TestCase, PyatsSnapshotDiffModelTest, PyatsSnapshotModelTest, Persistence and helper behavior of PyatsSnapshotDiff (Phase 3, ATW-14)., Persistence and helper behavior of PyatsSnapshot.

### Community 24 - "PyatsSnapshot"
Cohesion: 0.15
Nodes (14): Meta, PyatsCredentialType, PyatsSnapshotDiffType, PyatsSnapshotType, Query, GraphQL type for the PyatsSnapshot model.      Exposes the full JSONB ``data`` p, GraphQL type for the PyatsSnapshotDiff model (Phase 3, ATW-14).      Exposes the, GraphQL type for the PyatsCredential model.      ``password`` and ``enable_secre (+6 more)

### Community 25 - "ADR-0002: Multi-vendor graceful degradation pattern"
Cohesion: 0.18
Nodes (11): ADR-0002: Multi-vendor graceful degradation pattern, Alternatives considered, Capture path (`capture.py` + `jobs.py`), Consequences, Context, Decision, Diff path (`diff.py` + `jobs.py`), References (+3 more)

### Community 26 - "PyatsCredentialModelTest"
Cohesion: 0.18
Nodes (3): TestCase, PyatsCredentialModelTest, Field-level encryption and validation behavior of PyatsCredential.

### Community 27 - "Contributing to netbox-pyats"
Cohesion: 0.20
Nodes (10): Adding a model, Adding a supported platform, Architectural decisions (ADRs), Branch / PR conventions, Contributing to netbox-pyats, Full NetBox test suite (integration), Lint and format, Local dev environment (+2 more)

### Community 28 - "ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain"
Cohesion: 0.20
Nodes (10): ADR-0003: NetBox 4.6 migration dependencies and worker build toolchain, Alternatives considered, Blocker 1 (pyats worker build), Blocker 2 (migration dependency), Consequences, Context, Decision, Migration dependencies (Blocker 2) (+2 more)

### Community 29 - "get_fernet_key"
Cohesion: 0.20
Nodes (10): decrypt(), _derive_fernet_key_from_secret_key(), encrypt(), _get_config(), get_fernet_key(), Decrypt a Fernet token produced by :func:`encrypt`.      Empty input round-trips, Return the plugin's PLUGINS_CONFIG block (empty dict if unset)., Derive a 32-byte url-safe base64 Fernet key from a slice of SECRET_KEY.      SHA (+2 more)

### Community 30 - "jobs.py"
Cohesion: 0.24
Nodes (9): capture_snapshot_job(), enqueue_capture(), enqueue_diff(), NetBox background jobs for the netbox-pyats plugin.  Phase 2 (ATW-13) ships the, Enqueue a snapshot diff job on the dedicated ``pyats`` RQ queue.      This is th, RQ worker entry point — diff two snapshots and persist the result.      NetBox's, Enqueue a snapshot capture job on the dedicated ``pyats`` RQ queue.      This is, RQ worker entry point — capture a snapshot and persist it.      NetBox's :class: (+1 more)

### Community 31 - "netbox-pyats"
Cohesion: 0.20
Nodes (10): Compatibility matrix, Credential encryption, Development, Installation, Installing pyATS on the worker (required for snapshots), License, Multi-vendor support, netbox-pyats (+2 more)

### Community 32 - "PyATS worker deployment"
Cohesion: 0.22
Nodes (8): Capturing a snapshot, Option A: the shipped worker image (dev / reference), Option B: install pyats into your own worker, PyATS worker deployment, Running the worker, Troubleshooting, Verifying the queue and worker, Why a separate queue

### Community 33 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 34 - "DeviceCaptureView"
Cohesion: 0.29
Nodes (6): DeviceCaptureView, DeviceDiffView, Endpoint the device-page PyATS panel POSTs to.      Accepts a ``kind`` (config /, Endpoint the device-page PyATS panel POSTs to.      Accepts ``before_id`` and ``, PermissionRequiredMixin, View

### Community 35 - "[0.1.0] - Unreleased"
Cohesion: 0.29
Nodes (6): [0.1.0] - Unreleased, Added, Changelog, Compatibility, Dev, Fixed

### Community 36 - "ADR-0001: Plugin package layout"
Cohesion: 0.29
Nodes (7): ADR-0001: Plugin package layout, Alternatives considered, Consequences, Context, Decision, Locked conventions enforced on every PR, References

### Community 37 - "search.py"
Cohesion: 0.38
Nodes (6): PyatsCredentialIndex, PyatsSnapshotDiffIndex, PyatsSnapshotIndex, Search index for PyatsSnapshot.      Indexes the device name (via the FK) and th, Search index for PyatsSnapshotDiff (Phase 3, ATW-14).      Indexes the device na, SearchIndex

### Community 39 - "Architecture Decision Records"
Cohesion: 0.33
Nodes (6): Architecture Decision Records, Format, Index, Status legend, When NOT to write an ADR, When to write an ADR

### Community 40 - "PyatsCredentialForm"
Cohesion: 0.33
Nodes (3): PyatsCredentialForm, Create/edit form for a PyATS Credential.      Plaintext password/enable_secret a, NetBoxModelForm

### Community 41 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 42 - "capture_snapshot_for_netbox_device"
Cohesion: 0.50
Nodes (4): capture_snapshot_for_netbox_device(), Build a single-device testbed, connect, capture, disconnect.      Convenience wr, Return ``(genie_version, pyats_version)`` from the worker environment.      Best, _worker_versions()

### Community 43 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 44 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 45 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **100 isolated node(s):** `pyats-entrypoint.sh script`, `pyats-worker-entrypoint.sh script`, `Migration`, `Migration`, `Migration` (+95 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PyatsCredential` connect `PyatsCredential` to `PyatsSnapshotDiff`, `SnapshotStatusChoices`, `DeviceCaptureView`, `PyatsSnapshot`, `search.py`, `testbed.py`, `build_testbed`, `PyatsCredentialForm`, `PyatsCredentialAPITest`, `PyatsCredentialViewTest`, `SnapshotKindChoices`, `PyatsSnapshot`, `PyatsCredentialModelTest`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `PyatsSnapshotDiff` connect `PyatsSnapshotDiff` to `SnapshotStatusChoices`, `DeviceCaptureView`, `PyatsSnapshot`, `PyatsCredential`, `search.py`, `testbed.py`, `PyatsCredentialForm`, `SnapshotKindChoices`, `PyatsSnapshotDiffModelTest`, `PyatsSnapshot`, `jobs.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `PyatsSnapshot` connect `PyatsSnapshot` to `PyatsSnapshotDiff`, `SnapshotStatusChoices`, `DeviceCaptureView`, `PyatsSnapshot`, `PyatsCredential`, `search.py`, `testbed.py`, `PyatsCredentialForm`, `SnapshotKindChoices`, `PyatsSnapshotDiffModelTest`, `jobs.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `PyatsCredential` (e.g. with `Meta` and `PyatsCredentialSerializer`) actually correct?**
  _`PyatsCredential` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `PyatsSnapshot` (e.g. with `Meta` and `PyatsCredentialSerializer`) actually correct?**
  _`PyatsSnapshot` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `PyatsSnapshotDiff` (e.g. with `Meta` and `PyatsCredentialSerializer`) actually correct?**
  _`PyatsSnapshotDiff` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `SnapshotKindChoices` (e.g. with `CaptureResult` and `DeviceCaptureForm`) actually correct?**
  _`SnapshotKindChoices` has 39 INFERRED edges - model-reasoned connections that need verification._