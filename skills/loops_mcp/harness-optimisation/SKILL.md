---
name: harness-optimisation
description: >-
  Harness optimisation loop via eval-workbench MCP: analyse failing scored runs,
  propose agent code fixes, re-scan and re-run until the suite improves. Use when
  asked to fix an agent from eval failures.
---

# Skill: Harness Optimisation Loop (outer — MCP)

Use this skill when **you** (the autonomous coding agent) own the harness
optimisation loop — analyse failures, edit agent code, and re-run the suite.

Pair skill: `skills/loops_blueprint/harness-optimisation/SKILL.md` (inner loop via API).

---

## 1. Connect to MCP

If the MCP is not connected, launch it or add it to the host configuration

Simple command:
```bash
python run_app.py <repo> --mode mcp
```

More complex:
```bash
$PYTHONPATH=<app_dir>\src conda.bat run --no-capture-output -n <env_name> python <app_dir>\run_app.py --mode mcp <repo>
```

Stdio server; repo path from `EVAL_WORKBENCH_REPO` (defaults to CWD).

---

## 2. What this loop does

1. Find failing cases in the latest scored runs.
2. For each failure, write a ~100-word blurb (root cause + proposed fix).
3. Summarise patterns.
4. **Edit agent source code** in the repo to address the patterns.
5. Re-scan, re-run, and re-score — watch the test suite until failures shrink
   or you hit a stop condition.

---

## 3. Tool sequence

**Analyse:**

```
1. list_snapshots       → latest snapshot_id
2. list_scored_runs     → identify failures
3. get_case             → case definition (repeat per failure)
4. list_runs            → run_id for failed case
5. get_snapshot         → agent description at time of failure
```

**Fix and verify:**

```
6. [edit agent code in repo — your normal coding tools, not MCP]
7. scan_agent           → new snapshot after edits
8. generate_run         → re-run failing cases (repeat)
9. evaluate_run         → re-score (repeat)
10. list_scored_runs    → confirm failures resolved
```

Optionally `run_report` for a full CSV comparison per
`skills/eval_data_analysis/SKILL.md`.

---

## 4. Stop condition ("until G")

**G** = either:

- All previously failing cases now pass on re-run, **or**
- You have completed one optimisation iteration and documented remaining
  failures with blurbs (user may cap iterations).

Do not iterate directly on individual failing cases in isolation — fix the
**pattern** (see eval_data_analysis §7, Goodhart's Law). Re-run the full
failing set after each code change.

---

## 5. Where you act on results

| Phase | Action |
|---|---|
| Analyse | Write ~100-word blurbs; summarise patterns in your working notes. |
| Fix | Edit agent prompt, tools, or harness code in the ADK agent repo. |
| Verify | `scan_agent` → `generate_run` → `evaluate_run` on failing cases. |
| Regress | If new failures appear, stop and report — do not silently overwrite fixes. |

Hand off to `skills/loops_mcp/ci-cd/SKILL.md` for a full commit comparison once
the failing set is green.
