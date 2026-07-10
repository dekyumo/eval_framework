# Contract: Loops, MCP, and agent blueprints

Implements specs/spec_of_the_spec/SOUL8_LOOPS.md,
specs/spec_of_the_spec/SOUL8_LOOPS_applied.md and issues/loops_applied.md.

## The dual-loop idea

Everything agentic in 2026 is a loop. We expose each loop **twice**:

- **Inner loop** — an `AgentBlueprint` is instantiated as a Google ADK agent
  *inside* the framework and run to completion. Skills in
  `skills/loops_blueprint/`.
- **Outer loop** — an autonomous coding agent (Cursor / Claude Code / Codex)
  drives the framework through one **stdio MCP server**; the coding agent *is*
  the loop. Skills in `skills/loops_mcp/`.

Both paths resolve tools by name from the **same registry**
(`mcp/registry.py`), so a tool behaves identically whether called by the
in-framework blueprint agent or by an external coding agent.

## 1. Tool registry (`mcp/registry.py`)

`TOOL_NAMES` (already listed in the stub) is the public tool surface, each name
wrapping one service call. `build_registry(repo_path)` returns
`{name: callable}` with `repo_path` bound; callables take/return
JSON-serialisable values so they double as ADK `FunctionTool`s and MCP tools.

Read vs. write split (for skill guidance and future approval gating):
- **Read**: `list_snapshots, get_snapshot, list_cases, get_case, list_runs,
  list_scored_runs, list_campaigns, get_campaign_matrix, list_tags,
  list_datasets, list_rubrics, list_extractors, compare_snapshots,
  get_governance`.
- **Write / expensive**: `scan_agent, create_case, generate_case, generate_run,
  evaluate_run, create_campaign, create_tag, create_dataset, create_rubric,
  create_extractor, update_governance, run_report, run_blueprint`.

`compare_snapshots` wraps `analysis/comparison.py`; `run_report` wraps
`services/benchmark.run_headless_benchmark`. Unknown names raise
`ServiceError(400)`.

### Presets (`PRESET_TOOLS`, `PRESET_INSTRUCTIONS`)

The eight building-block agents from issues/loops_applied.md, each bound to a
subset of tools with a default instruction (role + do-E,F-until-G + example tool
sequence):

| preset | tools |
|---|---|
| `Scanner` | scan_agent, get_snapshot, list_snapshots |
| `RegistryExplorer` | list_tags, list_datasets, list_rubrics, list_extractors |
| `RegistryUpdater` | create_tag, create_dataset, create_rubric, create_extractor, list_tags, list_datasets, list_rubrics, list_extractors |
| `CaseMaker` | generate_case, create_case, list_cases, get_snapshot, list_tags |
| `CaseRunner` | generate_run, list_runs, get_case, list_snapshots |
| `CaseEvalRunner` | evaluate_run, list_scored_runs, list_runs |
| `CampaignRunner` | create_campaign, get_campaign_matrix, list_campaigns, list_datasets |
| `DataWriter` | run_report, get_snapshot, list_scored_runs |

## 2. Blueprint service (`services/blueprints.py`)

- `list_presets() -> [{preset, instruction, tools}]` from the registry maps.
- `preset_blueprint(preset) -> AgentBlueprint dict` (400 on unknown preset).
- `run_blueprint(repo_path, blueprint) -> BlueprintRunResult dict`:
  1. validate into `AgentBlueprint`;
  2. `tools = resolve_tools(repo_path, blueprint.tools)` (400 on unknown tool);
  3. build `LlmAgent(name=..., model=..., instruction=..., tools=tools)`;
  4. run synchronously to completion via `InMemoryRunner` (follow the pattern in
     `agents/case_writer/case_writer_runner.py`, wrapping `asyncio.run`);
  5. collect the transcript and tool calls into `BlueprintRunResult`.

`domain/blueprint.py` (already stubbed) defines `AgentBlueprint`,
`BlueprintPreset`, `ToolCall`, `BlueprintRunResult`.

## 3. MCP server (`mcp/server.py`, stdio)

`python run_app.py <repo> --mode mcp`. Repo path is the positional argument.
MCP mode dispatches immediately after argparse (no stdout prints, no Flask).
dotenv loads silently so blueprint/LLM tools get API keys. Registers every
registry tool via `build_server`. The standalone `eval-workbench-mcp` console
script and `python -m src.eval_workbench.mcp` remain as aliases. Serve over stdio.

## 4. Routes (already wired, thin) — `/api/blueprints`

- `GET  /api/blueprints/presets`
- `POST /api/blueprints/run`  (body: an `AgentBlueprint`)

## 5. The four loops

Each loop gets, in **both** `skills/loops_blueprint/<loop>/SKILL.md` (inner) and
`skills/loops_mcp/<loop>/SKILL.md` (outer), and an agent spec under
`specs/agent_spec/loops/<loop>.md`.

- **`ci_cd`** — monitor a new commit. Scanner → CaseRunner → CaseEvalRunner →
  DataWriter, then `compare_snapshots` against the previous commit; greenlight or
  not. Per issues/loops_applied.md this is mostly the `eval_data_analysis` skill
  plus `run_report`; the outer skill leans on that skill and the CSV output.
- **`audit`** — for the latest snapshot: check in/margin/ood cases sit in the
  right region vs. the stated domain; check client/technical/adversarial problem
  coverage; check which safeguards exist (from the snapshot) and whether they are
  tested; compute average token cost per run. Uses `get_governance`,
  `get_snapshot`, `list_cases`, `run_report`, and the `governance_audit` skill.
- **`harness_optimisation`** — for each failing case, generate a ~100-word blurb
  on what to improve; summarise; feed to an automated coding agent (outer loop)
  or surface for human action (inner loop); watch the test suite.
- **`adversarial`** — define adversariality modalities (tags), hand the snapshot
  to a frontier model, ask it to attack the agent, turn findings into new cases,
  then run the `harness_optimisation` loop.

Inner SKILLs show the `POST /api/blueprints/run` payload (preset or custom
blueprint) and how the calling LLM may edit the instruction/tools first. Outer
SKILLs show the concrete MCP tool sequence and stop condition (the "until G"),
and where the coding agent should act on results.

## 6. Dependencies & tests

- Add the `mcp` SDK to `pyproject.toml`; add the `eval-workbench-mcp` script.
- `tests/test_blueprints.py`: `list_presets`, `preset_blueprint`, and a
  `run_blueprint` run with a stubbed / cheap read-only tool set (assert transcript
  + tool_calls populated; unknown tool → ServiceError).
- `tests/test_mcp.py`: registry completeness (every `TOOL_NAMES` entry resolves
  via `build_registry`), and `resolve_tools` raises on an unknown name.

Keep tests light and meaningful; do not call paid LLMs in unit tests (bind fake
callables / use a read-only blueprint).
