# Architecture Decision Records

ADRs are short, dated records of structural decisions that are expensive to reverse. Every structural change to the plugin (layout, patterns, integration contracts) gets an ADR here. ADRs are linked from the relevant code and from the [architecture overview](https://github.com/openjarv/netbox-pyats) tracked on [ATW-23](/ATW/issues/ATW-23).

## Status legend

- **Accepted** — in effect; follow it.
- **Superseded** — replaced by a later ADR; keep for history.
- **Amended** — still in effect with a follow-up ADR modifying specific points.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [0001](0001-plugin-layout.md) | Plugin package layout | Accepted | 2026-07-19 |
| [0002](0002-graceful-degradation.md) | Multi-vendor graceful degradation pattern | Accepted | 2026-07-19 |
| [0003](0003-netbox46-migration-and-worker-toolchain.md) | NetBox 4.6 migration dependencies and worker build toolchain | Accepted | 2026-07-19 |
| [0004](0004-compliance-golden-parse-shape.md) | Compliance golden-config comparison shape | Accepted | 2026-07-21 |

## When to write an ADR

- Any structural change to the package layout (ADR-0001).
- Any new background-work pattern or status vocabulary change (ADR-0002).
- Any new model whose storage/diff strategy is non-obvious (e.g. compliance model, golden config storage — upcoming ADR-0003).
- Any new release-process or compatibility-matrix decision (D-7 CI, D-8 release).
- Any decision that would be expensive to reverse after the community depends on it.

## When NOT to write an ADR

- A new supported platform slug (edit `PLATFORM_SLUG_TO_PYATS_OS`; no ADR).
- A new field on an existing model that does not change storage shape or status semantics.
- A bug fix or refactor that does not change the structural contract.

## Format

Each ADR has: Context, Decision, Consequences, Alternatives considered, References. Keep them short — assume the reader is skimming.