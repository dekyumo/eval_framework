# Skill: CI/CD Loop (outer — MCP)

Use this skill when **you** (the autonomous coding agent) own the CI/CD loop.
Drive the eval workbench through its stdio MCP server instead of delegating to
an in-framework blueprint.

Pair skill: `skills/loops_blueprint/ci_cd/SKILL.md` (inner loop via API).

---

## 1. Connect to MCP

From the eval_framework repo root:

```bash
python run_app.py <repo> --mode mcp
```

Register the server in your MCP client (Cursor, Claude Code, Codex, etc.) as a
stdio process. All tools share the registry in `mcp/registry.py`.

---

## 2. What this loop does

Monitor a new commit: scan → run → score → export CSV → compare to baseline →
greenlight or block. Analysis of the CSV follows
`skills/eval_data_analysis/SKILL.md` — read that skill before declaring a
verdict.

---

## 3. Tool sequence

Typical sequence for commit `NEW` against baseline `BASE`:

```
1. scan_agent          → snapshot_id for NEW
2. get_snapshot        → confirm agent description matches intent
3. list_cases          → cases in the regression dataset
4. generate_run        → one run per case (repeat)
5. evaluate_run        → score each run (repeat)
6. run_report          → CSV path for NEW
7. list_snapshots      → find BASE snapshot_id
8. compare_snapshots   → {snapshot_a: BASE, snapshot_b: NEW}
9. get_case / list_runs → drill into regressions (see eval_data_analysis §5)
```

`run_report` wraps the headless benchmark CLI; the CSV it produces is the
primary artefact for commit comparison.

---

## 4. Stop condition ("until G")

**G** = CSV exported, `compare_snapshots` reviewed, and you have issued an
explicit **greenlight** or **block** with cited case/metric regressions.

Rules:
- Drop skipped rows; cast `result_value` by `result_type` (eval_data_analysis §1–2).
- Never trust aggregate deltas without reading traces for regressed cases.
- Re-run flaky cases 2–3× before treating a single failure as a regression.

---

## 5. Where you act on results

| Verdict | Action |
|---|---|
| **Greenlight** | Report success; optionally tag the snapshot or open a merge note. No code edits required. |
| **Block** | Do **not** merge. Surface the regression summary. If the user wants fixes, hand off to `skills/loops_mcp/harness_optimisation/SKILL.md`. |
| **Inconclusive** | Re-run the failing cases or widen the comparison window before deciding. |

This loop is intentionally thin — most intelligence lives in CSV analysis
(`skills/eval_data_analysis/SKILL.md`), not in bespoke loop logic.
