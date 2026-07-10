# Skill: Eval Data Analysis

Use this skill when analysing CSV output from the `eval_framework` CLI tool.

---

## 1. Data Model

The CSV has **one row per (case, metric)**. A single eval run for N cases and M metrics produces N×M rows.

Key columns:

| column | notes |
|---|---|
| `case_id` / `case_name` | identifies the test case |
| `metric_name` | the rubric item being scored |
| `result_type` | `bool`, `int`, `float`, or `enum` |
| `result_value` | the raw scored value (always stored as a string — cast before computing) |
| `result_source` | `llm_judge`, `deterministic`, `human`, or `verifier` |
| `skipped` | `True`/`False` — exclude skipped rows from aggregations |
| `commit` | git ref; use to group multi-commit comparisons |

Always drop skipped rows first:

```python
import pandas as pd

df = pd.read_csv("results.csv")
df = df[df["skipped"] == False].copy()
```

---

## 2. Aggregate with pandas

Cast `result_value` based on `result_type` before any arithmetic. For `bool`, cast to int (0/1).

```python
def cast_value(row):
    if row["result_type"] == "bool":
        return int(row["result_value"].strip().lower() == "true")
    if row["result_type"] in ("int", "float"):
        return float(row["result_value"])
    return row["result_value"]  # enum: keep as string

df["value"] = df.apply(cast_value, axis=1)

# Per-metric summary (numeric metrics only)
numeric = df[df["result_type"].isin(["bool", "int", "float"])]
summary = (
    numeric.groupby("metric_name")["value"]
    .agg(mean="mean", std="std", n="count")
    .round(3)
)
print(summary)
```

---

## 3. Bool metrics: convention and pass rates

**Convention**: `result_value=True` means "criterion met / agent passed this check". Higher pass rate is always better. This is consistent with the sklearn convention (positive label = the desired outcome).

The CSV has no ground-truth column for rubric items. The judge verdict *is* the label — there is no separate prediction to compare it against. Do not fabricate a `y_true = [1] * n` vector; that produces trivially misleading precision/recall values.

The natural metric for bool rubric items is the **pass rate**:

```python
bool_df = df[df["result_type"] == "bool"].copy()
bool_df["passed"] = bool_df["result_value"].str.strip().str.lower() == "true"

pass_rate = (
    bool_df.groupby("metric_name")["passed"]
    .agg(pass_rate="mean", n="count")
    .round(3)
)
print(pass_rate)
```

sklearn classification metrics (`precision_score`, `recall_score`, `f1_score`) are meaningful here only when you have a ground-truth label to compare against — i.e. when comparing `llm_judge` verdicts to `human` verdicts for the same case (see section 9), or when running deterministic extractors with known ground truth.

For numeric metrics (`int` / `float`) with ground truth from a deterministic extractor, use regression metrics. Ground truth comes from the case definition and is captured by the framework during scoring; if you need it in the CSV, re-run with a deterministic extractor that emits both predicted and ground-truth values:

```python
from sklearn.metrics import r2_score, mean_absolute_percentage_error

# Requires a separate ground-truth column (not present in the default CSV).
# Use when you have merged in expected values from your case definitions.
# r2 = r2_score(y_true, y_pred)
# mape = mean_absolute_percentage_error(y_true, y_pred)
```

---

## 4. Compare two commits

Load one CSV per commit, merge on `case_id` + `metric_name`, compute delta.

```python
a = pd.read_csv("results_commit_a.csv")
b = pd.read_csv("results_commit_b.csv")

for frame, label in [(a, "a"), (b, "b")]:
    frame = frame[frame["skipped"] == False].copy()
    frame["value"] = frame.apply(cast_value, axis=1)
    frame.rename(columns={"value": f"value_{label}", "commit": f"commit_{label}"}, inplace=True)
    if label == "a":
        merged = frame[["case_id", "case_name", "metric_name", f"value_{label}"]]
    else:
        merged = merged.merge(
            frame[["case_id", "metric_name", f"value_{label}"]],
            on=["case_id", "metric_name"], how="outer"
        )

merged["delta"] = merged["value_b"] - merged["value_a"]

# Cases that regressed
regressions = merged[merged["delta"] < 0].sort_values("delta")
print(regressions[["case_name", "metric_name", "value_a", "value_b", "delta"]])
```

Do not declare a commit better from aggregate means alone. Inspect the regressions individually (see section 5).

---

## 5. Drill into individual traces via MCP

Aggregate numbers obscure failure modes. Always inspect the traces for cases that failed or regressed.

If the tool is exposed as an MCP server, use `get_run` with the `run_id` from the CSV:

```python
# Pseudo-code — adapt to your MCP client
run_id = regressions.iloc[0]["run_id"]
trace = mcp_client.call("get_run", {"run_id": run_id})
# Examine: agent steps, tool calls, final answer, judge rationale
```

**Warning**: Never trust an aggregate score drop or improvement without reading at least a handful of traces. Aggregate means can move due to a single flaky case or a judge prompt quirk, not a real capability change.

---

## 6. Probabilistic nature of results

Both the LLM agent and the LLM judge are stochastic. A case that fails once may pass on the next run.

Rules of thumb:
- A single-run failure on one case is weak evidence. Re-run the case at least 2–3 times before treating it as a real regression.
- Judge variance is highest for borderline cases. If `result_source == "llm_judge"` and the score is near a threshold, treat it with extra skepticism.
- For statistical confidence on a metric, run the full dataset multiple times and report mean ± std.
- Deterministic metrics (`result_source == "deterministic"`) are reliable on a single run.

---

## 7. Goodhart's Law and optimisation drift

> "When a measure becomes a target, it ceases to be a good measure."

This is the most common failure mode in iterative agent development.

- **Keep a held-out test set.** Split your cases into a *tuning set* (used while developing the agent) and a *test set* (never looked at during tuning). Once a case is used to guide a prompt or code change, it is "burned" — it can no longer measure generalisation.
- **Watch human-vs-automated agreement.** If your automated eval score rises over several commits but human raters disagree with the verdicts more often, you are Goodharting, not improving.
- **Do not iterate directly on failing cases.** Identify the *pattern* behind failures (e.g. "agent does not handle multi-step tool chains") and fix that pattern. Then check whether your test set improved as a side-effect.
- **Rotate datasets periodically.** If the agent has been trained/prompted against the same dataset for many iterations, retire it and create fresh cases.

---

## 8. Check the agent description before drawing conclusions

Before attributing a score change to a code fix (or regression), retrieve the agent snapshot to confirm what code was actually running:

```python
# Via MCP
snapshot = mcp_client.call("get_snapshot", {"snapshot_id": df["snapshot_id"].iloc[0]})
print(snapshot["description"])  # human-readable summary of the agent code at that commit
```

This guards against:
- Comparing the wrong commits (copy-paste error in `--commit`)
- Cached / stale agent code not reflecting the intended change
- Accidentally testing against the wrong agent path

---

## 9. Alignment with human evals

Automated rubric scores are a proxy. Validate them:

- Filter `result_source == "human"` rows — these are ground-truth labels.
- Compare them against `result_source == "llm_judge"` rows for the same case+metric.
- A judge with <80% agreement with human labels on a held-out set is unreliable; fix the judge prompt before using its scores to make decisions.

```python
human = df[df["result_source"] == "human"][["case_id", "metric_name", "value"]].rename(columns={"value": "human"})
judge = df[df["result_source"] == "llm_judge"][["case_id", "metric_name", "value"]].rename(columns={"value": "judge"})

alignment = human.merge(judge, on=["case_id", "metric_name"])
alignment["agree"] = alignment["human"] == alignment["judge"]
print(f"Judge-human agreement: {alignment['agree'].mean():.1%} over {len(alignment)} cases")
```

Low agreement on specific metrics points to ambiguous rubric wording or a judge prompt that needs tightening — not necessarily a bad agent.
