---
name: ci-cd
description: >-
  CI/CD regression loop for ADK agents via eval-workbench MCP: compare snapshots,
  map prompt deltas to failing cases, or run a full scored campaign on a new
  commit, then greenlight or block with cited case ids. Use when asked to check
  a commit for regressions.
---

# Skill: CI/CD Loop (outer — MCP)

Drive the eval workbench MCP server when you own the CI/CD regression loop.

Pair skill: `skills/loops_blueprint/ci-cd/SKILL.md` (inner loop via API).

For CSV interpretation, read `skills/eval_data_analysis/SKILL.md` before declaring
a verdict.

---

## Purpose (first principles)

CI/CD answers: **did this commit make the agent worse on the regression suite?**
A good outcome is a clear **greenlight** or **block** backed by case ids and,
when available, metric names — not a vague summary or an early stop after
`compare_snapshots` alone.

Two legitimate paths exist depending on what the task supplies.

---

## Scope

**In scope**

- Regression dataset cases tied to the agent under test
- Snapshot-to-snapshot comparison (`compare_snapshots`)
- Per-case run/score results and CSV export (`run_report`)
- Mapping manifest or prompt diffs to expected case failures

**Out of scope**

- Editing agent source (hand off to `skills/loops_mcp/harness-optimisation/SKILL.md`)
- Audit-style governance review (`skills/loops_mcp/audit/SKILL.md`)
- Declaring inconclusive when baseline, regression, and case inventory are all available

---

## Preconditions / IDs

**MCP connection**

```bash
python run_app.py <repo> --mode mcp
```

**Snapshot id** — use the full string everywhere:

```
{commit_hash}:{agent_python_path}:{python_var_name}
```

Copy ids verbatim from `list_snapshots` or `scan_agent`. A commit hash alone is
not a valid snapshot id and will break downstream tools.

Confirm both snapshots share the same `agent_python_path` and `python_var_name`
before comparing.

---

## Workflow

Choose **Path A** or **Path B** based on what the task provides.

### Path A — Pre-supplied baseline and regression snapshots

Use when baseline and candidate snapshot ids are already known (typical in skill
evals and prepared CI fixtures).

```
1. compare_snapshots(snapshot_a=BASE, snapshot_b=NEW)
2. get_snapshot(BASE) and get_snapshot(NEW)  — read manifest / prompt deltas
3. list_cases()                             — inventory the regression dataset
4. get_case(case_id)                        — for cases implicated by the diff
5. list_scored_runs / list_runs             — if scores already exist
```

**Mapping checklist**

- [ ] Read `compare_snapshots` output — note manifest and instruction changes
- [ ] List all cases in the regression dataset with `list_cases`
- [ ] For each functional case (non-audit), ask: could the observed diff break this scenario?
- [ ] Pull `get_case` for the most likely regressions — read conversation and metrics
- [ ] If scored runs exist, confirm bool metrics flipped on those cases
- [ ] Cite every regression as `case_id` + short reason + metric if known

**Verdict rules**

- **Block** when a manifest/prompt change plausibly breaks one or more functional
  cases — even without fresh runs, if the diff and case semantics align
- **Greenlight** when the diff is immaterial to all functional cases, or scored
  runs show no regressions
- **Inconclusive** only after the inventory pass leaves genuine ambiguity (e.g.
  conflicting scores, missing case bodies, snapshots for different agents)

Do not stop after step 1. `compare_snapshots` is the starting point, not the
deliverable.

### Path B — New commit, full campaign

Use when you must scan and score a fresh commit end-to-end.

```
1. list_snapshots                          — check before scanning
2. scan_agent(commit=NEW)                  — snapshot_id for NEW
3. get_snapshot(NEW)                       — confirm agent matches intent
4. list_cases()                            — regression dataset inventory
5. generate_run + evaluate_run             — per case (or create_campaign)
6. run_report                              — CSV for NEW
7. list_snapshots                          — resolve BASE snapshot id (full string)
8. compare_snapshots(snapshot_a=BASE, snapshot_b=NEW)
9. get_case / list_runs                    — drill into regressions
```

**Analysis checklist** (see eval_data_analysis for detail)

- [ ] Drop skipped CSV rows before aggregating
- [ ] Cast `result_value` by `result_type`
- [ ] Inspect individual regressed cases — not only aggregate means
- [ ] Re-run flaky cases 2–3× before treating a single failure as regression

---

## Stop condition

**Done** when you have issued an explicit verdict:

| Verdict | When |
|---|---|
| **Greenlight** | No material regressions on functional cases; diff is benign or scores held |
| **Block** | At least one functional case regressed or newly fails — cite `case_*` ids |
| **Inconclusive** | Genuinely ambiguous after Path A inventory or Path B re-run attempts |

A block or greenlight without cited case ids is incomplete.

---

## Report shape

```markdown
## CI/CD verdict — {NEW snapshot_id}

**Verdict:** Greenlight | Block | Inconclusive

### Snapshots
- Baseline: {full BASE id}
- Candidate: {full NEW id}

### Diff summary
(from compare_snapshots — prompt/manifest highlights)

### Case impact
| case_id | expected impact | evidence | metrics |
|---|---|---|---|
| case_bar | prompt weakened safety rule | get_case + diff alignment | on_topic: fail |

### Regressions
…

### Notes
(flaky re-runs, skipped rows, inconclusive rationale if applicable)
```

---

## Acting on results

| Verdict | Action |
|---|---|
| **Greenlight** | Report success; optionally note snapshot for merge |
| **Block** | Do not merge; surface regression summary with case ids. For fixes, hand off to harness optimisation |
| **Inconclusive** | Name what is missing (scores, case body, snapshot mismatch); re-run targeted cases before re-verdicting |

| Finding | Action |
|---|---|
| Prompt diff matches planted break | Block with cited cases — runs optional when diff + case semantics are clear |
| Aggregate mean shifted but cases pass | Greenlight — aggregates alone are insufficient to block |
| Missing BASE snapshot | `list_snapshots` filtered by agent path; scan baseline commit if needed |
| Truncated id caused tool error | Recover full id from `list_snapshots`; retry |
