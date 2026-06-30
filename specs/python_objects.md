I think this is the right moment to do an architecture inventory before writing the spec. The main thing I would avoid is creating “pages that call LLMs.” Instead, think in terms of **domain services** with the UI as a client.

The system naturally splits into:

```
                 Web UI
                   |
                   v
              API layer
                   |
   +---------------+----------------+
   |                                |
 Agent Analyzer                Eval Engine
   |                                |
   +---------------+----------------+
                   |
             Storage layer (Kuzu, one DB per agent)

```

There is no separate provenance engine. Version lineage is just the Git graph held in the storage layer, and lineage/comparison queries run against it directly.

---

## Core domain classes

### Agent representation

### `AgentRepository`

Responsible for:

* locating the ADK agent
* loading the repository
* checking git state
* extracting metadata
* extracting the commit tree hash (`on_top_of` / parent relationship)
* resetting the commit tree in the database if something goes wrong
* reloading from scratch

Methods:

```
load(path)
get_commit()
is_dirty()

```

---

### `AgentSnapshot`

Immutable object.

```
AgentSnapshot:
    id
    commit_hash
    timestamp

    agents[]
    tools[]
    models[]
    prompts[]

    sampling_params      # temperature, top_p, ... (part of the agent, not the run)
    framework_commit?    # optional: commit of this eval framework, for tooling reproducibility

```

---

### `AgentGraph`

Probably the central object.

Nodes:

```
AgentNode
ToolNode
ModelNode
PromptNode

```

Edges:

```
delegates_to
uses_tool
uses_model
contains_prompt

```

Methods:

```
diff(other_snapshot): returns the set difference of sub-agents, tools, models, and prompts

find_capabilities()

find_risks()
```

---

# Agent analysis subsystem

## `AgentScanner`

The component that crawls the ADK project.

Responsibilities:

* AST inspection
* imports
* exported root agent
* decorators/configuration
* tool definitions

Methods:

```
scan(repository)

```

Output:

```
AgentManifest

```

---

## `CapabilityExtractor` / `SpecGenerator`

Uses an LLM.

Input:

* agent graph
* prompts
* tools

Output:

* Markdown spec

---

## `SpecAuditor`

Looks at the spec, the snapshot, and the manifest, and determines whether the agent respects its spec.

Ideally, a spec generated from the source should be given an all clear (because the spec and source obviously match). This lets the user detect when the agent is misaligned with the spec after either the spec changes or the implementation changes.

Input:

```
AgentSpec
+
AgentSnapshot

```

Output:

```
SpecAuditResult:
[
 {
   item,        # a line in the spec
   score,       # Score: value float in [0,100]
   confidence,  # low | medium | high
   rationale,   # what part of the code or snapshot is evidence for the score
 }
]
```

`score` / `confidence` use the single pinned `Score` type (value float in [0,100], confidence low/medium/high) shared by every metric, rubric item, and audit item.

---

# Evaluation subsystem

## `EvalCase`

Basic object:

```
EvalCase:
    id

    conversation             # multi-turn: list of genai messages (ADK/agentic, not single-shot)

    intents[]                # one or more (intent, domain_position) pairs (see Eval Builder)

    tags[]

    metrics[]                # each carries its ground truth / target for this case
```

Evaluation is multi-turn by default because ADK agents are agentic. A case is a conversation, not a single prompt.

---

## `EvalDataset`

Collection.

Methods:

```
add_case()
copy_case(case_id)   # duplicate an existing case into a new editable case
filter(tags)

```

`copy_case` is the deliberate replacement for an automated mutation engine: duplicate, then let the user tweak.

---

## `ScenarioGenerator`

LLM call to generate an initial prompt according to the domain/problem input.

Second call: run the prompt on the agent (the user has to specify a snapshot). We do not strictly need to run this to have a test, because we could define a test only from the initial prompt, but it is better to run it once so we can inspect the result and help create metrics.

Third call: generate the metrics (hard). The framework has to infer verifiability, intent, and related properties.

Inputs:

```
AgentSpec

domain:
    in/margin/ood

problem:
    happy/technical/adversarial/client

```

Output:

```
EvalCase

```

---

There is no mutation engine. The useful part of mutation is covered by `copy_case` (duplicate-and-edit) on `EvalDataset`.

---

## `Evaluator`

An evaluator computes a metric. All evaluators are the same concept: they point at the truth for a case and produce a `Score`. They differ only in *how* the truth is established (see functional spec §2.3):

* deterministic from the trace — `ClassificationEvaluator`, `RegressionEvaluator`
* external verifier (RL-style) — `DeterministicEvaluator`
* rubric only — `LLMJudgeEvaluator`, `HumanEvaluator` (sharing one `Rubric`)

Base interface:

```
evaluate(
    trace,
    case
) -> Score        # value float in [0,100], confidence low/medium/high

```

Implementations:

### `ClassificationEvaluator`

Metrics:

* precision
* recall
* F1

Given a trace, this needs:

* an extraction function (from a list of genai.parts to a bool or enum)
* ground truth (the same bool or enum)

### Regression evaluator

Metrics:

* R2
* MAPE
* standard deviation
* etc.

Given a trace, this needs:

* an extraction function (from a list of genai.parts to a float)
* ground truth

---

### `DeterministicEvaluator`

Typical use cases:

* pytest after development
* mathematical proof checks

Runs an external function that returns OK/KO.

---

### Rubrics

Rubrics are first-class members of this framework because human evaluators need to judge on the same axes as LLMs if we want to compare results.

They come with a default prompt to analyze a trace according to that rubric.

There are several default rubric frameworks (Quality, Tone, etc.) that can be included by default. The user should also be encouraged to create domain-specific rubrics.

Rubrics have output types, for example:

```
{ isOK: True/False, intent: refund|info|request, order_value: 43243.0, item_count: 2 }
```

A rubric’s output type cannot be changed if there are traces already run against it (create a new rubric instead).

Changing the default prompt is also problematic, because the output cannot be reproduced.

**Pairwise comparison** is just a rubric:

* output type: `1_better | 2_better` (optionally `tie`)
* default prompt: "which of these two traces is better, and why"
* human version: the same choice, made by a person

The one structural difference is that a pairwise rubric consumes **two traces** instead of one. This is not yet handled by the GUI (the Run Viewer and Comparison View assume a single trace); supporting a two-trace judging view is an open GUI item.

---

### `LLMJudgeEvaluator`

Uses the rubric and prompt above (or an overridden prompt).

---

### `HumanEvaluator`

Human evaluation according to a rubric.

---

# Execution subsystem

## `AgentRunner`

Executes ADK inside an isolated Git worktree checked out at the snapshot's commit (see `WorktreeRunner` below).

Methods:

```
run(
 agent_snapshot,
 eval_case,
 environment,
 repetitions = 1     # >1 produces several traces -> a data series for scikit metrics
)

```

Returns:

```
list[ExecutionTrace]   # one per repetition

```

---

## `WorktreeRunner`

Provides run isolation so concurrent runs and reruns of old commits never collide in the working tree or in `sys.modules`.

Responsibilities:

* `git worktree add` a throwaway tree at the target commit
* create an isolated environment (e.g. a fresh `uv` venv)
* run, then `git worktree remove`

We drive `git worktree` directly rather than depend on a coding-agent orchestrator. `flywheel-worktree` (Python) is prior art; surveyed CLIs (hawt, wt, parsec) target interactive coding agents, not an embedded runner. This is a correctness mechanism, not a security sandbox.

---

## `ExecutionTrace`

Probably important enough to model.

Contains:

```
Trace:
    list of genai.parts (input, tool calls, structured output, final result)

    exception?        # optional: set when the agent crashed; a crash is just a scorable trace

    latency
    tokens
```

---

## `ToolSandbox`

Controls external tools.

Modes:

```
LIVE
MOCK
FAULT
```

There are default mock tools that wrap regular tools and return predefined outputs (MOCK) or predefined failures (FAULT).

The difficult parts are:

* intercepting the tool itself (either by replacing the tool object inside the agent or by finding a tool-call hook in the ADK)
* generating mock tools (this may require an LLM to analyze the existing tool and produce a mock version that respects the expected schema)
* deciding where to store the mock tool code (perhaps in `test_mock_tools.py`, so the user can inspect it)

---

## `FaultInjector`

The FAULT machinery. In practice "fault injection" is mostly: mock tools that return bad output, and HTTP errors on the LLM call. There is no separate engine.

Two targets:

* tools — garbage output (`meow meow grrr`), exception, malformed payload
* LLM transport — HTTP errors on the model call:

  * 429
  * 503
  * generic error

---

# Comparison subsystem

## `RunComparator`

Methods:

```
compare(
 snapshot_a
 snapshot_b
)
gets the eval runs for A and B
```

Report what exists in A but not B, and in B but not A.

In the intersection:

* for each metric, compute it
* for classification, compare expected classes versus detected classes and show classification measures
* for rubrics, show average score and standard deviation
* if human scores exist, show agreement per item by type:

  * boolean / enum items: confusion (classification) table + Cohen's kappa
  * numeric items: correlation

Output is two levels, not a full cube:

* a summary matrix of `tag × metric` (aggregate score, and delta A→B, per cell)
* a per-cell drill-down: clicking a cell yields the per-case table (case, score A, score B, delta), with the trace one click away

Output:

```
RegressionReport

```

---

# Provenance

No dedicated subsystem. Version lineage is the Git graph in the storage layer; lineage and comparison queries run directly against Kuzu.

---

# Tag subsystem

## `Tag`

```
Tag:
    name
    color
    description

```

---

## `TagRegistry`

Methods:

```
create()
rename()
delete_if_unused()

```

---

## `TestSelector`

Lets the user iterate on `(eval_id, tags[])` to filter the eval cases they want.

---

# API routes

Assuming FastAPI-style. Auth is whatever the web framework provides (this is a local tool, not a SaaS). No pagination — datasets are small, not thousands of items. The system is almost add-only; `DELETE` is rare and deliberately friction-heavy in the UI (see UI pages).

## Agent

```
GET    /agents
GET    /agents/{id}
POST   /agents/import
POST   /agents/{id}/scan          # scan a clean commit -> get-or-create snapshot
GET    /agents/{id}/snapshots
DELETE /agents/{id}

```

---

## Spec

```
GET  /agents/{id}/spec

PUT  /agents/{id}/spec            # save edited / confirmed AGENT_SPEC.md

POST /agents/{id}/spec/generate

POST /agents/{id}/spec/audit

```

---

## Evaluation cases

```
GET    /cases
GET    /cases/{id}

POST   /cases                     # manual create
POST   /cases/generate
POST   /cases/{id}/copy           # duplicate-and-edit (replaces mutation)
PATCH  /cases/{id}
DELETE /cases/{id}

POST   /cases/{id}/run            # run a single case
POST   /runs                      # run a selection (snapshot + tag/case filter, repetitions)

```

---

## Runs

```
GET /runs

GET /runs/{id}

GET /runs/{id}/trace

POST /runs/{id}/human-eval        # submit human rubric answers / comments for a run

```

---

## Comparison

```
POST /compare

GET /regressions

```

---

## Tags

```
GET    /tags

POST   /tags

PATCH  /tags/{id}

DELETE /tags/{id}                 # only when its count is 0

```

---

# UI pages

## Dashboard

Shows:

* the agent graph (a directed graph between agents using the git graph)
* the current commit, highlighted

---

## Agent Explorer

Graph view:

* agents
* tools
* models
* spec
* automated spec/implementation alignment (audit) result

---

## Eval Builder

The matrix described above:

```
Domain:
(o) In domain
(o) Margin
(o) OOD


Problem:
[ ] Happy path
[ ] Technical
[ ] Adversarial
[ ] Client issue

```

Domain is a single radio per intent. The "user sends many intents in one turn" case is not modeled by turning the radio into a checkbox (that conflates two ideas). Instead a case can hold **multiple intents**, each its own `(intent, domain_position)` row:

```
Intents:
  [+] add intent
  - intent 1   domain: (o) in  ( ) margin ( ) ood
  - intent 2   domain: ( ) in  ( ) margin (o) ood
```

A single-intent case is just the common case of one row. Generate → edit → save.

---

## Run Viewer

Shows:

* trace
* tool calls
* scores
* failures

---

## Comparison View

Before/after:

```
Agent v1
Agent v2

+ Intent F1
- Latency
+ Robustness

```

---

## Cost Tracker

Tracks:

* tokens
* LLM judge calls
* expensive evaluations

---

## Destructive actions

The app is almost add-only. `DELETE` exists but is deliberately uncomfortable: a flashy red button behind a bad-tempered confirmation modal. This is not a compliance-grade append-only system, but close.

---

# LLM calls inventory

I would count them explicitly:

| CallPurpose        |                         |
| ------------------ | ----------------------- |
| Agent analyzer     | infer capabilities      |
| Spec generator     | create AGENT_SPEC       |
| Spec auditor       | validate implementation |
| Scenario generator | create eval cases       |
| LLM judge          | subjective scoring      |
| Failure classifier | categorize failures     |

---

The main application is:

* I have a blob of code called `agent.py`.
* I need it to work really well, because it is almost always in the hot part of the loop.
* So let’s inspect it carefully.
* The main way to do this is to add tests and track them over time and across commits.
