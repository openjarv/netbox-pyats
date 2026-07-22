# Coverage Gap Report — netbox-pyats

**Date:** 2026-07-22
**Source issue:** [ATW-95](/ATW/issues/ATW-95)
**Commit at audit:** `254e6c3` (main)
**Tool:** `pytest-cov` (coverage.py)

---

## Executive Summary

| Metric | Value |
|---|---|
| Total statements | 3,256 |
| Covered statements | 1,215 |
| Missing statements | 2,041 |
| **Overall coverage** | **37%** |
| Tests collected | 106 |
| Tests passed | 106 |
| Tests skipped | 8 |

The plugin has solid unit-test coverage for its core parsing and logic modules (`choices`, `compliance`, `crypto`, `diff`, `testbed`, `capture`) but **zero coverage** on several large, user-facing modules: `jobs.py`, `models.py`, `views.py`, and the entire `api/` package.

---

## Per-Module Coverage (source only — tests excluded)

| Module | Statements | Missing | Coverage | Status |
|---|---|---|---|---|
| `__init__.py` | 14 | 0 | 100% | ✅ |
| `api/serializers.py` | 62 | 62 | 0% | 🔴 |
| `api/urls.py` | 11 | 11 | 0% | 🔴 |
| `api/views.py` | 32 | 32 | 0% | 🔴 |
| `capture.py` | 133 | 27 | 80% | 🟡 |
| `choices.py` | 41 | 0 | 100% | ✅ |
| `compliance.py` | 65 | 0 | 100% | ✅ |
| `crypto.py` | 42 | 1 | 98% | ✅ |
| `diff.py` | 104 | 8 | 92% | ✅ |
| `filtersets.py` | 26 | 26 | 0% | 🔴 |
| `forms.py` | 91 | 91 | 0% | 🔴 |
| `graphql/schema.py` | 20 | 20 | 0% | 🔴 |
| `jobs.py` | 283 | 283 | 0% | 🔴 |
| `models.py` | 181 | 181 | 0% | 🔴 |
| `navigation.py` | 3 | 3 | 0% | 🔴 |
| `search.py` | 26 | 26 | 0% | 🔴 |
| `tables.py` | 84 | 84 | 0% | 🔴 |
| `template_content.py` | 35 | 35 | 0% | 🔴 |
| `testbed.py` | 105 | 9 | 91% | ✅ |
| `urls.py` | 5 | 5 | 0% | 🔴 |
| `version.py` | 1 | 0 | 100% | ✅ |
| `views.py` | 196 | 196 | 0% | 🔴 |

**Migrations** are excluded from gap analysis (auto-generated, tested implicitly by Django's migration framework).

---

## Critical Gaps (0% coverage, high impact)

### P0 — `jobs.py` (283 statements, 0%)
The largest untested module. Contains the RQ background job logic for snapshot capture, diff, and compliance runs. Every code path — job dispatch, error handling, retry logic — is untested.

**Risk:** Silent job failures in production with no test guard. Any refactoring of the job pipeline is unguarded.

### P0 — `models.py` (181 statements, 0%)
Core Django models (`PyatsSnapshot`, `PyatsSnapshotDiff`, `ComplianceRun`, `PyatsJob`). No model-level tests exercise field validation, save logic, or model methods.

**Risk:** Data integrity bugs (e.g., nullable FK handling, snapshot parsing) are uncaught. `test_models.py` exists but only imports models without exercising them (3% coverage on the test file itself).

### P0 — `views.py` (196 statements, 0%)
All Django views — list, detail, edit, delete, custom actions for snapshots, diffs, compliance, and jobs. Zero coverage.

**Risk:** UI regressions and broken user workflows are undetectable by tests.

### P1 — `api/` package (105 statements total, 0%)
`api/serializers.py` (62), `api/views.py` (32), `api/urls.py` (11) — the REST API surface is completely untested.

**Risk:** API contract violations, broken serialization, incorrect filtering.

### P1 — `forms.py` (91 statements, 0%)
Django form definitions for the plugin's UI. Untested.

### P1 — `tables.py` (84 statements, 0%)
Django-tables2 column definitions. Untested.

### P2 — `filtersets.py` (26 statements, 0%)
Filter logic for API and views. Untested.

### P2 — `graphql/schema.py` (20 statements, 0%)
GraphQL types and resolvers. Untested.

### P2 — `search.py` (26 statements, 0%)
NetBox search index registration. Untested.

### P2 — `template_content.py` (35 statements, 0%)
Template content injection hooks. Untested.

### P3 — `navigation.py`, `urls.py` (8 statements combined, 0%)
Navigation menu and URL routing. Low complexity but untested.

---

## Modules With Good Coverage

| Module | Coverage | Notes |
|---|---|---|
| `choices.py` | 100% | All choice enums exercised |
| `compliance.py` | 100% | Compliance engine fully tested |
| `crypto.py` | 98% | Encryption/decryption tested (1 edge case at line 74) |
| `diff.py` | 92% | Snapshot diff logic well tested |
| `testbed.py` | 91% | Dynamic testbed builder well tested |
| `capture.py` | 80% | Snapshot capture mostly tested; gaps in error paths (lines 332-369) |

---

## Integration & Compatibility Gaps

Beyond per-module coverage, the following test categories are **entirely missing**:

1. **No integration tests** — tests run against unit-level imports only; no Django test database, no HTTP request/response cycle.
2. **No NetBox version compatibility tests** — no matrix testing across NetBox 3.x/4.x.
3. **No RQ queue tests** — background job dispatch and queue behavior untested.
4. **No GraphQL endpoint tests** — `graphql/schema.py` has no test coverage.
5. **No end-to-end snapshot → diff → compliance pipeline test** — the full workflow is untested.

---

## Prioritized Recommendations

### P0 — Immediate (block release confidence)
1. **Add model-level tests** for `PyatsSnapshot`, `PyatsSnapshotDiff`, `ComplianceRun`, `PyatsJob` — field validation, save logic, nullable FK handling, model methods.
2. **Add job pipeline tests** for `jobs.py` — mock RQ queue, test dispatch, error handling, retry behavior.
3. **Add view tests** for `views.py` — use Django test client to exercise list/detail/edit/delete views.

### P1 — Near-term
4. **Add API tests** — serializers, viewsets, URL routing, filtering. Use Django REST Framework test client.
5. **Add form tests** — form validation, field choices, save behavior.
6. **Add table tests** — column rendering, sorting, pagination.

### P2 — Medium-term
7. **Add filter tests** — `filtersets.py` query parameter handling.
8. **Add GraphQL tests** — schema, resolvers, queries.
9. **Add search index tests** — `search.py` indexing.

### P3 — Long-term
10. **Add integration tests** — full HTTP stack against Django test database.
11. **Add NetBox compatibility matrix tests** — CI sweep across supported versions.
12. **Add end-to-end pipeline test** — snapshot capture → diff → compliance run.
13. **Cover remaining edge cases** in `capture.py` (lines 332-369), `crypto.py` (line 74), `diff.py` (lines 280-284).

---

## Test Run Output

```
106 passed, 8 skipped in 7.06s

TOTAL: 3256 statements, 2041 missing, 37% coverage
```

---

*Generated by QA Engineer audit — [ATW-95](/ATW/issues/ATW-95). Committed via [ATW-99](/ATW/issues/ATW-99).*