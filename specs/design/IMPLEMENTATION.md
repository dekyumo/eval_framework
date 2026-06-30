# IMPLEMENTATION — start here

This is the entry point for an agent (or person) implementing the Agent Evaluation and Provenance Workbench. Read it fully, then read the linked specs in order, then work the TODO at the bottom.

## What this is

A local, single-process workbench that makes ADK agent evaluation reproducible and inspectable. It snapshots an ADK agent at a clean git commit, runs evaluation cases against it in isolation, scores the traces, and compares versions. It is **not** a production observability platform.

## Reading order (do not skip)

1. `specs/spec_of_the_spec/SOUL1..SOUL13` — the conceptual grounding (the "why"). Each soul is a field of science the platform borrows from. Treat them as the source of intent.
2. `specs/functional_spec.md` and `specs/functional_spec_addendum.md` — the functional behaviour. Note: the souls were written **after** these, so where they conflict, the souls and this design win.
3. `specs/python_objects.md` — the first-pass object/architecture sketch.
4. `specs/design/object_model.md` — **the authoritative object model and Kuzu schema.** Build this first.
5. `specs/design/contracts/*.md` — the fragile components, each with a formal contract, error taxonomy, pseudocode, and tests. These are the parts a weaker model must implement carefully and not improvise.
6. `specs/agent_spec/AGENT1..AGENT4` — the framework's own ADK agents (dogfooded).

## Architecture (one rule above all)

```text
                Flask routes        Web UI (templates + graph lib)        Chat operator (ADK agent)
                     \                      |                                   /
                      \                     |                                  /
                       +------------------- SERVICE LAYER --------------------+        <-- the contract
                                              |
                        analysis (sklearn/numpy) | scanner | runner | faults | extraction
                                              |
                                      STORAGE (Kuzu, one DB per agent-under-test)
```

**The service layer is the contract.** The Flask routes, the web UI, and the chat agent are all *clients* of the same service functions. The chat agent wraps **service functions** as tools, never HTTP routes. Nothing above the service layer computes scores; the deterministic core does.

## Technology choices (locked)

| Concern | Choice | Notes |
| --- | --- | --- |
| Web | **Flask**, single process | `python run_app.py`. No Docker. Serves API + UI (templates first; a built static SPA later if needed). |
| Agents | **ADK (latest)** + **LiteLLM** | LiteLLM wrapper for non-Gemini models in the campaign panel. Pin the ADK version; isolate all ADK-version-sensitive code in `scanner/` and `faults/`. |
| Metrics/ML | **scikit-learn + numpy** (+ scipy) | Classification/regression metrics, Cohen's kappa, PCA/clustering, and the IRT response matrix as a logistic regression on a design matrix. |
| Embeddings | **sentence-transformers**, `paraphrase-multilingual-*` | For clustering/anomaly (SOUL2). Multilingual on purpose. |
| Storage | **Kuzu**, embedded, **one DB per agent-under-test** | Graph-shaped: commit DAG + snapshot→subagent/prompt/tool edges. |
| Isolation | **git worktree + uv venv**, subprocess execution | Correctness under concurrency, not a security sandbox. |
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
      kuzu_store.py                  # connection, get-or-create DB per agent
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
      app.py routes/ templates/ static/
    agents/                          # the framework's OWN ADK agents (dogfoodable)
      chat_operator/ agent.py tools.py sub_agents/   # AGENT1
      code_explorer/ agent.py                        # AGENT2 (assists scanner)
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

## Implementation discipline (the guardrails — obey these)

1. **Domain first, typed everywhere.** All domain objects are Pydantic models in `domain/`. No dicts-as-objects across module boundaries.
2. **Deterministic core.** Scoring, metrics, the response matrix, comparison: pure functions of stored data. **No LLM call ever computes a score or a metric.** LLM-as-judge produces a stored `Result`; aggregation is deterministic.
3. **Fragile parts behind contracts.** `scanner`, `runner`, `faults` each have a contract file with an explicit **error taxonomy** that separates *caller misuse*, *agent-under-test fault*, and *framework bug*. Write the contract's tests before/with the implementation. Never let an unexpected exception masquerade as an agent fault (blame must be attributable).
4. **Artifacts are fingerprinted.** Prompts (raw template, pre-`.format`), mock tools, and extractor functions are stored as inspectable source with a content hash. Same input → same fingerprint → reuse, never duplicate.
5. **Reproducibility.** Models are fully qualified and pinned; reject `latest`. Faults are deterministic (seeded). Snapshots require a clean commit.
6. **Held-out is sacred (SOUL13).** Every `EvalCase` carries `split: optimisation | judging`. Any optimisation loop may read only `optimisation` cases. `judging` cases never tune anything.
7. **Subprocess isolation.** Agent code is executed in a subprocess inside a worktree venv, never imported into the main process (avoids `sys.modules` collisions across commits).
8. **No scope creep.** Build the slices in the TODO. Do not add features not in the specs. If a spec is ambiguous, prefer the simplest inspectable option and leave a `# SPEC-GAP:` comment.

## Definition of done per component

A component is done when its **contract tests pass** (see each contract file). The first end-to-end milestone (M1) is: *scan a clean commit → snapshot → run one case → score it with one deterministic metric → display it.* Get to M1 before breadth.

## TODO / phased plan

Phases are ordered by dependency. Each phase ends when its tests are green. The list is intentionally slightly loose — use judgement on internal structure, but keep the discipline above.

- **Phase 0 — Scaffold.** `uv` project, deps pinned, `run_app.py` + Flask health route, pytest wired, `config.py` with the model panel. Kuzu connection opens and closes.
- **Phase 1 — Domain + storage.** Implement all `domain/` models per `object_model.md`. Implement `storage/schema.py` (Kuzu node/rel tables) and `repositories.py` with typed CRUD. Round-trip tests for every model.
- **Phase 2 — AgentScanner.** Implement per `contracts/agent_scanner.md`. Build the golden + malformed fixtures. All error-taxonomy tests pass. (Fragile — go slow.)
- **Phase 3 — WorktreeRunner.** Implement per `contracts/worktree_runner.md`, subprocess execution, venv cache, guaranteed cleanup, Windows caveats handled. Concurrency test passes. (Fragile.)
- **Phase 4 — AgentRunner + Trace.** Run one case in a worktree → serialized `Trace` (parts, structured output, exception, latency, tokens). **M1 here**: scan → snapshot → run → score → show.
- **Phase 5 — Scoring + extraction.** `analysis/metrics.py`, type-driven folding, deterministic + verifier + rubric evaluators, extractor loading/fingerprinting. Minimal `extractor_author` (AGENT4) draft→run→confirm.
- **Phase 6 — Faults.** Implement per `contracts/fault_injector.md` (ADK callbacks + `mocked_tools.py`). Robustness/resilience rubric (detect/contain/recover/honesty).
- **Phase 7 — Campaign + response matrix.** `EvalCampaign` runs the dataset across the model panel; `analysis/response_matrix.py` builds the design matrix + logistic regression for difficulty/ability, co-failure clustering, and thinning.
- **Phase 8 — Comparison + validity.** Snapshot/run comparison, regression detection, human–LLM agreement, the SOUL13 held-out guard (score-up-while-agreement-down flag).
- **Phase 9 — Web UI.** Agent/lineage graph, dashboard, run viewer, comparison view, eval builder (domain × problem matrix).
- **Phase 10 — Chat operator.** Wrap service functions as ADK tools (read vs confirm-write), build the agent + sub-agents (AGENT1), implement the monitor-version loop (human-greenlit). Dogfood: evaluate the chat operator with the platform.

See `object_model.md` next.
