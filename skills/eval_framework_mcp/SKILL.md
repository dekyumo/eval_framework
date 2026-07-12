---
name: eval-framework-mcp
description: >-
  Use the eval_framework MCP server (eval-workbench) to scan agents, build
  datasets and cases, run traces, score them, and launch campaigns. Use when
  working with eval-workbench MCP tools, run_app.py --mode mcp, or eval case
  registries in eval_framework_df.
---

# Eval Framework MCP

Use this skill when driving the eval workbench through its MCP server — not the
inner blueprint loops (`skills/loops_mcp/*`).

**Always inventory before you write.** Call the relevant `list_*` tools first.
Only call a `create_*` or `scan_*` tool when you know something is missing.
The workflow in §5 is a **suggested starting order for an empty registry**, not
a checklist you must run every time.

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

Quick smoke test once connected: call `list_datasets`, `list_gyms`, or `list_snapshots`.


---

## 2. ID conventions (not obvious from tool names)

| Object | ID format | You supply it? |
|---|---|---|
| **Snapshot** | `{commit_hash}:{agent_python_path}:{python_var_name}` e.g. `c97928…:a_single_agent.day_trip:root_agent` | No — returned by `scan_agent` |
| **Case** | e.g. `case_seoul_day` | **Yes** — pick a stable string |
| **Dataset** | e.g. `ds_daytrip` | **Yes** |
| **Tag** | slug from name if omitted | Optional — see §3 |
| **Rubric** | e.g. `rubric_daytrip_ontopic` | **Yes** |
| **Gym** | e.g. `ticket-triage-gym` | **Yes** (or slug from name) |
| **Extractor** | e.g. `ext_latency` | **Yes** |
| **Run** | `{dataset}-{case}-{agent}_{commit}_{model}-{hash}` | No — returned by `generate_run` |
| **Scored run** | `scored_{run_id}` | No — returned by `evaluate_run` |
| **Campaign** | e.g. `campaign_a1b2c3d4` | **Yes** |

`agent_path` is the ADK import path: `package.module:root_agent` (colon separates
module from variable).

After any `create_*`, call the matching `list_*` or `get_*` to confirm
persistence and capture IDs you will need later.

---

## 3. What each action is for

Use this table to decide **whether** to call a tool, not just how.

### Read / inventory (cheap — prefer these first)

| Tool | Use when |
|---|---|
| `list_snapshots` | You need a `snapshot_id` for `generate_run` or `create_campaign`. **Check here before `scan_agent`.** |
| `get_snapshot` | You need manifest, distribution, or agent metadata for an existing snapshot. |
| `list_datasets` / `list_cases` / `get_case` | Cases or datasets already exist; you are adding to or inspecting them. |
| `list_rubrics` / `list_extractors` | Scoring objects already exist; avoid duplicate `create_*`. |
| `list_gyms` | Gym environments for agentic-user cases already exist; check before `create_gym`. |
| `list_tags` | You want to attach an **existing** tag to a case, or see what labels are in use. |
| `list_runs` / `list_scored_runs` | Traces or scores already exist; avoid redundant runs. |
| `list_campaigns` / `get_campaign_matrix` | Campaign finished; you are analysing results. |
| `compare_snapshots` | Diff two agent versions (manifest / distribution). |
| `get_governance` | Read NIST AI RMF profile for a snapshot. |

### Write / expensive (only when the inventory step shows a gap)

| Tool | Semantically useful for | Skip when |
|---|---|---|
| **`scan_agent`** | First-time capture of an agent at a **specific git commit**: produces a `snapshot_id` (manifest + optional distribution). | `list_snapshots` already has the agent path + commit you need. Re-scanning the same commit wastes time and duplicates work. **Fails if the git repo has unstaged changes to tracked files** (`git status --porcelain -uno` non-empty) — commit or stash first. |
| **`create_dataset`** | Grouping cases for reports, campaigns, or organisation. | A suitable dataset already exists. |
| **`create_case`** | Adding one eval scenario (conversation, metrics, metadata) to a dataset. | The case id already exists (`get_case`). |
| **`create_rubric`** | Defining LLM-as-judge criteria for metrics with `strategy: "rubric"`. | `list_rubrics` already has the rubric you need. |
| **`create_extractor`** | Registering a **stored Python** `extract(trace)` used by **deterministic** metrics (`strategy: "deterministic"`). This is the scoring pipeline object, not the extractor_author agent. | You only need rubric or verifier scoring; or the extractor already exists. |
| **`create_gym`** | Registering a **gym environment class** for agentic-user simulations (`agentic_user.gym_ref`). The class lives in the agent repo; bound methods become user/solver tools at run time. | `list_gyms` already has the gym you need. |
| **`create_tag`** | Cross-cutting **case labels** for analysis: harmfulness, bias, PII, regulatory theme, etc. Attach via `tags` on specific cases. | You are just building a dataset — tags are not required. Do **not** create tags merely to mark "this suite" or "this internal agent". |
| **`generate_case`** | AI-assisted case **draft** via the case_writer agent (needs `snapshot_id` + specification string). | You are writing cases manually, or the user gave you full case JSON. |
| **`generate_run`** | Executing the **agent under test** on one case → produces a trace. | A run already exists for the same snapshot + case + model (unless `force=true`). |
| **`evaluate_run`** | Scoring an **existing** run (rubric / deterministic / verifier per case metrics). | Runs are not created yet, or the run is already scored (unless `force=true`). |
| **`create_campaign`** | Batch: all cases in a dataset × all models in a panel → runs + scores → matrix. | You only need one case/model, or a campaign already exists. |
| **`update_governance`** | Saving NIST AI RMF profile text on a snapshot. | Read-only inspection (`get_governance`). |
| **`run_report`** | One-shot headless benchmark (CLI-style) via MCP. | Interactive MCP steps are enough. |
| **`run_blueprint`** | Inner optimisation / adversarial loops — see `skills/loops_mcp/*`. | Normal eval registry work. |

### How objects relate (not a mandatory pipeline)

```
snapshot  ←── scan_agent (only if missing)
    │
    ├── generate_run(snapshot, case, model) → run → trace
    │         └── evaluate_run(run) → scored run
    │
    └── create_campaign(dataset, snapshot, models) → many runs + scores
              └── get_campaign_matrix → ability / difficulty

dataset ←── create_dataset
    └── create_case (dataset_id links case into exactly one dataset)

case.metrics ──► rubric_ref  → Rubric (create_rubric)
              ──► extractor_ref → Extractor (create_extractor)
              ──► verifier_ref  → (future)

case.tags ──► optional Tag ids (create_tag only for real categorisation needs)

Gym ←── create_gym (class_path points to env class in agent repo)
    └── agentic_user.gym_ref on cases using two-agent simulation
```

- **`snapshot_id`** is the **agent under test** at a pinned commit — whichever
  agent the user is evaluating.
- **`generate_run`** picks snapshot + case at run time; cases do not embed the
  snapshot.
- Cases reference rubrics via `metrics[].rubric_ref` and extractors via
  `extractor_ref`.

---

## 4. Case fields cheat sheet

| Field | Values / notes |
|---|---|
| `distribution_position` | `in`, `margin`, `ood` — where this case sits relative to the agent's intended domain |
| `problem_type` | `happy`, `technical`, `adversarial`, `client` |
| `split` | `train` (optimisation) or `test` (judging) |
| `conversation` | list of `{ role, kind: "text", text }` turns — usual agent input |
| `session_state` | optional ADK session injection before run — see §6 |
| `agentic_user` | two-agent gym simulation — see §6b; requires `create_gym` + `gym_ref` |
| `tool_fault` | `{ tool_name, fault_type }` for fault-injection / mocked-tool runs |
| `tags` | optional list of tag ids — only when the case needs a cross-cutting label |
| `metrics[].strategy` | `rubric`, `deterministic`, `verifier` |

Use **either** `conversation` **or** `input_payload`, not both.

---

## 5. Suggested order when starting from scratch

If the registry is **empty** for your task, this order is a reasonable default.
**Skip any step** whose output already exists in `list_*`.

1. **`list_snapshots`** — if the target agent+commit is already there, note
   `snapshot_id` and **do not** call `scan_agent`.
2. **`scan_agent`** — only if step 1 found no matching snapshot.
3. **`list_rubrics` / `list_extractors` / `list_gyms`** — create only what your case metrics need.
4. **`create_dataset`** — if no dataset for this work yet.
5. **`create_case`** — one or many; pass `dataset_id` so the dataset links automatically.
6. **`generate_run`** — when you are ready to produce traces (user may do this separately).
7. **`evaluate_run`** — when traces exist and you want scores (user may do this separately).
8. **`create_campaign`** — optional batch across models; then `get_campaign_matrix`.

Do not bundle steps the user did not ask for (e.g. scanning an already-scanned
agent, creating tags, evaluating runs, or launching campaigns).

### Example: greenfield day-trip agent

```text
list_snapshots
scan_agent(agent_path="a_single_agent.day_trip:root_agent", commit="HEAD")   # only if missing
list_rubrics
create_rubric({ "id": "rubric_daytrip_ontopic", ... })
create_dataset({ "id": "ds_daytrip", "name": "DayTrip Tests", "case_ids": [] })
create_case({ "id": "case_seoul_day", "conversation": [...], "metrics": [...] },
            dataset_id="ds_daytrip")
# user may run later:
generate_run(snapshot_id, "case_seoul_day", model_id="gemini-2.5-flash")
evaluate_run(run_id)
```

### Example: add cases to an existing dataset

```text
list_datasets
list_rubrics
get_case("case_existing")          # optional pattern reference
create_case({ ... }, dataset_id="ds_existing")
```

### Example: register gyms for agentic-user cases

```json
{
  "data": {
    "id": "ticket-triage-gym",
    "name": "Ticket Triage Gym",
    "class_path": "gym.ticket_triage_gym.TicketTriageGym",
    "description": "Inbox/processed fixture env for ticket triage agentic sims"
  }
}
```

Then `list_gyms` to confirm. Agentic cases set `agentic_user.gym_ref` to that id,
`user_tools` / `solver_tools` to gym method names, and `termination_method` to
the gym's bool predicate (e.g. `inbox_empty`).

### Example: manual case (full control)

```json
{
  "dataset_id": "ds_daytrip",
  "data": {
    "id": "case_seoul_day",
    "name": "Seoul day trip",
    "conversation": [{ "role": "user", "kind": "text", "text": "Plan a day in Seoul" }],
    "session_state": null,
    "distribution_position": "in",
    "problem_type": "happy",
    "split": "test",
    "source": "manual",
    "metrics": [{
      "id": "m_seoul",
      "name": "quality",
      "strategy": "rubric",
      "result_type": "float",
      "rubric_ref": "rubric_daytrip_ontopic"
    }]
  }
}
```

### AI-assisted case draft (`generate_case`)

```
generate_case(snapshot_id, "happy-path case: plan a day in Seoul with $200 budget")
→ draft dict → edit → create_case({ ...draft, "id": "case_…", "dataset_id": "ds_…" })
```

Requires a stored snapshot and a non-empty `specification` string.

---

## 6. `session_state`

For most agents: leave `session_state` **null**. The case `conversation` is the
input.

Use `session_state` only when the **agent under test** reads session variables
(e.g. its instruction template contains `{variable}` placeholders filled from
ADK session state). Complex values are often stored as JSON strings.

If the agent takes a single user message and has no session placeholders, do not
invent `session_state` fields.

For **agentic-user** cases, set `session_state` to `{ "gym": {} }` (or a config
dict passed to the gym constructor). The gym class is resolved from
`agentic_user.gym_ref` → `list_gyms` / `create_gym` registry entry.

---

## 6b. Agentic-user cases and gyms

Workflow (all via MCP):

1. `create_gym` with `class_path` pointing at the env class in the agent repo
   (e.g. `gym.ticket_triage_gym.TicketTriageGym`).
2. `list_gyms` to confirm the `id`.
3. `create_case` with `agentic_user`:

```json
{
  "user_agent_path": "user_agents.ticket_triage_user:root_user",
  "gym_ref": "ticket-triage-gym",
  "user_tools": ["keyword_search", "inbox_empty"],
  "solver_tools": [],
  "max_turns": 8,
  "termination_method": "inbox_empty"
}
```

4. `conversation` must include an opening user turn (seed text for the simulation).
5. `generate_run` / `evaluate_run` as usual.

Gym method names in `user_tools` / `solver_tools` must exist on the gym class.
`termination_method` must be a gym method returning `bool`.

---

## 6c. Rubric `default_judge_prompt` pitfalls

The rubric judge is an ADK agent. **Only use `{instructions}`** in
`default_judge_prompt` — ADK interprets other `{…}` tokens as session-state
placeholders. Using `{trace}` causes `KeyError: Context variable not found: trace`
and all bool scores come back false.

The execution trace is already passed as the **user message** to the judge agent
(see `rubric_judge_runner.py`). Safe template:

```
Please evaluate the trace based on the following instructions: {instructions}
```

---

## 7. Rubric results and campaign metrics

`RubricEvaluator` stores one `Result` **per rubric item**, not per case metric:

```
result.name == "{metric.name} ({item.name})"
```

Example: metric `quality` + item `on_topic` → `quality (on_topic)`.

Implications:

- **`get_campaign_matrix`** takes `metric` = that **full result name** (or a
  unique item suffix). Rubric metrics expand to one dropdown entry per item.
- Bool items → logistic IRT; float/int items → linear regression on raw values.

Author rubric prompts so **higher is better** and **True means pass** (SOUL3).

---

## 8. Bulk case creation

When adding many cases, a practical order:

1. `list_gyms` → `create_gym` only if needed
2. `list_rubrics` → `create_rubric` only if needed
3. `list_datasets` → `create_dataset` only if needed
4. `create_case` for each case with `dataset_id`

After a batch: `list_datasets` (confirm each dataset's `case_ids` length);
`list_gyms`; spot-check with `get_case(case_id)`.

For running many cases, prefer **`run_report`** (one MCP call per dataset) when
you need all cases for one agent scored. Use **`generate_run` + `evaluate_run`**
per case when debugging individual failures (`force=true` to re-run).

---

## 9. Read-only vs write tools

**Read:** `list_snapshots`, `get_snapshot`, `list_cases`, `get_case`,
`list_runs`, `list_scored_runs`, `list_campaigns`, `get_campaign_matrix`,
`list_tags`, `list_datasets`, `list_rubrics`, `list_extractors`, `list_gyms`,
`compare_snapshots`, `get_governance`

**Write / expensive:** `scan_agent`, `create_*`, `generate_case`,
`generate_run`, `evaluate_run`, `create_campaign`, `update_governance`,
`run_report`, `run_blueprint`

(`create_gym` registers gym classes; `list_gyms` inventories them.)

`generate_run` without `force` skips cases that already have a run for the same
snapshot + case + model. `evaluate_run` without `force` skips already-scored runs.

---

## 10. Headless report (no MCP loop needed)

CLI alternative for a one-shot benchmark report:

```bash
python run_app.py <repo> --mode headless \
  --agent_path "a_single_agent.day_trip:root_agent" \
  --commit HEAD --dataset "DayTrip Tests"
```

MCP equivalent: `run_report(agent_path, commit, dataset_name, …)`.

---

## 11. Related skills

| Goal | Skill |
|---|---|
| Fix failing agent from scores | `skills/loops_mcp/harness_optimisation/SKILL.md` |
| Red-team / adversarial cases | `skills/loops_mcp/adversarial/SKILL.md` |
| Analyse score matrices | `skills/eval_data_analysis/SKILL.md` |
| Inner-loop via blueprint API | `skills/loops_blueprint/*/SKILL.md` |
