# Object model

Authoritative domain model. All types are Pydantic v2 models in `src/eval_workbench/domain/`. They contain **no I/O**; persistence lives in `storage/`. Field names below are normative; types are Python.

Design rule from the souls: **the trace is the unit** (SOUL3), **a crash is a scorable trace** (carries an exception), **results are free-form typed values folded by type** (not a forced 0–100), **prompts/mocks/extractors are fingerprinted artifacts** (SOUL4/10/11).

## 1. Trace and message parts (SOUL3)

```python
Role = Literal["system", "user", "assistant", "tool"]
PartKind = Literal["text", "tool_call", "tool_response", "media"]

class MessagePart(BaseModel):
    role: Role
    kind: PartKind
    text: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None          # for tool_call
    tool_response: Any | None = None        # for tool_response
    media_uri: str | None = None            # for media (stored out of band)
    ts: float | None = None                 # optional wall-clock

class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0

class Trace(BaseModel):
    id: str
    parts: list[MessagePart]                # the full conversation incl. tool calls/responses
    structured_output: Any | None = None    # final structured result if the agent produced one
    exception: str | None = None            # set iff the agent crashed; a crash IS a scorable trace
    latency_ms: float | None = None
    tokens: TokenUsage | None = None
    # provenance (foreign keys)
    snapshot_id: str
    case_id: str
    model_id: str                            # the model actually used (campaign may override)
    repetition_index: int = 0
    fault_config_id: str | None = None
```

## 2. Result and folding (SOUL3, free-form per the decided model)

A `Result` is a single typed observation produced by one metric/rubric-item/verifier/human. Results are **aggregated by type via a folding function**; there is no universal 0–100 score.

```python
ResultType = Literal["bool", "int", "float", "enum"]
ResultSource = Literal["deterministic", "verifier", "llm_judge", "human"]
Confidence = Literal["low", "medium", "high"]

class Result(BaseModel):
    name: str                                # which metric / rubric item
    type: ResultType
    value: bool | int | float | str          # str only when type == "enum"
    enum_values: list[str] | None = None     # required when type == "enum"
    confidence: Confidence | None = None      # judges/humans set this; deterministic may omit
    rationale: str | None = None
    source: ResultSource

class AggregateResult(BaseModel):
    name: str
    type: ResultType
    n: int
    stats: dict                              # shape depends on type (see folds)
```

**Folding registry** (`analysis/metrics.py`). A fold maps `list[Result]` (same name/type) → `AggregateResult.stats`. Default folds:

| type  | fold output (`stats`) |
| ----- | --------------------- |
| bool  | `{"proportion_true": float, "n_true": int, "n_false": int}` |
| enum  | `{"counts": {value: int}, "mode": value}` |
| int   | `{"counts": {value: int}, "mean": float, "stdev": float}` |
| float | `{"mean": float, "stdev": float, "min": float, "max": float}` |

The registry is extensible: `register_fold(type_or_name, fn)`. "Anything with a folding function is fair game" — a custom result name may register its own fold.

## 3. Metrics / evaluators (functional spec §2.3, three strategies)

A `MetricDef` is attached to a case and names how the truth is established.

```python
MetricStrategy = Literal["deterministic", "verifier", "rubric"]

class MetricDef(BaseModel):
    id: str
    name: str
    strategy: MetricStrategy
    result_type: ResultType
    enum_values: list[str] | None = None
    # deterministic: extractor + ground truth
    extractor_ref: str | None = None         # -> Extractor.id
    ground_truth: Any | None = None
    comparator: str | None = None            # "eq", "abs_tol:0.01", "in_set", ...
    # verifier: external function/program
    verifier_ref: str | None = None
    # rubric
    rubric_ref: str | None = None            # -> Rubric.id
```

Evaluators (in `analysis`/`services/scoring.py`) all implement `evaluate(trace, case, metric) -> list[Result]`:
- `DeterministicEvaluator`: `value = extractor(trace)`; compare to `ground_truth` via `comparator`.
- `VerifierEvaluator`: run external `verifier_ref(input, output)`.
- `RubricEvaluator`: LLM judge or human applies the rubric → one `Result` per item.

## 4. Extractor (SOUL3 + AGENT4)

```python
class Extractor(BaseModel):
    id: str
    name: str
    return_type: ResultType
    source_path: str                         # inspectable .py, authored/edited by a human (AGENT4 drafts)
    fingerprint: str                         # sha256 of normalized source
```

Runtime contract: `extractor(trace: Trace) -> bool | int | float | str`. Pure, no I/O, deterministic. Loaded and executed by `extraction/extractor.py` in-process (it does not run agent code).

## 5. Rubric (SOUL11)

```python
class RubricItem(BaseModel):
    name: str
    type: ResultType
    enum_values: list[str] | None = None
    prompt: str                              # objective, anchored ("did the reply cite the refund window?")

class Rubric(BaseModel):
    id: str
    name: str
    items: list[RubricItem]
    default_judge_prompt: str
    consumes_two_traces: bool = False        # pairwise rubric
    version: int
    fingerprint: str
    frozen: bool = False                     # True once any trace has been scored against it
```

Frozen rubric is immutable; changing items or prompt = create a new rubric. Default shipped rubrics: `quality`, `tone`, `safety`, `robustness` (items: detect/contain/recover/honesty — SOUL10).

## 6. Eval case and dataset (functional spec §6, addendum §3-4)

```python
DomainPosition = Literal["in", "margin", "ood"]
ProblemType = Literal["happy", "technical", "adversarial", "client"]
Split = Literal["optimisation", "judging"]
CaseSource = Literal["manual", "generated", "copied", "incident"]

class Intent(BaseModel):
    intent: str
    domain_position: DomainPosition

class EvalCase(BaseModel):
    id: str
    conversation: list[MessagePart]          # multi-turn input (agentic, not single prompt)
    intents: list[Intent]                    # one row per intent (multi-intent supported)
    problem_type: ProblemType
    tags: list[str] = []
    metrics: list[MetricDef] = []
    fault_config: "FaultConfig | None" = None
    split: Split = "judging"                 # SOUL13; default held-out
    difficulty_prior: Literal["easy", "medium", "hard"] | None = None  # derived from intents x problem
    source: CaseSource = "manual"

class EvalDataset(BaseModel):
    id: str
    name: str
    case_ids: list[str]
    # service methods: add_case, copy_case (duplicate-and-edit), filter(tags)
```

`difficulty_prior` is derived a priori: more `ood`/`adversarial` ⇒ harder (SOUL9). It is the prior the campaign later calibrates.

## 7. Agent snapshot, manifest, graph (functional spec §2.2, §3)

```python
class PromptNode(BaseModel):
    id: str
    fingerprint: str                         # of the RAW ADK instruction template, pre-.format
    text: str

class ToolNode(BaseModel):
    id: str
    name: str
    signature: str
    source_fingerprint: str
    reaches_external: bool                   # declared external access (functional spec §11.2)

class ModelNode(BaseModel):
    id: str                                  # fully qualified, pinned (reject "latest")
    provider: str

class AgentNode(BaseModel):
    name: str
    model_id: str
    prompt_id: str
    tool_ids: list[str] = []
    skill_ids: list[str] = []
    hook_ids: list[str] = []
    subagent_names: list[str] = []

class AgentManifest(BaseModel):
    agents: list[AgentNode]
    tools: list[ToolNode]
    models: list[ModelNode]
    prompts: list[PromptNode]
    root_agent_name: str

class AgentSnapshot(BaseModel):
    id: str                                  # = commit_hash (identity is the clean commit)
    repo_path: str
    commit_hash: str
    branch: str
    timestamp: float
    manifest: AgentManifest
    sampling_params: dict                    # temperature, top_p... (part of the agent, not the run)
    dependency_lock: str                     # contents/hash of the lockfile at the commit
    framework_commit: str | None = None
```

Graph edges (stored, see Kuzu schema): `DELEGATES_TO`, `USES_TOOL`, `USES_MODEL`, `CONTAINS_PROMPT`, and commit `ON_TOP_OF` parent.

## 8. Runs (functional spec §2.4, §10.3-10.4)

```python
class EvalRun(BaseModel):
    id: str
    snapshot_id: str
    case_id: str
    model_id: str                            # may differ from snapshot default in a campaign
    repetition_index: int
    trace: Trace
    campaign_id: str | None = None

class ScoredEvalRun(BaseModel):
    id: str
    run_id: str
    results: list[Result]
    aggregates: list[AggregateResult] = []   # when folded across repetitions
```

## 9. Eval campaign and response matrix (SOUL9 — the IRT driver)

```python
class EvalCampaign(BaseModel):
    id: str
    name: str
    dataset_id: str
    base_snapshot_id: str                    # FIXED agent code/prompt; only the model varies
    model_panel: list[str]                   # e.g. gemini-2.x-flash-lite ... claude-haiku ... gpt-...-mini
    repetitions: int = 1
    created_at: float
# A campaign produces EvalRun rows for the cross product (model in panel) x (case in dataset) x repetition.
```

`ResponseMatrix` is a derived analysis object, not stored raw (recomputed from runs):

```python
class ResponseMatrix(BaseModel):
    campaign_id: str
    models: list[str]                        # rows
    case_ids: list[str]                      # columns
    cell: dict[tuple[str, str], float]       # (model, case) -> aggregated outcome in [0,1] or mean
    # derivations (see contracts/scoring_extraction_response_matrix.md):
    #   difficulty[case]  via logistic regression item coefficients (Rasch/1PL)
    #   ability[model]    via the same regression's model coefficients
    #   clusters[case]    co-failure clustering of columns (sub-skills)
    #   redundant_pairs   near-duplicate columns -> suite thinning
```

## 10. Tags, human eval, faults

```python
class Tag(BaseModel):
    name: str
    color: str
    description: str = ""
# TagRegistry: closed set; create / rename / delete_if_unused (count == 0).

class HumanEval(BaseModel):
    id: str
    run_id: str
    rubric_id: str
    results: list[Result]                    # same structure as automated; source="human"
    comments: str = ""
# Agreement (analysis/agreement.py): per rubric item, by type:
#   bool/enum -> confusion matrix + Cohen's kappa ; int/float -> correlation.

FaultBoundary = Literal["user_input","tool_call","tool_result","model_transport","model_output","state","inter_agent"]
FaultClass = Literal["crash","omission","timing","value","byzantine"]
FaultTrigger = Literal["first_call","nth_call","always"]

class FaultConfig(BaseModel):                 # FARM: the F (see SOUL10 + fault_injector contract)
    id: str
    boundary: FaultBoundary
    fault_class: FaultClass
    target: str                              # tool name, or "model"
    trigger: FaultTrigger = "always"
    n: int | None = None                     # for nth_call
    persistent: bool = True                  # transient (recover by retry) vs persistent (escalate)
    payload: Any | None = None               # garbage value / http code / malformed body
    seed: int = 0                            # deterministic
    mocked_tools_ref: str                    # path to mocked_tools.py
    mocked_tools_fingerprint: str
```

## 11. Kuzu schema (one DB per agent-under-test)

Node tables (Kuzu DDL sketch; PK in parentheses):

```text
Commit(hash)            : hash STRING, branch STRING, ts INT64
Snapshot(id)            : id STRING, commit_hash STRING, sampling_params STRING(json), dependency_lock STRING, manifest STRING(json)
AgentNode(key)          : key STRING, snapshot_id STRING, name STRING, model_id STRING, prompt_id STRING
ToolNode(id)            : id STRING, name STRING, signature STRING, source_fingerprint STRING, reaches_external BOOL
ModelNode(id)           : id STRING, provider STRING
PromptNode(id)          : id STRING, fingerprint STRING, text STRING
EvalCase(id)            : id STRING, conversation STRING(json), intents STRING(json), problem_type STRING, split STRING, difficulty_prior STRING, source STRING
Rubric(id)              : id STRING, name STRING, items STRING(json), version INT64, fingerprint STRING, frozen BOOL
Extractor(id)           : id STRING, name STRING, return_type STRING, source_path STRING, fingerprint STRING
EvalRun(id)             : id STRING, snapshot_id STRING, case_id STRING, model_id STRING, repetition_index INT64, trace STRING(json), campaign_id STRING
ScoredEvalRun(id)       : id STRING, run_id STRING, results STRING(json), aggregates STRING(json)
EvalCampaign(id)        : id STRING, name STRING, dataset_id STRING, base_snapshot_id STRING, model_panel STRING(json), repetitions INT64
EvalDataset(id)         : id STRING, name STRING, case_ids STRING(json)
Tag(name)               : name STRING, color STRING, description STRING
HumanEval(id)           : id STRING, run_id STRING, rubric_id STRING, results STRING(json), comments STRING
FaultConfig(id)         : id STRING, ... (mirror the model)
```

Rel tables:

```text
ON_TOP_OF      (Commit -> Commit)          # child on top of parent
SNAPSHOT_OF    (Snapshot -> Commit)
HAS_AGENT      (Snapshot -> AgentNode)
DELEGATES_TO   (AgentNode -> AgentNode)
USES_TOOL      (AgentNode -> ToolNode)
USES_MODEL     (AgentNode -> ModelNode)
CONTAINS_PROMPT(AgentNode -> PromptNode)
RUN_OF_CASE    (EvalRun -> EvalCase)
RUN_OF_SNAPSHOT(EvalRun -> Snapshot)
IN_CAMPAIGN    (EvalRun -> EvalCampaign)
SCORED_FROM    (ScoredEvalRun -> EvalRun)
TAGGED         (EvalCase -> Tag)
```

JSON-in-column is acceptable for leaf payloads (traces, manifests, results); use real edges for anything queried as a graph (lineage, topology). `storage/repositories.py` owns (de)serialization between these rows and the Pydantic models above.

Next: the fragile-component contracts in `contracts/`.
