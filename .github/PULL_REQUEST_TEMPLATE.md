<!--
 PR body hygiene (ATW-159): do NOT paste Paperclip control-plane metadata
 into this public PR body. Specifically:
   - no `agent://<uuid>` URIs
   - no full agent UUIDs (8-4-4-4-12 hex) or 8-char ID prefixes
   - no internal org-role titles ("Chief of staff", "CTO", "QA Engineer",
     "Security Engineer", "Community Manager", "Senior Dev Engineer")
   - no Paperclip issue-thread verdict quotes that carry the above
 The CI lane `pr-body-scrub-guard` fails this PR if any are present.
 Reference reviewer/merger by role only ("reviewer: CTO", "merger: CEO") or
 omit those lines entirely — GitHub's reviewer-request UI is the assignment
 path. See docs/developer/contributing.md § "PR body hygiene".
-->

## Summary

<!-- What does this PR do and why? One or two sentences. -->

## Linked issue

- Closes #

## Changes

-

## Verification

- [ ] `black --check netbox_pyats` green
- [ ] `isort --check-only netbox_pyats` green
- [ ] `flake8 netbox_pyats` green
- [ ] Pure-Python tests green (`pytest netbox_pyats/tests/test_*.py`)
- [ ] (If model/view/API change) Integration suite green in the dev container

## Notes for reviewers

<!-- Architecture/scope notes only. No agent IDs, no internal role titles. -->