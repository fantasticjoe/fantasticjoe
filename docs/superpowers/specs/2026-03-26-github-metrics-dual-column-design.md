# GitHub Metrics Dual-Column 6-Card Design

## Summary

Reshape the GitHub Metrics section on the profile README into a strict 3-row, 2-column grid.

Keep the currently stable cards:
- `metrics-header.svg`
- `metrics-languages.svg`
- `metrics-isocalendar.svg`

Add three more stable cards so the section always renders as an even 6-card layout:
- `metrics-followup.svg`
- `metrics-topics.svg`
- `metrics-repositories.svg`

Do not keep `metrics-achievements.svg` in the layout because the upstream achievements plugin currently fails on deprecated GitHub Projects Classic fields and renders an error card instead of useful content.

## Goals

- Make the Metrics section feel balanced on a profile README
- Avoid odd-card layouts that leave a row with only one card
- Preserve the strongest existing cards and extend them with complementary information
- Keep the workflow on officially supported, currently stable `lowlighter/metrics` plugins

## Non-Goals

- Redesign the rest of the profile README
- Fork or patch `lowlighter/metrics`
- Restore the achievements plugin in this change

## Card Set

The final six cards will be:

1. `header`
2. `languages`
3. `isocalendar`
4. `followup`
5. `topics`
6. `repositories`

## Layout

README layout will use a fixed 3x2 table:

- Row 1: `header` | `languages`
- Row 2: `isocalendar` | `followup`
- Row 3: `topics` | `repositories`

Each cell will stay at `width="50%"` so the section remains symmetrical.

## Workflow Changes

Update `.github/workflows/metrics.yml` to:

- Keep existing `header`, `languages`, and `isocalendar` jobs
- Remove the broken `achievements` job
- Add new jobs for `followup`, `topics`, and `repositories`

Each new job should:

- use `lowlighter/metrics@latest`
- write a dedicated SVG file
- keep `contents: write`
- use the existing `METRICS_TOKEN`
- use `config_timezone: Asia/Shanghai`
- set `base: ""` so each card stays focused

Recommended plugin intent:

- `followup`: show issue and pull request follow-up activity
- `topics`: show starred topics in `labels` mode so the card reads clearly in a README grid
- `repositories`: show pinned repositories instead of generic featured repositories so the card reflects the profile's curated public work

Recommended plugin choices:

- `topics`
  - `plugin_topics: yes`
  - `plugin_topics_mode: labels`
  - `plugin_topics_limit`: keep within the default or a small fixed count if needed for readability
- `repositories`
  - `plugin_repositories: yes`
  - `plugin_repositories_pinned`: use a small pinned count suitable for one card
  - do not mix pinned, random, and starred repository modes in this change

## Content Balance

The six-card set should read as:

- overview: `header`
- technical stack: `languages`
- contribution rhythm: `isocalendar`
- collaboration/workflow: `followup`
- interests/domain signals: `topics`
- representative work: `repositories`

This keeps the section varied and avoids stacking too many cards that all describe time-based activity.

## Error Handling

- If any of the new cards produce poor or noisy output, prefer narrowing plugin options rather than adding more cards
- The broken achievements card should be fully removed from the README so profile visitors never see the upstream error state

## Verification

After implementation:

1. Run the Metrics workflow manually
2. Confirm all six jobs succeed
3. Confirm new SVG files are present in the target branch/repo
4. Re-read the README table to verify it contains exactly three rows and six images
5. Inspect generated cards for obvious duplication or empty output
