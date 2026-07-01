---
name: Agent Evaluation & Provenance Workbench
# Resolved design tokens (from the Stitch "Workbench — Lab Instrument" design system,
# asset assets/9802665030210198722, project 6491290619762269673). Feed these into the
# Tailwind theme in frontend/. This file owns APPEARANCE; contracts/web_frontend.md owns STRUCTURE & BEHAVIOUR.
colorMode: dark
seed: '#7C5CFF'
colorVariant: TONAL_SPOT
roundness: 8px
fonts:
  headline: Space Grotesk
  body: Inter
  mono: JetBrains Mono
# Material-derived palette resolved by Stitch:
colors:
  background: '#0c0e13'
  surface: '#0c0e13'
  surface-dim: '#0c0e13'
  surface-bright: '#282c37'
  surface-container-lowest: '#000000'
  surface-container-low: '#11131a'
  surface-container: '#161921'
  surface-container-high: '#1c2028'
  surface-container-highest: '#212630'
  surface-variant: '#212630'
  on-surface: '#e2e5f3'
  on-surface-variant: '#a7abb8'
  outline: '#717582'
  outline-variant: '#444853'
  primary: '#cabeff'
  primary-fixed: '#7c5cff'      # the brand indigo/violet
  primary-container: '#542bd6'
  on-primary: '#4100c5'
  on-primary-container: '#e7dfff'
  secondary: '#bec7d8'
  secondary-container: '#333c4a'
  tertiary: '#ff85a2'
  error: '#f97386'
  error-container: '#871c34'
  on-error-container: '#ff97a3'
# Domain-semantic colors (NOT part of the Material palette — enforce these ourselves):
semantic:
  pass: '#31C48D'        # bool true / verified
  fail: '#F5698E'        # bool false
  margin: '#F6A609'      # domain_position == margin ; also caller-error
  ood: '#7A8393'         # domain_position == ood ; neutral
  info: '#7C5CFF'        # indigo primary
  # blame taxonomy (scanner/runner errors):
  caller-error: '#F6A609'      # amber — the operator called us wrong
  agent-error: '#F5698E'       # rose — the agent-under-test is at fault
  framework-error: '#C24BFF'   # violet-magenta — our bug
typography:
  headline-lg: { fontFamily: Space Grotesk, fontSize: 24px, fontWeight: '600', lineHeight: 32px }
  body-md:     { fontFamily: Inter, fontSize: 13px, fontWeight: '400', lineHeight: 20px }
  mono-sm:     { fontFamily: JetBrains Mono, fontSize: 12px, fontWeight: '400', lineHeight: 16px }
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  full: 9999px
---

# Agent Evaluation & Provenance Workbench — Design System

> Source of truth for **appearance**. For pages, flows, and behaviour see `contracts/web_frontend.md`.
> Live mockups (viewable in Stitch, project `6491290619762269673`): agent-lineage view generated; see the mockup log at the bottom.

## Product & mood
A local, single-operator **lab instrument** for evaluating AI agents: reproducible, inspectable, honest. A precision scientific tool / observability console, **not** a marketing site. Dark, calm, data-dense, high signal-to-noise. No hero sections, no illustrations, no marketing pills. Think Linear × a spectrum analyzer × a git client.

## Color
- **Dark mode only.** Canvas is the deepest layer (`#0B0D12`/`#0c0e13`), panels sit above (`#12151C`/`#161921`), raised surfaces (`#1A1E27`/`#1c2028`). Thin low-contrast borders (`#242A36`/`outline-variant`) define the grid.
- **Primary** electric indigo/violet (`#7C5CFF`) used **sparingly** — active/selected state, primary action, graph-node highlight. Everything else neutral so data reads first.
- **Semantic outcome colors** (consistent everywhere): pass/true = emerald `#31C48D`, fail/false = rose `#F5698E`, warning/margin = amber `#F6A609`, neutral/ood = slate `#7A8393`, info = indigo.
- **Blame taxonomy colors** (scanner/runner errors, from the error taxonomy in the contracts): caller-error = amber (operator's fault), agent-error = rose (agent-under-test's fault), framework-error = violet-magenta (our bug). Must be visually distinct **and** labeled.
- **Split badges (SOUL13):** `optimisation` = teal outline; `judging` = a locked/sacred violet solid badge — judging must *look* protected.

## Typography
- Headline: **Space Grotesk**. Body: **Inter**. Mono: **JetBrains Mono** for ALL machine values — commit hashes, fingerprints, ids, model ids, code/prompt/tool source, latencies, token counts, matrix cells. Machine data is always monospace.
- Compact scale: body 13–14px, tight table rows, muted-grey mono metadata.

## Shape & density
- 8px corner radius on cards/inputs; subtle buttons (not pills). **1px borders over shadows**, minimal elevation — border + slight bg lift instead of drop shadows.
- Data-dense: compact tables with monospace numeric columns, tight vertical rhythm, sticky headers.

## Layout
- **App shell:** persistent **left rail** — repo + `AgentTarget` context switcher at the top, then nav (Agents, Snapshots, Cases, Runs, Campaigns, Compare, Registries, Chat). Routed content pane to the right. A **jobs tray** shows async scan/run/campaign progress. **No top marketing navbar.**

## Signature components
- **Agent/lineage graph** — node-link DAG on the dark canvas; selected node glows indigo; a detail drawer shows fingerprints + source.
- **Commit DAG** — vertical git-graph of snapshots; pick two → Compare.
- **Trace viewer** — a rendered **conversation** (never JSON): user/assistant/tool bubbles, `tool_call`/`tool_response` as framed blocks, a crash as a red exception card (a crash is a valid scorable outcome); latency + tokens in mono.
- **Response-matrix heatmap** — models × cases, green→red cells, side panels for item difficulty, model ability, co-failure clusters, thinning suggestions.
- **Result chips** — bool as pass/fail pill, enum as chip, int/float as value + fold stats.
- **Confirm cards** — any write/expensive action (scan, run, launch campaign, delete, freeze) confirms effects before executing; reads are instant.
- **Editors, never raw JSON** — cases, metrics, rubrics (frozen = read-only + "new version"), extractors (fingerprinted source + run-on-sample preview), tags (delete only if unused).
- **Empty states** — every list names the action that fills it (e.g. "No agents yet — Add a repository").

## Voice
Terse, technical, exact. Real domain names (snapshot, trace, rubric, campaign, split). No emoji, no exclamation, no cutesy copy.

## Mockup log (Stitch project `6491290619762269673`, design system `assets/9802665030210198722`)
Ten reference screens live under `specs/design/mockups/`, one folder each with a `screen.png` (render) and `code.html` (Stitch's static HTML — a structural reference to extract into React/TS, **not** production code). Each maps to a page in `contracts/web_frontend.md`:
- `mockups/01_add_target_scan_onboarding/` — Add target & scan (page 1)
- `mockups/02_agent_lineage/` — Agent lineage & provenance view (page 2)
- `mockups/03_eval_case_builder/` — Eval-case builder, domain × problem (page 3)
- `mockups/04_trace_viewer_scoring/` — Trace viewer + scoring (page 4)
- `mockups/05_compare_snapshot_diff/` — Compare: aggregate diff + validity guard + semantic diff (page 5)
- `mockups/06_campaign_response_matrix/` — Campaign response-matrix / IRT (page 6)
- `mockups/07_registries_rubrics_frozen/` — Registries → Rubrics editor, frozen state (page 7)
- `mockups/08_extractor_authoring/` — Extractor authoring, AGENT4 draft→run→confirm (page 7)
- `mockups/09_human_evaluation/` — Human evaluation + agreement (page 8)
- `mockups/10_chat_operator/` — Chat operator + action-proposal confirm cards (page 9)
