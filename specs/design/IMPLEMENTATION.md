# IMPLEMENTATION — start here

This is the entry point for an agent (or person) implementing the Agent Evaluation and Provenance Workbench. Read it fully, then read the linked specs in order, then work the TODO at the bottom.

## What this is

A local, single-process workbench that makes ADK agent evaluation reproducible and inspectable. It snapshots an ADK agent at a clean git commit, runs evaluation cases against it in isolation, scores the traces, and compares versions. It is **not** a production observability platform.

## Reading order (do not skip)

1. `specs/spec_of_the_spec/SOUL1..SOUL13` — the conceptual grounding (the "why"). Each soul is a field of science the platform borrows from. Treat them as the source of intent.
2. `specs/functional_spec.md` and `specs/functional_spec_addendum.md` — the functional behaviour. Note: the souls were written **after** these, so where they conflict, the souls and this design win.
3. `specs/python_objects.md` — the first-pass object/architecture sketch.
4. `specs/design/object_model.md` — **the authoritative object model and Kuzu schema.** Build this first.
5. `specs/design/contracts/*.md` — the fragile components, each with a formal contract, error taxonomy, pseudocode, and tests. These are the parts a weaker model must implement carefully and not improvise. This includes `contracts/web_frontend.md` — the SPA pages, actions, and edit surfaces (gen-1's UI was underspecified).
6. `specs/agent_spec/AGENT1..AGENT5` — the framework's own ADK agents (dogfooded).

## Architecture (one rule above all)

```text
                Flask routes        Web UI (templates + graph lib)        Chat operator (ADK agent)         Command line run for CD/CI
                     \                      |                                   /                               /
                      \                     |                                  /                               /
                       +------------------- SERVICE LAYER --------------------+-------------------------------+        <-- the contract
                                              |
                        analysis (sklearn/numpy) | scanner | runner | faults | extraction
                                              |
                                      STORAGE (Kuzu, one DB per repo)
```

**The service layer is the contract.** The Flask routes, the web UI, and the chat agent are all *clients* of the same service functions. The chat agent wraps **service functions** as tools, never HTTP routes. Nothing above the service layer computes scores; the deterministic core does.

## Unit of evaluation (read before Phase 2 — gen-1 got this wrong)

The thing under test is an **`AgentTarget = (repo, agent_path)`**, not a repo. A repo may contain several ADK agents, and a sub-agent may be evaluated on its own.

- **Snapshot identity is `(commit, agent_path)`.** One commit of a multi-agent repo yields several snapshots.
- **One Kuzu DB per repo**, shared by the repo's agents (they share a commit DAG + topology). The DB path is configured/derived per repo, **never hard-coded**.
- **the git repo, that contains a .git is set from the commandline when the application is launched**
- **the agent path is set in the UI** (pick agent → scan). 
- **ADK is the only agent framework.** "An agent is an importable object / directory" is ADK's model, not ours. **Do not build a non-ADK compatibility shim** —

## Technology choices (locked)

| Concern | Choice | Notes |
| --- | --- | --- |
| Web API | **Flask**, single process | `python run_app.py`. No Docker. Serves a JSON API **and** the pre-built SPA bundle as static files. No server-side templating for app pages. |
| Web UI | **React + TypeScript SPA**, Vite build | Compiled to static assets checked in / built once, then served by Flask. One app, client-side routing — not a pile of static pages with a navbar. See `contracts/web_frontend.md`. |
| Agents | **ADK, pinned** (`google-adk`, exact version in `pyproject.toml`) + **LiteLLM** | ADK is the ONLY agent framework; no shim for others. LiteLLM wraps non-Gemini campaign models. Isolate ADK-version-sensitive code in `scanner/` and `faults/`. ADK must be a real dependency, not mocked. |
| Metrics/ML | **scikit-learn + numpy** (+ scipy) | Classification/regression metrics, Cohen's kappa, PCA/clustering, and the IRT response matrix as a logistic regression on a design matrix. |
| Embeddings | **sentence-transformers**, `paraphrase-multilingual-*` | For clustering/anomaly (SOUL2). Multilingual on purpose. |
| Storage | **Kuzu**, embedded, **one DB per repo** | Graph-shaped: commit DAG + snapshot→subagent/prompt/tool edges. Path configured per repo. Store the DB next to the repo|
| Isolation | **git worktree + uv venv**, subprocess execution, roll your own or get a library | Correctness under concurrency, not a security sandbox. |
| Tests | **pytest** | Contract tests for every fragile component. |
| Packaging | **uv** | `pyproject.toml`; pinned deps. |

## Directory structure

```text
eval_framework/                      # THIS repo (git)
  run_app.py                         # single entry point
  pyproject.toml
  specs/                             # all specs (this folder)
  src/eval_workbench/
    config.py                        # settings, model panel, paths
    domain/                          # Pydantic models, NO i/o
      trace.py result.py case.py rubric.py snapshot.py manifest.py
      run.py campaign.py fault.py tag.py
    storage/
      schema.py                      # Kuzu DDL (node/rel tables)
      kuzu_store.py                  # connection, get-or-create DB per REPO (keyed by repo path)
      repositories.py                # typed read/write per node type
    services/                        # THE CONTRACT LAYER (API + chat agent call this)
      agents.py snapshots.py cases.py runs.py scoring.py
      campaigns.py comparison.py tags.py human_eval.py loops.py
    analysis/                        # sklearn/numpy
      metrics.py response_matrix.py clustering.py agreement.py drift.py
    scanner/                         # FRAGILE — see contract
      scanner.py errors.py
    runner/                          # FRAGILE — see contract
      worktree.py agent_runner.py exec_script.py
    faults/                          # ADK-callback interception — see contract
      injector.py fault_specs.py
    extraction/
      extractor.py                   # load/fingerprint/run extractor functions
    web/
      app.py                         # Flask: JSON API + serves the built SPA bundle (no app templates)
      routes/                        # thin JSON endpoints -> service layer
      static/                        # BUILT SPA bundle (output of frontend/ build) is served from here
    frontend/                        # React + TypeScript SPA source (Vite). Built to web/static/. See contracts/web_frontend.md
      src/ index.html vite.config.ts package.json
    agents/                          # the framework's OWN ADK agents (dogfoodable), git submodule so versions can be switched
      chat_operator/ agent.py tools.py sub_agents/   # AGENT1
      code_explorer/ agent.py                        # AGENT2 (the scanner's LLM assist)
      fault_mocker/  agent.py                         # AGENT3 (writes mocked_tools.py)
      extractor_author/ agent.py                      # AGENT4 (writes extractors)
  tests/
    fixtures/agents/                 # tiny golden ADK agents (clean + malformed)
    test_scanner.py test_worktree.py test_faults.py
    test_scoring.py test_response_matrix.py test_agreement.py

../agents/                           # SIBLING dir, OUTSIDE this repo
  refund_bot/                        # an agent-under-test: its OWN git repo
  ...
```

Agents-under-test are **separate sibling git repos** referenced by path; the framework never evaluates its own repo as a target except for deliberate dogfooding of `src/eval_workbench/agents/*`.

**Do not author agents just to exercise the framework.** For manual testing / dogfooding you need a few real ADK agents to point at — clone an existing set instead of inventing one. [`github.com/cuppibla/adk_tutorial`](https://github.com/cuppibla/adk_tutorial/) has small, self-contained ADK agents covering the shapes the scanner and runner must handle: single agent, sequential, parallel, loop, custom, **router** (exercises the intent-classification enum metric), agent-as-tool, agent-with-memory, and MCP. Clone it into the sibling `../agents/` dir and use its subfolders as `AgentTarget`s. (This is separate from the tiny **golden fixtures** in `tests/fixtures/agents/`, which are hand-built minimal cases the scanner's contract tests assert against — see `contracts/agent_scanner.md`.)

## Implementation discipline (the guardrails — obey these)

1. **Domain first, typed everywhere.** All domain objects are Pydantic models in `domain/`. No dicts-as-objects across module boundaries.
2. **Deterministic core.** Scoring, metrics, the response matrix, comparison: pure functions of stored data. **No LLM call ever computes a score or a metric.** LLM-as-judge produces a stored `Result`; aggregation is deterministic.
3. **Fragile parts behind contracts.** `scanner`, `runner`, `faults` each have a contract file with an explicit **error taxonomy** that separates *caller misuse*, *agent-under-test fault*, and *framework bug*. Write the contract's tests before/with the implementation. Never let an unexpected exception masquerade as an agent fault (blame must be attributable).
4. **Artifacts are fingerprinted.** Prompts (raw template, pre-`.format`), mock tools, and extractor functions are stored as inspectable source with a content hash. Same input → same fingerprint → reuse, never duplicate.
5. **Reproducibility.** Models are fully qualified and pinned; reject `latest`. Faults are deterministic (seeded). Snapshots require a clean commit.
6. **Held-out is sacred (SOUL13).** Every `EvalCase` carries `split: optimisation | judging`. Any optimisation loop may read only `optimisation` cases. `judging` cases never tune anything.
7. **Subprocess isolation.** Agent code is executed in a subprocess inside a worktree venv, never imported into the main process (avoids `sys.modules` collisions across commits).
8. **No scope creep.** Build the slices in the TODO. Do not add features not in the specs. If a spec is ambiguous, prefer the simplest inspectable option and leave a `# SPEC-GAP:` comment.
9. **Thin over clever (gen-1 over-produced).** Cheap models pad. The worktree runner should be a thin wrapper over `git worktree` + `uv` (or a vetted library), not a 400-line reimplementation. Regression "detection" is a threshold comparison over stored aggregates surfaced in the UI, not a bespoke ML module. If a component grows past ~a screen of code, stop and simplify before continuing.
10. **Config, never constants.** Repo path, agent path, model panel, DB location, judge model — all live in `config.py` and/or are set in the UI. **No hard-coded paths, no `AGENT_ENTRYPOINT` env var documented only in source.** A fresh checkout must be configurable without editing code.
11. **All four agents ship; the scanner enables dogfooding.** Do not ship only the chat operator (gen-1's mistake). The scanner (deterministic path + AGENT2 LLM assist) is what makes the platform usable and self-hostable, so it comes first. Sub-agents must be real ADK agents, not mocked stubs.
12. **Nothing is mocked in the delivered core.** `agent_runner.py`, the ADK dependency, and the sub-agents are real. Mocks belong only in `tests/` and in the deliberately-generated `mocked_tools.py` fault artifact.

## Definition of done per component

A component is done when its **contract tests pass** (see each contract file). The first end-to-end milestone (M1) is: *scan a clean commit → snapshot → run one case → score it with one deterministic metric → display it.* Get to M1 before breadth.

## TODO / phased plan

Phases are ordered by dependency. Each phase ends when its tests are green. The list is intentionally slightly loose — use judgement on internal structure, but keep the discipline above.

- first: ask the user if a conda repo or venv exists, or whether you should create one for the project
- for this implementation, basic agent (AGENT1-AGENT4 are provided)
- **Phase 0 — Scaffold.** `uv` project, deps pinned, `run_app.py` + Flask health route, pytest wired, `config.py` with the model panel. Kuzu connection opens and closes.
- **Phase 1 — Domain + storage.** Implement all `domain/` models per `object_model.md`. Implement `storage/schema.py` (Kuzu node/rel tables) and `repositories.py` with typed CRUD. Round-trip tests for every model.
- **Phase 2 — AgentScanner.** Implement per `contracts/agent_scanner.md`: input is an `AgentTarget` (repo + agent_path), output is a snapshot + manifest + detected `AgentDomain`. Build the golden + malformed fixtures. All error-taxonomy tests pass. (Fragile — go slow.)
- **Phase 3 — WorktreeRunner.** Implement per `contracts/worktree_runner.md`, subprocess execution, venv cache, guaranteed cleanup, Windows caveats handled. Concurrency test passes. (Fragile.) You can also use a reputable library for this, at your option.
- **Phase 4 — AgentRunner + Trace.** Run one case in a worktree → serialized `Trace` (parts, structured output, exception, latency, tokens). **M1 here**: scan → snapshot → run → score → show. Implement Agent5, the case writer, at this stage.
- **Phase 5 — Scoring + extraction.** `analysis/metrics.py`, type-driven folding, deterministic + verifier + rubric evaluators, extractor loading/fingerprinting. Minimal `extractor_author` (AGENT4) draft→run→confirm.
- **Phase 6 — Faults.** Implement per `contracts/fault_injector.md` (ADK callbacks + `mocked_tools.py`). Robustness/resilience rubric (detect/contain/recover/honesty).
- **Phase 7 — Campaign + response matrix.** `EvalCampaign` runs the dataset across the model panel; `analysis/response_matrix.py` builds the design matrix + logistic regression for difficulty/ability, co-failure clustering, and thinning.
- **Phase 8 — Comparison + validity.** Snapshot/run comparison, regression detection, human–LLM agreement, the SOUL13 held-out guard (score-up-while-agreement-down flag).
- **Phase 8.5 - other** other missing routes are implemented before the webUI is generated.
- **Phase 9 — Web UI (SPA).** Build the React + TypeScript SPA per `contracts/web_frontend.md`, applying the Stitch `DESIGN.md`. Must cover the full loop: **add repo → pick agent → scan** (no env vars), agent/lineage graph, dashboard, run/trace viewer, comparison view, eval builder (domain × problem matrix), and **edit surfaces for tags, cases, metrics, rubrics, extractors** (gen-1 shipped raw JSON with no editing). Build output lands in `web/static/` and is served by Flask.
- **Phase 10 — Chat operator.** Wrap service functions as ADK tools (read vs confirm-write), AGENT1 has been defined with tool stubs. Finish the implementation by giving it the required access to the services with tools. Implement the chat window with Human in the Loop for write operations.

See `object_model.md` next.
