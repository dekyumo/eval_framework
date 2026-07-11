---
name: eval-framework-mcp
description: >-
  Use the eval_framework MCP server (eval-workbench) to scan agents, build
  datasets and cases, run traces, score them, and launch campaigns. Use when
  working with eval-workbench MCP tools, run_app.py --mode mcp, or eval case
  registries in eval_framework_df.
---

# Eval Framework MCP

Use this skill when **you** drive the eval workbench through its MCP server —
not the inner blueprint loops (`skills/loops_mcp/*`), but the day-to-day happy
path: scan → registry → cases → runs → scores → campaign.

---

## 1. Connect the MCP server

The server is a **stdio** JSON-RPC process. Anything that captures or buffers
**stdout** breaks the handshake (`Connection closed`).

```json
{
  "command": "C:\\path\\to\\conda.bat",
  "args": [
    "run",
    "--no-capture-output",
    "-n",
    "eval_framework",
    "python",
    "C:\\path\\to\\eval_framework\\run_app.py",
    "--mode",
    "mcp",
    "C:\\path\\to\\agent_repo"
  ],
  "env": {
    "PYTHONPATH": "C:\\path\\to\\eval_framework\\src"
  }
}
```

Notes:

- **`--no-capture-output`** on `conda run` is required (conda otherwise swallows
  stdout).
- **`PYTHONPATH`** must point at the `src` folder (module root is `src`, imports
  are `from src.eval_workbench...`). Alternative: set `cwd` to `src` and invoke
  `..\run_app.py`.
- The **repo path** is the positional argument to `run_app.py` — the git repo
  that holds agent code **and** the Kuzu eval database (often `eval_framework_df`).
- Register in global or project MCP config; restart the MCP client after edits.

Quick smoke test once connected: call `list_datasets` or `list_snapshots`.

---

## 2. ID conventions (not obvious from tool names)

| Object | ID format | You supply it? |
|---|---|---|
| **Snapshot** | `{commit_hash}:{agent_python_path}:{python_var_name}` e.g. `c97928…:a_single_agent.day_trip:root_agent` | No — returned by `scan_agent` |
| **Case** | e.g. `case_ew_in01` | **Yes** — pick a stable string |
| **Dataset** | e.g. `ds_eval_writer_cases` | **Yes** |
| **Tag** | slug from name if omitted | Optional (`create_tag` can derive from `name`) |
| **Rubric** | e.g. `rubric_accef63c` | **Yes** |
| **Extractor** | e.g. `ext_latency` | **Yes** |
| **Run** | `{dataset}-{case}-{agent}_{commit}_{model}-{hash}` | No — returned by `generate_run` |
| **Scored run** | `scored_{run_id}` | No — returned by `evaluate_run` |
| **Campaign** | e.g. `campaign_a1b2c3d4` | **Yes** |

`agent_path` is the ADK import path: `package.module:root_agent` (colon separates
module from variable).

Always **`list_*` after `create_*`** to confirm persistence and capture the IDs
you will need in later steps.

---

## 3. Object relationships

```
scan_agent → snapshot (fixed agent code + manifest + distribution)
                ↓
create_dataset ← create_case (dataset_id required — links case into exactly one dataset)
create_rubric / create_extractor / create_tag
                ↓
generate_run(snapshot_id, case_id, model_id) → run (+ trace)
                ↓
evaluate_run(run_id) → scored run (rubric / extractor / verifier metrics)
                ↓
create_campaign(dataset + snapshot + model_panel) → runs all cases × models,
                scores them, then get_campaign_matrix → ability of model & difficulty of case
```

- **`snapshot_id`** always refers to the **agent under test**, not the eval
  workbench internal agents (case_writer, extractor_author, …) unless you are
  deliberately evaluating those.
- Cases are run against whichever **snapshot** you select at run time (`generate_run`).
- Cases reference rubrics via `metrics[].rubric_ref` (and extractors via
  `extractor_ref`).

---

## 4. Happy path (tool sequence)

### 4a. Scan the agent under test

```
scan_agent(agent_path="a_single_agent.day_trip:root_agent", commit="HEAD")
→ note snapshot["id"]
get_snapshot(snapshot_id)   # optional: read manifest + distribution
```

### 4b. Registry setup

```
list_tags / list_datasets / list_rubrics     # inventory first

create_tag({ "name": "cases_about_llamas", "color": "#4ade80" })
create_rubric({
  "id": "rubric_daytrip_ontopic",
  "name": "IsDaytripOnTopic",
  "instructions": "…",
  "items": [{ "name": "on_topic", "type": "float", "prompt": "Evaluate whether the assistant answer is on topic on a scale of 0 to 100" }],
  "default_judge_prompt": "Evaluate: {instructions}",
  "judge_model_id": "gemini-2.5-flash",
  "version": 1,
  "fingerprint": "manual"
})
create_dataset({ "id": "ds_daytrip", "name": "DayTrip Tests", "case_ids": [] })
```

### 4c. Create eval cases

**Manual** (full control):

```
create_case({
  "id": "case_seoul_day",
  "name": "Seoul day trip",
  "dataset_id": "ds_daytrip",
  "conversation": [{ "role": "user", "kind": "text", "text": "Plan a day in Seoul" }],
  "distribution_position": "in",
  "problem_type": "happy",
  "split": "test",
  "source": "manual",
  "metrics": [{
    "id": "m_seoul",
    "name": "quality",
    "strategy": "rubric",
    "result_type": "float",
    "rubric_ref": "rubric_daytrip"
  }]
}, dataset_id="ds_daytrip")
```

**AI-assisted draft** (case_writer agent inside the framework):

```
generate_case(snapshot_id, "happy-path case: plan a day in Seoul with $200 budget")
→ returns draft dict (conversation, problem_type, …)
→ edit if needed, then create_case({ ...draft, "id": "case_…", "dataset_id": "ds_…" })
```

`generate_case` needs a **stored snapshot** of the target agent and a non-empty
`specification` string.

### 4d. Run traces

```
generate_run(snapshot_id, case_id, model_id="gemini-2.5-flash")
→ returns run dict with trace; idempotent unless force=true

# repeat per case, or use create_campaign for batch
list_runs()
```

### 4e. Score runs

```
evaluate_run(run_id)
list_scored_runs()
```

Each case's `metrics` define what gets scored (rubric, deterministic extractor,
or verifier).

### 4f. Campaign → model ability & case difficulty

```
create_campaign({
  "id": "campaign_abc12345",
  "name": "Flash vs Flash-Lite",
  "dataset_id": "ds_daytrip",
  "base_snapshot_id": "<snapshot_id>",
  "model_panel": ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
  "created_at": <unix_seconds>
})
# runs every case in dataset × every model, scores each

get_campaign_matrix(campaign_id)
→ cell["model_id|case_id"] scores
→ difficulty[case_id], ability[model_id]  (IRT-style regression)
```

---

## 5. Case fields cheat sheet

| Field | Values / notes |
|---|---|
| `distribution_position` | `in`, `margin`, `ood` — coverage of **this case** |
| `problem_type` | `happy`, `technical`, `adversarial`, `client` |
| `split` | `train` (optimisation) or `test` (judging) |
| `conversation` | list of `{ role, kind: "text", text }` turns |
| `session_state` | injected into ADK session before run — **see §6** |
| `metrics[].strategy` | `rubric`, `deterministic`, `verifier` |

Use **either** `conversation` **or** `input_payload`, not both.

---

## 6. `session_state` — when it matters

For **normal** eval cases (trip planner, refund bot, …): leave
`session_state` null. The case conversation is the agent input.

The `{snapshot}` / `{user_specification}` pattern in `session_state` is a
**quirk of evaluating the internal `case_writer` agent** — that agent reads
those keys from session state to generate cases for *other* agents. Do **not**
assume every case needs a snapshot JSON in `session_state`.

---

## 7. Read-only vs write tools

**Read:** `list_snapshots`, `get_snapshot`, `list_cases`, `get_case`,
`list_runs`, `list_scored_runs`, `list_campaigns`, `get_campaign_matrix`,
`list_tags`, `list_datasets`, `list_rubrics`, `list_extractors`,
`compare_snapshots`, `get_governance`

**Write / expensive:** `scan_agent`, `create_*`, `generate_case`,
`generate_run`, `evaluate_run`, `create_campaign`, `update_governance`,
`run_report`, `run_blueprint`

Prefer `list_*` before creating duplicates. `generate_run` without `force` skips
cases that already have a run for the same snapshot + case + model.

---

## 8. Headless report (no MCP loop needed)

CLI alternative for a one-shot benchmark report:

```bash
python run_app.py <repo> --mode headless \
  --agent_path "a_single_agent.day_trip:root_agent" \
  --commit HEAD --dataset "DayTrip Tests"
```

MCP equivalent: `run_report(agent_path, commit, dataset_name, …)`.

---

## 9. Related skills

| Goal | Skill |
|---|---|
| Fix failing agent from scores | `skills/loops_mcp/harness_optimisation/SKILL.md` |
| Red-team / adversarial cases | `skills/loops_mcp/adversarial/SKILL.md` |
| Analyse score matrices | `skills/eval_data_analysis/SKILL.md` |
| Inner-loop via blueprint API | `skills/loops_blueprint/*/SKILL.md` |
