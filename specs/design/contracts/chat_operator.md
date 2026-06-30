# Contract: Chat operator and the monitor-version loop

`agents/chat_operator/` (AGENT1) + `services/loops.py`. The chat agent itself is trivial — it is an ADK agent whose tools are the framework's own service functions. The real work is (a) the tool surface and (b) one safe loop. Build this **last** (Phase 10); it depends on the service layer being complete.

## Principle (carried from IMPLEMENTATION.md)

The agent calls **service functions**, in-process, not HTTP routes. The agent never computes a score, builds a matrix, or mutates storage directly — it calls deterministic services that do. The agent is just another client of the contract layer, alongside the Flask routes and the UI.

## Tool surface

Wrap service functions as ADK `FunctionTool`s, split into two tiers:

**Read tools (unrestricted):**

```text
list_agents() ; get_snapshot(id) ; list_snapshots(agent)
list_cases(tags?) ; get_case(id) ; get_run(id) ; get_trace(run_id)
compare_snapshots(a, b) ; get_regressions() ; build_response_matrix(campaign_id)
get_agreement(rubric_id) ; list_tags()
```

**Write / expensive tools (return a PROPOSAL, require human confirmation in the UI before execution):**

```text
scan_snapshot(agent, commit) ; create_case(...) ; copy_case(id) ; edit_case(...)
run_case(case_id, snapshot_id) ; run_dataset(snapshot, tag_filter, repetitions)
run_campaign(dataset, model_panel, repetitions) ; submit_human_eval(run_id, ...)
delete_*(...)            # always behind the bad-tempered confirmation modal
```

Write tools do not execute on call; they return a structured `ActionProposal` that the UI renders for the human to approve. This keeps the human in the loop (SOUL12) and prevents an LLM turn from silently mutating the corpus.

Tool schemas come from the typed service signatures (Pydantic), so the tool list is generated, not hand-maintained.

## Sub-agents (AGENT1 — implements LOOPS soul loops 1 & 2)

The operator can hand off to three sub-agents (read-only analysts):
- **failure-explainer** — input: a failing trace + snapshot; output: why it failed.
- **failure-clusterer** — input: a set of failures; output: phenomenological categories (calls `analysis/clustering.py`; does not invent the clustering math).
- **regression-explainer** — input: two snapshots + a trace; output: why this trace regressed.

## The monitor-version loop (the one safe loop to ship — SOUL8)

`services/loops.py: monitor_version(snapshot_a, snapshot_b) -> VersionReport`. Deterministic pipeline; the agent narrates and proposes, the human greenlights.

```python
def monitor_version(a: AgentSnapshot, b: AgentSnapshot) -> VersionReport:
    diff = semantic_diff(a, b)                  # manifest diff: prompt/model/tool/hierarchy changes
    delta = compare_runs(a, b)                  # per tag x metric score deltas on the SAME cases
    attribution = attribute(delta, diff)        # link each regression to the smallest matching change
    return VersionReport(diff, delta, attribution, recommendation="greenlight" | "hold")
```

Rules:
- Attribution is a **suggestion**, never an autonomous decision. The report ends with a recommendation; a human clicks greenlight.
- Respect the held-out split (SOUL13): comparison runs over `judging` cases; never tune anything here.
- Causality caveat (agreed earlier): attribution is interventional only where the framework owns the change (the commit diff). It does not claim to explain failures whose cause is hidden environment state.

The other SOUL8 loops (red/green/blue, GEPA-style optimisation, Darwin-Gödel) are **out of scope** for now. Any future optimisation loop must read only `optimisation`-split cases and never touch `judging` (SOUL13).

## Streaming

Serve agent turns over Flask SSE in AG-UI-style parts (message parts, tool start/stop, reasoning start/stop, a stop control). Keep it simple; this is a local single-user tool.

## Tests

- each read tool returns the same data as calling the service directly.
- a write tool returns an `ActionProposal` and does **not** mutate storage until `confirm` is called.
- `monitor_version` on two snapshots with a known prompt change → the regression is attributed to that prompt change; recommendation is `hold` when a `judging`-split regression exists.
- the operator never calls a scoring/matrix function that returns a raw number it then re-derives — it surfaces the service's number verbatim.

## Dogfooding

Once running, point the scanner at `src/eval_workbench/agents/chat_operator` at a clean framework commit, snapshot it, and evaluate the operator with the platform. This is the intended end-to-end demo.
