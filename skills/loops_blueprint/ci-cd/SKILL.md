# Skill: CI/CD Loop (inner — blueprint)

Use this skill to run the CI/CD loop **inside** the eval workbench. The framework
instantiates a Google ADK agent from your blueprint and runs it to completion.

Pair skill: `skills/loops_mcp/ci-cd/SKILL.md` (outer loop via MCP).

---

## 1. What this loop does

Monitor a new commit: scan the agent, run and score cases, export a CSV report,
then compare against the previous commit snapshot. End with a **greenlight** or
**block** decision.

This loop is mostly `run_report` plus CSV analysis — see
`skills/eval_data_analysis/SKILL.md` for how to interpret the report output.

---

## 2. Run via API

**List presets** (optional):

```
GET /api/blueprints/presets
```

**Run a blueprint**:

```
POST /api/blueprints/run
Content-Type: application/json
```

### Option A — custom blueprint (recommended for CI/CD)

The calling LLM may edit `instruction` and `tools` before posting. Typical tool
set spans the preset building blocks Scanner → CaseRunner → CaseEvalRunner →
DataWriter, plus `compare_snapshots`:

```json
{
  "agent_name": "ci_cd_monitor",
  "model": "gemini-2.5-flash",
  "instruction": "You are a CI/CD monitor for an ADK agent.\n\nTools: scan_agent, generate_run, evaluate_run, run_report, compare_snapshots, get_snapshot, list_snapshots, list_cases, list_runs, list_scored_runs.\n\nDo the following until a greenlight/block decision is reached:\n1. scan_agent at the target commit\n2. generate_run + evaluate_run for the regression dataset\n3. run_report to produce a CSV\n4. compare_snapshots against the previous commit baseline\n5. Summarise regressions and declare greenlight (no material regressions) or block (regressions or new failures)\n\nExample sequence: scan_agent → generate_run → evaluate_run → run_report → compare_snapshots → final verdict.",
  "tools": [
    "scan_agent",
    "get_snapshot",
    "list_snapshots",
    "list_cases",
    "generate_run",
    "list_runs",
    "evaluate_run",
    "list_scored_runs",
    "run_report",
    "compare_snapshots"
  ]
}
```

### Option B — chain presets

Run presets sequentially if you prefer smaller agents:

1. `Scanner` — scan_agent at HEAD
2. `CaseRunner` — generate_run for each case
3. `CaseEvalRunner` — evaluate_run
4. `DataWriter` — run_report

Post each preset as a blueprint (fetch defaults from `/api/blueprints/presets`,
then override `instruction` if needed). A final custom blueprint with only
`compare_snapshots` can wrap the comparison step.

---

## 3. Stop condition ("until G")

**G** = you have a CSV report for the new commit, a snapshot comparison against
the previous commit, and a written **greenlight** or **block** verdict with
reasons (which cases/metrics regressed).

Do not greenlight from aggregate means alone — inspect individual regressions
per `skills/eval_data_analysis/SKILL.md` section 5.

---

## 4. Caller responsibilities

- Set the target commit/ref in tool args (via `scan_agent` / `run_report`).
- Tweak `instruction` to name the dataset, agent path, and regression policy.
- Read `BlueprintRunResult.final_output` and `tool_calls` from the response.
- This inner loop **reports**; it does not edit agent source code. For automated
  fixes, use the outer loop (`skills/loops_mcp/harness-optimisation/SKILL.md`).
