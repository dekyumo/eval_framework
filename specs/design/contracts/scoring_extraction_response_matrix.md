# Contract: Scoring, Extraction, and the Response Matrix

`services/scoring.py` + `analysis/metrics.py` + `analysis/response_matrix.py` + `extraction/extractor.py`. Scoring is easy; the only hard part is **extraction** (trace → typed value). The response matrix is "a design matrix + a log-linear model" (the implementer's own insight) — literally a Rasch/1PL IRT model via logistic regression.

## 1. Scoring an eval run

```python
def score_run(run: EvalRun, case: EvalCase) -> ScoredEvalRun:
    results = []
    for metric in case.metrics:
        results += evaluate(run.trace, case, metric)   # dispatch on metric.strategy
    return ScoredEvalRun(run_id=run.id, results=results)
```

`evaluate` dispatches:
- `deterministic` → `DeterministicEvaluator`: `value = extractor(trace)`; `result = compare(value, metric.ground_truth, metric.comparator)`.
- `verifier` → `VerifierEvaluator`: run `verifier_ref(input, output)`; map to a typed `Result`.
- `rubric` → `RubricEvaluator`: LLM judge (or human) applies the rubric → one `Result` per item.

**No LLM call computes a number directly.** The judge returns a typed `Result` (e.g. `bool` per rubric item) with a `confidence`; everything numeric afterwards is deterministic folding.

## 2. Comparators (deterministic metric)

| comparator | applies to | semantics |
| --- | --- | --- |
| `eq` | bool/int/enum | exact equality → bool Result |
| `abs_tol:<x>` | int/float | `abs(value - gt) <= x` → bool Result |
| `rel_tol:<x>` | float | relative tolerance → bool Result |
| `in_set` | enum | membership → bool Result |
| `identity` | any | store the extracted value as the Result (for regression metrics) |

## 3. Extraction (the hard part — AGENT4 authors it)

An extractor is a pure function `extract(trace: Trace) -> bool | int | float | str`, stored as inspectable, fingerprinted source (`Extractor` model). It walks `trace.parts` / `trace.structured_output` to pull the thing being measured (the final number, the detected intent, whether a tool was called).

`extraction/extractor.py`:

```python
def load_extractor(ref: str) -> Callable[[Trace], Any]: ...   # import, verify fingerprint, sandbox-lite
def run_extractor(ref: str, trace: Trace) -> Any: ...          # deterministic, no I/O
```

Authoring loop (AGENT4, `agent_spec/AGENT4_extractor_author.md`): given example traces + target type + NL description → draft `extract` → **run it against the example traces and show outputs** → human confirms or edits → store fingerprinted. Draft-run-confirm, never autonomous (SOUL12). The stored function then runs deterministically forever.

Failure handling: if `extract` raises on a trace, the metric yields a `Result` of the right type with a sentinel + `confidence="low"` and the exception in `rationale` — extraction failure is itself a (bad) observation, not a crash of the scorer.

## 4. Folding across repetitions and datasets (type-driven)

Repetitions (N traces per (snapshot, case)) and dataset-level aggregation use the **fold registry** (see `object_model.md` §2). Fold by `Result.type`:
- bool → proportion true + counts
- enum → value counts + mode
- int → counts + mean/stdev
- float → mean/stdev/min/max
- extensible: `register_fold(name_or_type, fn)`.

For dataset-level classification/regression metrics, build arrays from extracted values + ground truths and call scikit-learn directly:
- classification (bool/enum): `accuracy`, `precision_recall_fscore_support`, `confusion_matrix`.
- regression (int/float with `identity`): `r2_score`, `mean_absolute_percentage_error`, stdev.

## 5. Human–LLM agreement (`analysis/agreement.py`, SOUL11/12)

When both `source="human"` and `source="llm_judge"` Results exist for the same rubric item across cases:
- bool/enum → `confusion_matrix` + `cohen_kappa_score`.
- int/float → Pearson/Spearman correlation.

Low agreement on an item ⇒ flag the **rubric item** as suspect (broken/ambiguous), not the rater (SOUL11). Agreement also gates the human-attention triage (SOUL12): high agreement ⇒ the LLM judge may stand in.

## 6. Response matrix and difficulty (SOUL9 — design matrix + logistic regression)

`analysis/response_matrix.py`. Given a campaign's runs (model × case × repetition), build the matrix and fit a 1PL/Rasch model as a logistic regression.

```python
def build_response_matrix(campaign_id: str) -> ResponseMatrix:
    runs = get_runs(campaign_id)
    # outcome per (model, case): fold repetitions of the case's primary bool/correctness metric -> p in [0,1]
    cell = {(m, c): proportion_correct(runs_for(m, c)) for m in models for c in cases}
    return ResponseMatrix(campaign_id, models, cases, cell)

def fit_irt(rm: ResponseMatrix) -> tuple[dict, dict]:
    # long form: one row per (model, case[, rep]) with binary outcome y
    # design matrix X = one-hot(model dummies) | one-hot(case dummies)   (drop one ref per block)
    X, y = design_matrix(rm)                      # numpy / scipy.sparse
    clf = LogisticRegression(penalty=None, fit_intercept=True, max_iter=1000)
    clf.fit(X, y)
    ability = coefficients_for_model_block(clf)   # model coefficients
    difficulty = -coefficients_for_case_block(clf) # NEGATED case coefficients = difficulty
    return ability, difficulty
```

Notes:
- 1PL/Rasch is the default (robust, few parameters). A 2PL/discrimination term (model×case interaction) is optional and only if data is plentiful.
- `difficulty` partitions cases into easy/medium/hard (bin the coefficients); compare against each case's a-priori `difficulty_prior` (domain × problem) — agreement validates the prior, disagreement is interesting.
- Degenerate columns (a case all models pass or all fail) carry no difficulty information; report them separately, don't let them break the fit (they cause separation — handle with a tiny ridge if `penalty=None` fails to converge).

## 7. Co-failure clustering and thinning (SOUL2 from the behavioural side)

```python
def cofailure_clusters(rm: ResponseMatrix, k=None) -> dict[str, int]:
    M = matrix(rm)                                # models x cases, values in [0,1]
    C = corr(columns(M))                          # case-by-case correlation of outcomes
    # cluster cases by correlation (hierarchical, or KMeans on PCA of columns)
    return labels

def redundant_pairs(rm, threshold=0.97) -> list[tuple[str, str]]:
    # column pairs whose outcome correlation exceeds threshold -> candidates to thin
    ...
```

Clusters are *behavioural* sub-skills (what skill a case exercises), complementary to SOUL2's *content* clusters (what a case is about, via embeddings in `analysis/clustering.py`). `redundant_pairs` feeds suite thinning: keep one of each near-duplicate.

## 8. Model capacity / routing

Per-model row of the matrix → which problem-types / clusters each model clears → input to model switching (which family/size is sufficient for which problem).

## Tests

- `score_run`: deterministic metric with `eq` and `abs_tol`; verifier; rubric (mock judge returns fixed Results).
- folds: each type folds to the documented stats; custom registered fold works.
- extractor: load + fingerprint verify; raises-on-trace → low-confidence sentinel Result, scorer survives.
- agreement: known human/LLM Result pairs → expected kappa and correlation.
- response matrix: a tiny synthetic campaign where strong models pass hard items and weak ones fail → recovered `difficulty` orders the items correctly; degenerate column handled without crashing.
- cofailure: two cases constructed to co-move land in the same cluster; a redundant pair is detected.
