# Skill: Harness Optimisation Loop (inner — blueprint)

Use this skill to analyse failing test cases and produce improvement guidance
**inside** the eval workbench.

Pair skill: `skills/loops_mcp/harness-optimisation/SKILL.md` (outer loop via MCP).

---

## 1. What this loop does

For each failing case in the latest eval run:

1. Inspect the case definition, run trace, and judge rationale.
2. Write a ~100-word blurb on what should be improved (agent prompt, tool use,
   harness, or case definition).
3. Summarise patterns across failures.
4. Surface the summary for **human review** — this inner loop does not edit code.

After fixes (by a human or outer-loop coding agent), re-run the test suite to
confirm improvement.

---

## 2. Run via API

```
POST /api/blueprints/run
Content-Type: application/json
```

The calling LLM may edit `instruction` and `tools` before posting:

```json
{
  "agent_name": "harness_optimiser",
  "model": "gemini-2.5-flash",
  "instruction": "You are a harness optimisation analyst.\n\nTools: list_scored_runs, list_runs, get_case, get_snapshot, list_cases, evaluate_run.\n\nDo the following until an optimisation brief is complete:\n1. list_scored_runs for the latest snapshot — identify failing cases (bool metrics with result_value=false, or numeric below threshold)\n2. For each failing case: get_case + inspect run trace — write a ~100-word blurb on the root cause and what to improve\n3. Summarise common failure patterns across blurbs\n4. Output a single optimisation brief for a coding agent or human\n\nDo not edit agent source code. Watch the test suite by noting which cases must pass after fixes.\n\nExample sequence: list_scored_runs → get_case (failing) × N → summarise → optimisation brief.",
  "tools": [
    "get_snapshot",
    "list_cases",
    "get_case",
    "list_runs",
    "list_scored_runs",
    "evaluate_run"
  ]
}
```

`CaseEvalRunner` preset is a useful starting point if you prefer presets.

---

## 3. Stop condition ("until G")

**G** = every failing case has a ~100-word blurb, patterns are summarised, and
an optimisation brief is written listing concrete changes and the cases that
must pass on re-run.

---

## 4. Caller responsibilities

- Specify which snapshot/dataset defines "failing" (latest scored runs by default).
- Read `BlueprintRunResult.final_output` and hand the brief to a human or to the
  outer loop (`skills/loops_mcp/harness-optimisation/SKILL.md`) for code changes.
- Re-invoke the CI/CD loop after fixes to confirm regressions are resolved.
