# Screenshot Improvement Suggestions

**Issue:** ATW-879  
**Date:** 2026-08-13  
**Agent:** Vision Specialist (1da1937b-3007-4548-857e-546f37b851fc)

This document summarizes each documentation screenshot with one concrete improvement suggestion.

---

## 1. nav-pyats-menu.png
**Dimensions:** 2880 × 1800  
**Context:** Installation guide — shows the NetBox navigation menu with the PyATS/Genie top-level menu expanded

**Current content:** Full navigation menu showing seven plugin menu items under the PyATS/Genie umbrella

**Improvement suggestion:** Add callout annotations (numbered circles or arrows) pointing to the seven menu groups mentioned in the text ("Genie Tools, Credentials, Snapshots, Golden Configs & Compliance, Automation, Parser Catalog, and Jobs & Platforms") to help readers quickly map the prose to the visual.

---

## 2. credential-add-form.png
**Dimensions:** 1440 × 900  
**Context:** Installation guide Step 4 — shows the Add Credential form with device picker open

**Current content:** Form with device selection dropdown visible

**Improvement suggestion:** Blur or crop out unrelated form fields below the fold and add a red box around the device picker dropdown specifically, since that's what the caption emphasizes ("with the device picker open").

---

## 3. device-pyats-tab.png
**Dimensions:** 1440 × 1000  
**Context:** Installation guide Step 4 — shows the device detail page PyATS tab with capture button and recent snapshots list

**Current content:** Device page tab showing capture buttons and empty recent-snapshots list

**Improvement suggestion:** Add a green arrow pointing to the "Capture" button mentioned in step 3, and annotate the empty state message in the recent-snapshots list to set expectations for first-time users.

---

## 4. jobs-view.png
**Dimensions:** 1440 × 1000  
**Context:** Likely usage guide or troubleshooting — shows RQ jobs view

**Current content:** Job list view showing queued/running/completed jobs

**Improvement suggestion:** Add status badge legends (color-coded for success/error/running) and crop to show only the most relevant columns (Job ID, Status, Created, Result) to reduce cognitive load.

---

## 5. supported-platforms.png
**Dimensions:** 2880 × 2174  
**Context:** Troubleshooting or usage guide — shows the parser platform support matrix

**Current content:** Large table or list showing supported device platforms

**Improvement suggestion:** Group platforms by vendor (Cisco, Juniper, Arista, etc.) with collapsible sections or color-coded vendor headers, and add a "last updated" timestamp since parser support evolves.

---

## 6. compliance-run-drift.png
**Dimensions:** 783 × 1933 (tall, narrow)  
**Context:** Compliance guide — shows drift detection results

**Current content:** Long vertical view of compliance drift output

**Improvement suggestion:** This screenshot is too tall for comfortable viewing. Split into two logical sections: (1) summary header with pass/fail counts, and (2) detailed drift lines. Add callouts explaining the color coding (red = drift, green = compliant).

---

## 7. diff-viewer.png
**Dimensions:** 1565 × 1680  
**Context:** Usage guide — shows the diff viewer comparing two snapshots

**Current content:** Side-by-side or unified diff view

**Improvement suggestion:** Add a visual indicator showing which snapshot is "baseline" vs "current" (e.g., badges or color-coded headers), and annotate the line numbers or hunk markers for users unfamiliar with diff formats.

---

## 8. genie-diff-page.png
**Dimensions:** 2880 × 1800  
**Context:** Usage guide — shows the dedicated Genie Diff page

**Current content:** Full diff page UI with selectors and output

**Improvement suggestion:** Add numbered callouts for the three key UI regions: (1) snapshot selectors, (2) diff format toggle, (3) output area. This matches the workflow described in the usage guide.

---

## 9. genie-learn-page.png
**Dimensions:** 2880 × 1800  
**Context:** Usage guide — shows the Genie Learn page

**Current content:** Learn page UI with parsed output

**Improvement suggestion:** Highlight the "Learn" button and add a before/after annotation showing the raw CLI → structured data transformation, since "learn" is a Genie-specific concept that may be unfamiliar.

---

## 10. genie-parse-page.png
**Dimensions:** 2880 × 3510 (tallest screenshot)  
**Context:** Usage guide — shows the Genie Parse page with command catalog

**Current content:** Very tall page showing parser catalog and parse results

**Improvement suggestion:** This is the tallest screenshot (3510px). Split into two focused screenshots: (1) parser catalog with search/filter, (2) parse results with JSON/YAML output. Add a note about the scheduled parser-catalog refresh feature.

---

## Summary Statistics

| Screenshot | Dimensions | Primary Issue | Priority |
|------------|-----------|---------------|----------|
| nav-pyats-menu.png | 2880×1800 | No callouts for menu items | Medium |
| credential-add-form.png | 1440×900 | Focus not clear | Medium |
| device-pyats-tab.png | 1440×1000 | Action button not highlighted | Medium |
| jobs-view.png | 1440×1000 | Too many columns visible | Low |
| supported-platforms.png | 2880×2174 | No vendor grouping | Medium |
| compliance-run-drift.png | 783×1933 | Too tall, no color legend | High |
| diff-viewer.png | 1565×1680 | No baseline/current indicator | Medium |
| genie-diff-page.png | 2880×1800 | No UI region labels | Medium |
| genie-learn-page.png | 2880×1800 | "Learn" concept not explained | Medium |
| genie-parse-page.png | 2880×3510 | Too tall, unfocused | High |

---

## Recommended Next Steps

1. **High priority:** Re-capture `genie-parse-page.png` and `compliance-run-drift.png` as multiple focused screenshots
2. **Medium priority:** Add callout annotations to all screenshots using a consistent style (red boxes, numbered circles, arrows)
3. **Low priority:** Create a screenshot style guide for future documentation updates

---

**Related:** ATW-878 (vision-agent test) — this analysis can serve as test data for automated screenshot quality evaluation.
