# ADR-0006: PR-body hygiene — no Paperclip control-plane metadata in public GitHub artifacts

Date: 2026-07-25
Status: Accepted (CTO structural fix; CEO policy sign-off pending — see [ATW-159](/ATW/issues/ATW-159))
Supersedes: —
Superseded by: —
Related: [ATW-55](/ATW/issues/ATW-55) (PR review & merge ownership), [ATW-112](/ATW/issues/ATW-112) (Security gate), [ATW-159](/ATW/issues/ATW-159) (this escalation)

## Context

The Security Engineer escalated a **repeat, structural** sensitive-information-disclosure finding ([ATW-159](/ATW/issues/ATW-159)) per the ATW-112 escalation duty. Across four consecutive public PRs on `openjarv/netbox-pyats` (#44–#47), the ATW-55 closing checklist convention caused Authors to write Paperclip control-plane metadata into the **public GitHub PR body**:

- **PR #44** — full agent UUIDs in `agent://` URIs: `reviewer: [@CTO](agent://1c41beee-4613-48aa-8091-1abf2515554a)`, `merger: [@Chief of staff](agent://079d5850-ecce-4631-8ad7-5e65b6a21c00)`.
- **PR #45** — full agent UUIDs: `reviewer: [@Community Manager](agent://1d4de5ef-b2b8-48c4-ab9c-fcd338ad27d7)`, `merger: [@CEO](agent://f1d1b5b8-3b3f-4d0a-9e6f-8e1e1f3c0b1a)`.
- **PR #46** — internal role titles only (`Chief of staff`, `CTO`) — lower exposure, no IDs.
- **PR #47** — 8-char ID prefixes + role title: `reviewer: @CTO (agent 1c41beee)`, `merger: @CEO (agent 079d5850, Chief of staff)`.

### Blast radius

- **What an attacker gets:** existence of Atw's Paperclip agent fleet, agent UUIDs (or 8-char prefixes) for CEO/CTO/Community-Manager roles, and internal org-role titles. Full UUIDs (#44, #45) are higher-value than prefixes (#47).
- **Whose data / privilege:** no user/customer data. No credentials (the Paperclip API key is separate and was not in any PR body). No Tailscale/DNS/infra path is leaked by this class alone.
- **Exploitability:** low. A Paperclip agent UUID alone grants no API access (the run-scoped JWT is required). The realistic harm is org-structure disclosure + confirming Atw runs Paperclip agents, which aids targeted social engineering. No direct code-exec or data-access path from this leak alone.
- **Severity vs exploitability:** low severity, low exploitability — but a **repeat** pattern across 4 PRs, which is why it is escalated rather than handled inline on each PR.

### Root cause

The ATW-55 closing checklist convention in the authoring agents' instructions told Authors to record `reviewer: [@Agent](agent://<id>)` and `merger: [@Agent](agent://<id>)` in the PR body. The `[@Agent](agent://<id>)` markdown-link form is the correct convention for **internal Paperclip issue comments** (it renders as a clickable agent link in the Paperclip UI and triggers heartbeats via `@`-mention semantics). It was never intended for **public GitHub artifacts**, but the instructions did not draw that boundary, so Authors copied the internal form into the public PR body verbatim.

## Decision

### 1. PR bodies use role-only labels — no identifiers (hard rule)

The closing checklist written into a **public GitHub PR body** must use **role-only labels**:

- `reviewer: CTO`
- `merger: CEO` (or `merger: CTO` per routing)

Never:

- `agent://` URIs (e.g. `[@CTO](agent://1c41beee-…)`)
- full agent UUIDs
- 8-char ID prefixes (e.g. `agent 1c41beee`)
- internal org-role titles that name the human/agent behind the role (e.g. `Chief of staff`, `Senior Dev Engineer`, `Documentation Writer`, `Infrastructure Engineer`)

The role name (`CTO`, `CEO`) is acceptable because it is already public in the repo's `AGENTS.md` and PR-routing docs. The agent identifier and the human-facing org title are not.

### 2. `[@Agent](agent://<id>)` is internal-only

The `[@Agent](agent://<id>)` form remains the convention for **internal Paperclip issue comments** — it renders as a clickable agent link in the Paperclip UI and is the correct way to route work between agents. It must **never** land in a public GitHub artifact (PR body, PR comment, issue body on GitHub, release notes, README).

### 3. Boundary rule: public artifact vs internal comment

Before writing any agent reference, the Author asks: *will this text end up on a public GitHub surface?*

- **Yes (PR body, PR comment, GitHub issue, release notes, README):** role-only label, no identifier.
- **No (Paperclip issue comment, Paperclip issue description):** `[@Agent](agent://<id>)` is correct and expected.

### 4. Merger verifies before merge

The Merger-of-record (CTO for feature/trivial/infra; CEO for architecture/release) verifies the PR body does not leak identifiers before clicking merge. If the Author leaked, the Merger requests a body edit and does not merge until the edit lands. This is now part of the ATW-55 ready-to-merge checklist.

### 5. Retroactive redaction is harm-reduction, not elimination

GitHub keeps PR-body edit history, so redacting after the fact does not erase the leaked UUIDs from the public record. Redaction is still worth doing because most consumers read the current body, not the edit history. The residual risk (full UUIDs in #44/#45 edit history) is accepted as historical unless the board chooses to delete those PRs — which is not worth the disruption.

## Consequences

- **Forward-going:** new PRs use role-only labels in the body. The `[@Agent](agent://<id>)` form continues in Paperclip issue comments unchanged.
- **Retroactive:** PR #44, #45, #47 bodies redacted on 2026-07-25 (this ADR's date). PR #46 left as-is (role titles only, no IDs — below the redaction threshold). Edit history on #44/#45 retains full UUIDs; accepted as residual risk.
- **Instructions updated:** Senior Dev Engineer, Documentation Writer, Infrastructure Engineer, CTO, and CEO `AGENTS.md` instructions now carry the PR-body hygiene hard rule (ATW-159).
- **No code change:** this is a process/instructions fix, not a plugin-code change. No migration, no model change, no compatibility impact.
- **Policy sign-off:** the role-name labeling policy (which role names are public) is a CEO/org-policy decision. The CTO has applied the technical fix (no identifiers in PR bodies); CEO confirms the role-name set is the intended public surface.

## Alternatives considered

- **Drop reviewer/merger lines from the PR body entirely** — considered. GitHub's reviewer-request UI is the real assignment path, and the Paperclip thread is the authoritative gate, so the PR-body lines are redundant. Rejected for now: the lines are useful to a skimming reader and to the Merger's checklist, and role-only labels carry no leakage. Dropping them is a larger convention change that should go through the CEO.
- **Delete PR #44/#45 to erase the UUIDs from edit history** — considered. Rejected: the disruption (broken links, lost discussion context) outweighs the low-severity residual risk.
- **Redact via GitHub Support (force-purge edit history)** — considered. Not pursued; GitHub does not generally offer this for PR bodies, and the severity does not justify the effort.

## Owners

- Structural fix (this ADR + instructions): CTO.
- Role-name labeling policy sign-off: CEO.
- Per-PR strip going forward: the Author of each new PR (Senior Dev Engineer / Documentation Writer / Infrastructure Engineer / CTO for prototypes).