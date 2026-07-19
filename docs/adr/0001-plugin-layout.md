# ADR-0001: Plugin package layout

Date: 2026-07-19
Status: Accepted (CTO; CEO sign-off via [ATW-23](/ATW/issues/ATW-23) confirmation `26b21df4`)
Supersedes: —
Superseded by: —

## Context

The PyATS NetBox Plugin reached the end of Phase 3 (snapshot diff engine + viewer) with a working, idiomatic NetBox plugin layout. Before feature work continues into the compliance phase and before the Senior Dev Engineer opens non-trivial PRs, the CTO must lock the canonical package layout so every future change fits the agreed structure and new contributors can navigate the codebase without guessing.

This ADR records the layout as it stands at `main` @ `cc707b3`. It is a write-down of an existing, working structure — not a new design — so it can be referenced from `CONTRIBUTING.md` and from future ADRs (compliance model, batch capture, global credentials).

## Decision

The plugin package follows the canonical NetBox plugin shape below. This layout is **locked**: no structural change to it is permitted without a new (or amending) ADR.

```
netbox-pyats/
├── netbox_pyats/                # the plugin package (entry point: netbox_pyats:config)
│   ├── __init__.py              # NetBoxPyATSConfig (PluginConfig) — queues, template_extensions, default_settings
│   ├── version.py               # __version__ (single source; CHANGELOG + pyproject mirror)
│   ├── choices.py               # all *Choices classes (TextChoices) — single home for enums
│   ├── models.py                # PyatsCredential, PyatsSnapshot, PyatsSnapshotDiff (all NetBoxModel)
│   ├── migrations/0001–0003     # one migration per schema addition, linear
│   ├── crypto.py                # Fernet field-level encryption (no plaintext at rest, ever)
│   ├── testbed.py               # NetBox ORM → pyATS Testbed bridge (lazy pyats import)
│   ├── capture.py               # pure-Python capture core (no NetBox/RQ) + NetBox convenience wrapper
│   ├── diff.py                  # pure-Python recursive JSONB diff engine (no Genie needed)
│   ├── jobs.py                  # RQ job entry points + enqueue helpers; runs on the `pyats` queue
│   ├── views.py                 # generic CRUD + DeviceCaptureView / DeviceDiffView POST endpoints
│   ├── urls.py                  # /plugins/pyats/... routes
│   ├── forms.py / filtersets.py / tables.py / search.py / navigation.py
│   ├── template_content.py      # PluginTemplateExtension → Device page "PyATS" tab
│   ├── templates/netbox_pyats/  # server-rendered detail templates (no JS)
│   ├── api/                     # serializers, urls, views (DRF viewsets on NetBox router)
│   ├── graphql/                 # graphene types
│   └── tests/                   # pure-Python + NetBox-gated suites (importorskip pattern)
├── dev/                         # docker-compose dev env + pyats-worker Dockerfile + entrypoints
├── docs/                        # operator + contributor docs (workers.md, adr/)
├── pyproject.toml               # packaging, deps, tool config
├── docker-compose.dev.yml       # NetBox 4.6 + PG + Redis + pyats worker
├── README.md / CHANGELOG.md / CONTRIBUTING.md / LICENSE
```

### Locked conventions enforced on every PR

1. **Single source of truth per concern.** `version.py` is the only place `__version__` lives; `choices.py` is the only home for `*Choices`; `models.py` is the only home for ORM models.
2. **Models subclass `netbox.models.NetBoxModel`** (tags, custom fields, journaling, change logging for free). New models follow the 11-step "Adding a model" checklist in `CONTRIBUTING.md`.
3. **One migration per schema addition, linear.** No squashes without a CTO ADR.
4. **Templates are server-rendered, no JS.** A JS build pipeline requires a new ADR.
5. **REST + GraphQL** are generated from the same models via NetBox's standard router/type registration; secrets are write-only on REST and excluded from GraphQL.
6. **Background work always runs on the dedicated `pyats` RQ queue** (declared via `NetBoxPyATSConfig.queues = ["pyats"]`) and is enqueued through `core.models.Job.enqueue` for NetBox UI status tracking. The web process never imports pyATS; `pyats[full]` is not an install-time dependency.
7. **Pure-Python cores** (`capture.py`, `diff.py`, `crypto.py`, `testbed.py`) carry no NetBox/RQ imports so they can be unit-tested in plain Python and reused from the worker without dragging the web process in.
8. **Tests** follow the `importorskip` split: pure-Python tests run anywhere; NetBox-dependent tests skip cleanly outside the dev container and run inside it via `docker compose -f docker-compose.dev.yml exec netbox pytest`.

## Consequences

- **Positive:** new contributors can locate any concern without searching; PR review has a deterministic structural checklist; the plugin stays idiomatic and upgrade-safe against NetBox core.
- **Positive:** pure-Python cores are independently testable and CI-friendly (no DB/Redis needed), which is the foundation for D-7 (CI workflow) landing cleanly.
- **Negative:** adding a new model is an 11-step touch (model → migration → choices → form → table → filterset → search → views → urls → api → graphql → template → nav → tests). This is deliberate: it matches NetBox plugin norms and keeps the surface navigable.
- **Negative:** the no-JS, server-rendered template constraint means interactive UI features (e.g. a structured compliance tree with collapse/expand beyond `<details>`) will need an ADR if they ever require client-side JS.

## Alternatives considered

- **Split models into `models/` package (one file per model).** Rejected: the codebase is small, the single `models.py` is greppable, and NetBox plugin convention favors a single `models.py` until it becomes unwieldy. Revisit via ADR if `models.py` exceeds ~1,500 lines.
- **Bundle a JS build pipeline now for a richer diff viewer.** Rejected: server-rendered `<details>` is sufficient for v1, avoids a maintenance and security surface, and keeps the plugin install-light. Revisit only if a feature genuinely requires client-side interactivity.
- **Make `pyats[full]` an install-time dependency.** Rejected: it would force every NetBox operator to install Genie's parser tree on the web process, which is heavy and platform-fragile. The lazy-import + dedicated-queue pattern isolates the heavy dependency to the worker only.

## References

- Architecture overview, §2.1: [ATW-23 architecture document](/ATW/issues/ATW-23#document-architecture)
- `CONTRIBUTING.md` — "Adding a model" checklist
- Related: ADR-0002 (graceful degradation pattern)